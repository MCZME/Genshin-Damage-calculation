from typing import Any, Dict, List, Optional, Tuple

from core.systems.contract.damage import Damage, DamageType
from core.systems.contract.reaction import (
    ElementalReactionType, 
    ReactionCategory, 
    ReactionResult
)
from core.context import EventEngine
from core.event import DamageEvent, EventType, GameEvent
from core.logger import get_emulation_logger
from core.mechanics.aura import Element
from core.systems.base_system import GameSystem
from core.tool import get_current_time, get_reaction_multiplier


class ReactionSystem(GameSystem):
    """
    元素反应逻辑分发系统。
    
    负责将 AuraManager 产出的原始反应结果 (ReactionResult) 转化为实际的游戏效果，
    包括生成剧变反应伤害、应用减抗效果等。
    """

    def __init__(self) -> None:
        super().__init__()
        # 剧变反应受击 ICD 配置: (时间窗口帧数, 最大受击次数)
        # 0.5s 内最多受 2 次同类反应伤害
        self._REACTION_ICD_WINDOW = 30 
        self._REACTION_MAX_HITS = 2

        # 运行时状态记录: 
        # Key: (目标实体ID, 反应类型) -> [最后重置帧, 当前窗口内受击次数]
        self._target_reaction_records: Dict[Tuple[int, ElementalReactionType], List[int]] = {}

    def register_events(self, engine: EventEngine) -> None:
        """订阅伤害前置事件以截获反应。"""
        engine.subscribe(EventType.BEFORE_DAMAGE, self)
        engine.subscribe(EventType.ELECTRO_CHARGED_TICK, self)
        engine.subscribe(EventType.BURNING_TICK, self)

    def handle_event(self, event: GameEvent) -> None:
        """事件分发。"""
        if event.event_type == EventType.BEFORE_DAMAGE:
            self._process_damage_reactions(event)
        elif event.event_type == EventType.ELECTRO_CHARGED_TICK:
            self._handle_ec_tick(event)
        elif event.event_type == EventType.BURNING_TICK:
            self._handle_burning_tick(event)

    def _handle_ec_tick(self, event: GameEvent) -> None:
        """处理感电周期性跳电伤害。"""
        target = event.data.get("target")
        # 产生感电剧变伤害 (倍率 1.2)
        self._generate_transformative_damage(
            source_char=target, # Tick 伤害源简化处理为目标自身
            target=target,
            r_type=ElementalReactionType.ELECTRO_CHARGED,
            multiplier=1.2,
            element=Element.ELECTRO
        )

    def _handle_burning_tick(self, event: GameEvent) -> None:
        """处理燃烧周期性范围伤害。"""
        target = event.data.get("target")
        source_char = event.source # 燃烧的源通常是最初挂火/草的角色
        
        # 产生燃烧剧变伤害 (倍率 0.25)
        # 燃烧是 AOE 伤害，我们手动调用一次广播
        from core.systems.contract.attack import AttackConfig, HitboxConfig, AOEShape
        
        react_dmg = Damage(
            damage_multiplier=0,
            element=(Element.PYRO, 0.0),
            damage_type=DamageType.REACTION,
            name="燃烧伤害"
        )
        react_dmg.config = AttackConfig(
            hitbox=HitboxConfig(shape=AOEShape.SPHERE, radius=1.0) # 1米范围 AOE
        )
        
        # 注入计算参数 (等级系数, 反应系数)
        level_mult = get_reaction_multiplier(target.level) # 燃烧通常随环境或目标等级缩放？简化为 0.25
        react_dmg.add_data("等级系数", level_mult)
        react_dmg.add_data("反应系数", 0.25)
        
        # 发布广播
        self.context.space.broadcast_damage(target, react_dmg)

    def _generate_transformative_damage(
        self, 
        source_char: Any, 
        target: Any, 
        r_type: ElementalReactionType, 
        multiplier: float, 
        element: Element
    ) -> None:
        """内部辅助：产生标准的剧变伤害事件。"""
        level_mult = get_reaction_multiplier(source_char.level)
        
        react_dmg = Damage(
            damage_multiplier=0,
            element=(element, 0.0),
            damage_type=DamageType.REACTION,
            name=r_type.value
        )
        react_dmg.add_data("等级系数", level_mult)
        react_dmg.add_data("反应系数", multiplier)
        
        self.engine.publish(DamageEvent(
            event_type=EventType.BEFORE_DAMAGE,
            frame=get_current_time(),
            source=source_char,
            target=target,
            damage=react_dmg
        ))

    def _check_damage_icd(self, target: Any, r_type: ElementalReactionType) -> bool:
        """检查目标是否还能承受该类型的剧变伤害。"""
        current_f = get_current_time()
        key = (id(target), r_type)
        
        if key not in self._target_reaction_records:
            self._target_reaction_records[key] = [current_f, 1]
            return True
            
        record = self._target_reaction_records[key] # [reset_f, count]
        
        # 1. 窗口重置判定
        if current_f - record[0] >= self._REACTION_ICD_WINDOW:
            record[0] = current_f
            record[1] = 1
            return True
            
        # 2. 次数限制判定
        if record[1] < self._REACTION_MAX_HITS:
            record[1] += 1
            return True
            
        return False

    def _process_damage_reactions(self, event: GameEvent) -> None:
        """解析伤害对象中携带的反应结果。"""
        dmg: Damage = event.data.get("damage")
        if not dmg:
            return

        # 卫语句：防止剧变反应伤害再次触发剧变反应，导致无限递归
        if dmg.damage_type == DamageType.REACTION:
            return

        results: List[ReactionResult] = getattr(dmg, "reaction_results", [])
        for res in results:
            self._apply_reaction_effect(event, res)

    def _apply_reaction_effect(self, event: GameEvent, res: ReactionResult) -> None:
        """根据反应类别分发逻辑。"""
        source_char = event.data.get("character")
        target = event.data.get("target")

        # 记录反应日志
        get_emulation_logger().log_reaction(
            source_char=source_char,
            reaction_type=res.reaction_type.value,
            target=target
        )

        if res.reaction_type == ElementalReactionType.CRYSTALLIZE:
            self._handle_crystallize(event, res)
        elif res.category == ReactionCategory.TRANSFORMATIVE:
            self._handle_transformative(event, res)
        elif res.category == ReactionCategory.STATUS:
            self._handle_status_change(event, res)

    def _handle_transformative(self, event: GameEvent, res: ReactionResult) -> None:
        """处理剧变类反应 (产生额外的剧变伤害)。"""
        source_char = event.data.get("character")
        target = event.data.get("target")
        
        # 卫语句：检查剧变伤害 ICD (同一目标 0.5s 内最多受 2 次同类伤害)
        if not self._check_damage_icd(target, res.reaction_type):
            get_emulation_logger().log_debug(
                f"目标 {target.name} 对 {res.reaction_type.value} 处于受击 ICD 中，跳过伤害", 
                sender="Reaction"
            )
            return

        level_mult = get_reaction_multiplier(source_char.level)
        
        reaction_multipliers = {
            ElementalReactionType.OVERLOAD: 2.75,
            ElementalReactionType.ELECTRO_CHARGED: 1.2,
            ElementalReactionType.SUPERCONDUCT: 0.5,
            ElementalReactionType.SWIRL: 0.6,
            ElementalReactionType.SHATTER: 1.5,
            ElementalReactionType.BLOOM: 2.0,
            ElementalReactionType.BURGEON: 3.0,
            ElementalReactionType.HYPERBLOOM: 3.0,
        }
        base_mult = reaction_multipliers.get(res.reaction_type, 1.0)
        
        # 1. 产生基础剧变伤害 (绽放本身不直接对怪造成伤害，仅生成核心)
        if res.reaction_type != ElementalReactionType.BLOOM:
            react_dmg = Damage(
                damage_multiplier=0, 
                element=(res.source_element, 0.0), 
                damage_type=DamageType.REACTION,
                name=res.reaction_type.value
            )
            react_dmg.add_data("等级系数", level_mult)
            react_dmg.add_data("反应系数", base_mult)
            
            self.engine.publish(DamageEvent(
                event_type=EventType.BEFORE_DAMAGE,
                frame=get_current_time(),
                source=source_char,
                target=target,
                damage=react_dmg
            ))
        else:
            # 绽放特有逻辑：生成草原核
            self._spawn_dendro_core(event, res)

        # 2. 扩散特有逻辑：元素传播
        if res.reaction_type == ElementalReactionType.SWIRL:
            self._handle_swirl_propagation(event, res)

        # 3. 超导特有逻辑：减物理抗性 (40%, 12秒)
        if res.reaction_type == ElementalReactionType.SUPERCONDUCT:
            from core.effect.common import ResistanceDebuffEffect
            # 作用于受击目标
            debuff = ResistanceDebuffEffect(
                owner=target,
                name="超导减抗",
                elements=["物理"],
                amount=40.0,
                duration=12 * 60
            )
            debuff.apply()

    def _spawn_dendro_core(self, event: GameEvent, res: ReactionResult) -> None:
        """产生草原核实体。"""
        from core.entities.elemental_entities import DendroCoreEntity
        from core.entities.base_entity import Faction
        
        target = event.data.get("target")
        source_char = event.data.get("character")
        
        # 1. 数量控制：最多存在 5 个
        cores = [e for e in self.context.space.get_all_entities() if isinstance(e, DendroCoreEntity)]
        if len(cores) >= 5:
            # 找到最早产生的核心并令其爆炸
            oldest_core = sorted(cores, key=lambda x: x.current_frame, reverse=True)[0]
            oldest_core.finish()
            
        # 2. 生成新核心
        core = DendroCoreEntity(source_char, target.pos)
        self.context.space.register(core)

    def _handle_crystallize(self, event: GameEvent, res: ReactionResult) -> None:
        """处理结晶反应：产生结晶晶片实体。"""
        from core.entities.elemental_entities import CrystalShardEntity
        
        source_char = event.data.get("character")
        target_entity = event.data.get("target")
        
        # 结晶盾基础值
        base_hp = get_reaction_multiplier(source_char.level) * 0.5 
        
        # 产生晶片实体，位置在怪物处
        shard = CrystalShardEntity(
            creator=source_char,
            element=res.target_element,
            pos=target_entity.pos,
            base_shield_hp=base_hp
        )
        
        self.context.space.register(shard)

    def _handle_swirl_propagation(self, event: GameEvent, res: ReactionResult) -> None:
        """处理扩散传播：对周围敌人施加元素并造成伤害。"""
        source_char = event.data.get("character")
        primary_target = event.data.get("target")
        swirled_element = res.target_element # 被扩散掉的元素
        
        # 检索周围 6米内的其他敌人
        nearby_enemies = self.context.space.get_entities_in_range(
            origin=(primary_target.pos[0], primary_target.pos[1]),
            radius=6.0,
            faction=primary_target.faction
        )
        
        for enemy in nearby_enemies:
            if enemy == primary_target:
                continue
                
            # 对周围敌人产生扩散伤害 (附带元素附着)
            spread_dmg = Damage(
                damage_multiplier=0,
                element=(swirled_element, 1.0), # 扩散会传播 1U 元素
                damage_type=DamageType.REACTION,
                name=f"扩散 ({swirled_element.value})"
            )
            # 扩散二次伤害不再次触发扩散，但在新架构下由 AuraManager 自动处理
            
            self.engine.publish(DamageEvent(
                event_type=EventType.BEFORE_DAMAGE,
                frame=get_current_time(),
                source=source_char,
                target=enemy,
                damage=spread_dmg
            ))

    def _handle_status_change(self, event: GameEvent, res: ReactionResult) -> None:
        """处理状态类反应 (如冻结、激化等状态的视觉或逻辑标记)。"""
        # 目前大部分逻辑在 AuraManager 内部处理完成
        pass
