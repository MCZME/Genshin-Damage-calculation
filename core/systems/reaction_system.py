from typing import Any, Dict, List, Tuple

from core.systems.contract.damage import Damage
from core.systems.contract.reaction import (
    ElementalReactionType, 
    ReactionCategory, 
    ReactionResult
)
from core.context import EventEngine
from core.event import EventType, GameEvent
from core.logger import get_emulation_logger
from core.mechanics.aura import Element
from core.systems.base_system import GameSystem
from core.tool import get_current_time, get_reaction_multiplier
from core.action.attack_tag_resolver import AttackCategory


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
        """订阅反应事件。"""
        engine.subscribe(EventType.AFTER_ELEMENTAL_REACTION, self)
        engine.subscribe(EventType.ELECTRO_CHARGED_TICK, self)
        engine.subscribe(EventType.BURNING_TICK, self)

    def handle_event(self, event: GameEvent) -> None:
        """事件分发。"""
        if event.event_type == EventType.AFTER_ELEMENTAL_REACTION:
            res = event.data.get("elemental_reaction")
            if res:
                self._apply_reaction_effect(event, res)
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
        
        from core.systems.contract.attack import AttackConfig, HitboxConfig, AOEShape
        
        react_dmg = Damage(
            damage_multiplier=0,
            element=(Element.PYRO, 0.0),
            config=AttackConfig(
                attack_tag=AttackCategory.REACTION,
                hitbox=HitboxConfig(shape=AOEShape.SPHERE, radius=1.0) # 1米范围 AOE
            ),
            name="燃烧伤害"
        )
        
        level_mult = get_reaction_multiplier(target.level)
        react_dmg.add_data("等级系数", level_mult)
        react_dmg.add_data("反应系数", 0.25)
        
        self.context.space.broadcast_damage(target, react_dmg)

    def _generate_transformative_damage(
        self, 
        source_char: Any, 
        target: Any, 
        r_type: ElementalReactionType, 
        multiplier: float, 
        element: Element
    ) -> None:
        """产生一次性的剧变伤害。"""
        # 检查受击 ICD
        if not self._check_damage_icd(target, r_type):
            return
            
        from core.systems.contract.attack import AttackConfig
        level_mult = get_reaction_multiplier(source_char.level)
        
        dmg = Damage(
            damage_multiplier=0,
            element=(element, 0.0),
            config=AttackConfig(attack_tag=AttackCategory.REACTION),
            name=r_type.value
        )
        dmg.add_data("等级系数", level_mult)
        dmg.add_data("反应系数", multiplier)
        
        self.engine.publish(GameEvent(
            event_type=EventType.BEFORE_DAMAGE,
            frame=get_current_time(),
            source=source_char,
            data={
                "character": source_char,
                "target": target,
                "damage": dmg
            }
        ))

    def _apply_reaction_effect(self, event: GameEvent, res: ReactionResult) -> None:
        """根据反应类别分发逻辑。"""
        source_char = event.source
        target = event.data.get("target")

        get_emulation_logger().log_reaction(
            source_char=source_char,
            reaction_type=res.reaction_type.value,
            target=target
        )

        # 1. 物理化副作用 (生成实体)
        if res.reaction_type == ElementalReactionType.CRYSTALLIZE:
            self._handle_crystallize(event, res)
        elif res.reaction_type == ElementalReactionType.BLOOM:
            self._handle_bloom(event, res)
            
        # 2. 状态/Debuff 副作用
        if res.reaction_type == ElementalReactionType.SUPERCONDUCT:
            self._handle_superconduct(event, res)
        elif res.reaction_type == ElementalReactionType.SWIRL:
            self._handle_swirl(event, res)
        elif res.reaction_type == ElementalReactionType.FREEZE:
            self._handle_freeze(event, res)
            
        # 3. 剧变伤害产生
        if res.category == ReactionCategory.TRANSFORMATIVE:
            self._handle_transformative(event, res)

    def _handle_crystallize(self, event: GameEvent, res: ReactionResult) -> None:
        """处理结晶反应。"""
        from core.entities.elemental_entities import CrystalShardEntity
        target = event.data.get("target")
        source_char = event.source
        
        base_shield = get_reaction_multiplier(source_char.level) * 1.0
        shard = CrystalShardEntity(
            creator=source_char,
            element=res.target_element,
            pos=tuple(target.pos),
            base_shield_hp=base_shield
        )
        self.context.space.register(shard)

    def _handle_bloom(self, event: GameEvent, res: ReactionResult) -> None:
        """处理绽放反应。"""
        from core.entities.elemental_entities import DendroCoreEntity
        target = event.data.get("target")
        source_char = event.source
        core = DendroCoreEntity(creator=source_char, pos=tuple(target.pos))
        self.context.space.register(core)

    def _handle_superconduct(self, event: GameEvent, res: ReactionResult) -> None:
        """处理超导减抗逻辑。"""
        from core.effect.common import ResistanceDebuffEffect
        target = event.data.get("target")
        source_char = event.source
        
        # 降低 40% 物理抗性，持续 12s
        debuff = ResistanceDebuffEffect(
            owner=target,
            name="超导减抗",
            elements=["物理"],
            amount=40.0,
            duration=12 * 60
        )
        # 如果实体具备添加效果的方法，则应用
        if hasattr(target, "active_effects"):
            # 检查是否已存在同名效果，避免重复叠加
            for eff in target.active_effects:
                if eff.name == "超导减抗":
                    eff.duration = 12 * 60 # 刷新时间
                    return
            debuff.apply()

    def _handle_swirl(self, event: GameEvent, res: ReactionResult) -> None:
        """处理扩散反应的空间传播。"""
        target = event.data.get("target")
        source_char = event.source
        
        # 扩散半径通常为 6m
        # 传播除了风以外的反应元素
        element_to_spread = res.target_element
        if element_to_spread != Element.ANEMO:
            self.context.space.broadcast_element(
                source=source_char,
                element=element_to_spread,
                u_value=1.0, 
                origin=(target.pos[0], target.pos[1]), # 仅取 X, Z
                radius=6.0,
                exclude_target=target
            )

    def _handle_freeze(self, event: GameEvent, res: ReactionResult) -> None:
        """处理冻结状态。"""
        # 目前主要由 AuraManager 维护冻结元素量，此处可用于触发特定的 AFTER_FREEZE 事件
        pass

    def _handle_transformative(self, event: GameEvent, res: ReactionResult) -> None:
        """处理剧变类反应伤害产生逻辑。"""
        source_char = event.source
        target = getattr(event, "target", None)

        # 检查受击 ICD
        if not self._check_damage_icd(target, res.reaction_type):
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
        
        # 产生剧变伤害
        if res.reaction_type != ElementalReactionType.BLOOM:
            self._generate_transformative_damage(
                source_char=source_char,
                target=target,
                r_type=res.reaction_type,
                multiplier=base_mult,
                element=res.source_element
            )

    def _check_damage_icd(self, target: Any, r_type: ElementalReactionType) -> bool:
        """检查特定目标对特定剧变伤害的受击 ICD。"""
        key = (id(target), r_type)
        current_frame = get_current_time()
        
        if key not in self._target_reaction_records:
            self._target_reaction_records[key] = [current_frame, 1]
            return True
            
        record = self._target_reaction_records[key]
        last_reset_frame = record[0]
        hit_count = record[1]
        
        if current_frame - last_reset_frame > self._REACTION_ICD_WINDOW:
            record[0] = current_frame
            record[1] = 1
            return True
            
        if hit_count < self._REACTION_MAX_HITS:
            record[1] += 1
            return True
            
        return False
