import random
from typing import Any

from core.systems.contract.attack import AttackConfig
from core.systems.contract.damage import Damage
from core.systems.contract.reaction import (
    ElementalReactionType,
    ReactionCategory,
    ReactionResult,
)
from core.context import EventEngine
from core.event import EventType, GameEvent
from core.logger import get_emulation_logger
from core.mechanics.aura import Element
from core.systems.base_system import GameSystem
from core.tool import get_current_time, get_reaction_multiplier


class ReactionSystem(GameSystem):
    """
    元素反应逻辑分发系统。

    负责将 AuraManager 产出的原始反应结果 (ReactionResult) 转化为实际的游戏效果，
    包括生成剧变反应伤害、应用减抗效果等。
    同时处理月曜反应的触发判定与效果分发。
    """

    def __init__(self) -> None:
        super().__init__()
        # 剧变反应受击 ICD 配置: (时间窗口帧数, 最大受击次数)
        # 0.5s 内最多受 2 次同类反应伤害
        self._REACTION_ICD_WINDOW = 30
        self._REACTION_MAX_HITS = 2

        # 运行时状态记录:
        # Key: (目标实体ID, 反应类型) -> [最后重置帧, 当前窗口内受击次数]
        self._target_reaction_records: dict[
            tuple[int, ElementalReactionType], list[int]
        ] = {}

        # 月曜触发角色配置（由 LunarReactionSystem 统一管理）
        # 此处保留引用，避免循环导入时直接访问
        self._lunar_system: Any = None

    def register_events(self, engine: EventEngine) -> None:
        """订阅反应事件。"""
        engine.subscribe(EventType.AFTER_ELEMENTAL_REACTION, self)
        engine.subscribe(EventType.ELECTRO_CHARGED_TICK, self)
        engine.subscribe(EventType.BURNING_TICK, self)
        # 月曜事件
        engine.subscribe(EventType.LUNAR_CHARGED_TICK, self)
        engine.subscribe(EventType.LUNAR_CRYSTALLIZE_ATTACK, self)

    def handle_event(self, event: GameEvent) -> None:
        """事件分发。"""
        if event.event_type == EventType.AFTER_ELEMENTAL_REACTION:
            res = event.data.get("elemental_reaction")
            if res:
                # 尝试转换为月曜反应
                res = self._try_convert_to_lunar(event, res)
                self._apply_reaction_effect(event, res)
        elif event.event_type == EventType.ELECTRO_CHARGED_TICK:
            self._handle_ec_tick(event)
        elif event.event_type == EventType.BURNING_TICK:
            self._handle_burning_tick(event)
        elif event.event_type == EventType.LUNAR_CHARGED_TICK:
            self._handle_lunar_charged_tick(event)
        elif event.event_type == EventType.LUNAR_CRYSTALLIZE_ATTACK:
            self._handle_lunar_crystallize_attack(event)

    def _handle_ec_tick(self, event: GameEvent) -> None:
        """处理感电周期性跳电伤害。"""
        target = event.data.get("target")
        # 产生感电剧变伤害 (倍率 1.2)
        self._generate_transformative_damage(
            source_char=target,  # Tick 伤害源简化处理为目标自身
            target=target,
            r_type=ElementalReactionType.ELECTRO_CHARGED,
            multiplier=1.2,
            element=Element.ELECTRO,
        )

    def _handle_burning_tick(self, event: GameEvent) -> None:
        """处理燃烧周期性范围伤害。"""
        target = event.data.get("target")

        from core.systems.contract.attack import AttackConfig, HitboxConfig, AOEShape

        react_dmg = Damage(
            damage_multiplier=(0.0,),
            element=(Element.PYRO, 0.0),
            config=AttackConfig(
                attack_tag="燃烧伤害",
                hitbox=HitboxConfig(shape=AOEShape.SPHERE, radius=1.0),
            ),
            name="燃烧伤害",
        )

        if target is None:
            return
        level_mult = get_reaction_multiplier(target.level)
        react_dmg.add_data("等级系数", level_mult)
        react_dmg.add_data("反应系数", 0.25)

        if self.context and self.context.space:
            self.context.space.broadcast_damage(target, react_dmg)

    def _generate_transformative_damage(
        self,
        source_char: Any,
        target: Any,
        r_type: ElementalReactionType,
        multiplier: float,
        element: Element,
    ) -> None:
        """产生一次性的剧变伤害。"""
        # 检查受击 ICD
        if not self._check_damage_icd(target, r_type):
            return

        level_mult = get_reaction_multiplier(source_char.level)

        # 构建符合物理定义的攻击标签
        tag = f"{r_type.value}伤害"
        if r_type == ElementalReactionType.SWIRL:
            tag = f"扩散{element.value}伤害"

        dmg = Damage(
            damage_multiplier=(0.0,),
            element=(element, 0.0),
            config=AttackConfig(attack_tag=tag),
            name=r_type.value,
        )
        dmg.add_data("等级系数", level_mult)
        dmg.add_data("反应系数", multiplier)

        if self.engine:
            self.engine.publish(
                GameEvent(
                    event_type=EventType.BEFORE_DAMAGE,
                    frame=get_current_time(),
                    source=source_char,
                    data={"character": source_char, "target": target, "damage": dmg},
                )
            )

    def _handle_crystallize(self, event: GameEvent, res: ReactionResult) -> None:
        """处理结晶反应。"""
        from core.entities.elemental_entities import CrystalShardEntity

        target = event.data.get("target")
        source_char = event.source

        if target is None:
            return
        base_shield = get_reaction_multiplier(source_char.level) * 1.0
        shard = CrystalShardEntity(
            creator=source_char,
            element=res.target_element,
            pos=tuple(target.pos),
            base_shield_hp=base_shield,
        )
        if self.context and self.context.space:
            self.context.space.register(shard)

    def _handle_bloom(self, event: GameEvent, res: ReactionResult) -> None:
        """处理绽放反应。"""
        from core.entities.elemental_entities import DendroCoreEntity

        target = event.data.get("target")
        source_char = event.source
        if target is None:
            return
        core = DendroCoreEntity(creator=source_char, pos=tuple(target.pos))
        if self.context and self.context.space:
            self.context.space.register(core)

    def _handle_superconduct(self, event: GameEvent, res: ReactionResult) -> None:
        """处理超导减抗逻辑。"""
        from core.effect.common import ResistanceDebuffEffect

        target = event.data.get("target")
        if target is None:
            return

        debuff = ResistanceDebuffEffect(
            owner=target,
            name="超导减抗",
            elements=["物理"],
            amount=40.0,
            duration=12 * 60,
        )
        active_effects = getattr(target, "active_effects", None)
        if active_effects is not None:
            for eff in active_effects:
                if eff.name == "超导减抗":
                    eff.duration = 12 * 60
                    return
            debuff.apply()

    def _handle_swirl(self, event: GameEvent, res: ReactionResult) -> None:
        """处理扩散反应的空间传播。"""
        target = event.data.get("target")
        source_char = event.source

        element_to_spread = res.target_element
        if element_to_spread != Element.ANEMO:
            if target is None:
                return
            if self.context and self.context.space:
                self.context.space.broadcast_element(
                    source=source_char,
                    element=element_to_spread,
                    u_value=1.0,
                    origin=(target.pos[0], target.pos[1]),
                    radius=6.0,
                    exclude_target=target,
                )

    def _handle_freeze(self, event: GameEvent, res: ReactionResult) -> None:
        """处理冻结状态。"""
        # 目前主要由 AuraManager 维护冻结元素量，此处可用于触发特定的 AFTER_FREEZE 事件
        pass

    def _handle_transformative(self, event: GameEvent, res: ReactionResult) -> None:
        """处理剧变类反应伤害产生逻辑。"""
        source_char = event.source
        target = event.data.get("target")

        # 检查受击 ICD
        if not self._check_damage_icd(target, res.reaction_type):
            return

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
            # 判定剧变伤害的元素属性 (严格对齐 V2.5 战斗物理规范)
            dmg_el = res.source_element
            if res.reaction_type == ElementalReactionType.SWIRL:
                # 扩散反应伤害元素取决于被扩散的元素 (target_element)
                dmg_el = res.target_element
            elif res.reaction_type == ElementalReactionType.OVERLOAD:
                dmg_el = Element.PYRO
            elif res.reaction_type == ElementalReactionType.SUPERCONDUCT:
                dmg_el = Element.CRYO
            elif res.reaction_type == ElementalReactionType.SHATTER:
                dmg_el = Element.PHYSICAL
            elif res.reaction_type in {ElementalReactionType.HYPERBLOOM, ElementalReactionType.BURGEON}:
                dmg_el = Element.DENDRO
            
            self._generate_transformative_damage(
                source_char=source_char,
                target=target,
                r_type=res.reaction_type,
                multiplier=base_mult,
                element=dmg_el,
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

    # ================================
    # 月曜反应相关方法
    # ================================

    def _try_convert_to_lunar(
        self,
        event: GameEvent,
        res: ReactionResult
    ) -> ReactionResult:
        """
        尝试将原反应转换为月曜反应。

        条件：
        1. 队伍中有对应触发角色
        2. 反应由角色触发（非敌人/环境）
        3. 元素组合匹配
        """
        source_char = event.source

        # 检查是否为角色触发
        if not self._is_character_source(source_char):
            return res

        # 获取队伍成员
        team_members = self._get_team_members()

        # 绽放 → 月绽放
        if res.reaction_type == ElementalReactionType.BLOOM:
            if self._can_trigger_lunar_bloom(team_members):
                return self._convert_to_lunar_bloom(res, source_char)

        # 感电 → 月感电
        elif res.reaction_type == ElementalReactionType.ELECTRO_CHARGED:
            if self._can_trigger_lunar_charged(team_members):
                return self._convert_to_lunar_charged(res, source_char)

        # 结晶（水） → 月结晶
        elif res.reaction_type == ElementalReactionType.CRYSTALLIZE:
            # 仅水元素结晶可转换
            if res.target_element == Element.HYDRO:
                if self._can_trigger_lunar_crystallize(team_members):
                    return self._convert_to_lunar_crystallize(res, source_char)

        return res

    def _is_character_source(self, source: Any) -> bool:
        """判定反应源是否为角色。"""
        from character.character import Character
        return isinstance(source, Character)

    def _get_team_members(self) -> list[Any]:
        """获取当前队伍成员。"""
        if self.context and self.context.space and self.context.space.team:
            return self.context.space.team.get_members()
        return []

    def _get_lunar_system(self) -> Any:
        """获取月曜系统实例。"""
        if self._lunar_system is None and self.context:
            from core.systems.lunar_system import LunarReactionSystem
            self._lunar_system = self.context.get_system(LunarReactionSystem)
        return self._lunar_system

    def _can_trigger_lunar_bloom(self, members: list[Any]) -> bool:
        """判定是否可触发月绽放。"""
        lunar_system = self._get_lunar_system()
        if lunar_system:
            return lunar_system.can_trigger_lunar_bloom(members)
        return False

    def _can_trigger_lunar_charged(self, members: list[Any]) -> bool:
        """判定是否可触发月感电。"""
        lunar_system = self._get_lunar_system()
        if lunar_system:
            return lunar_system.can_trigger_lunar_charged(members)
        return False

    def _can_trigger_lunar_crystallize(self, members: list[Any]) -> bool:
        """判定是否可触发月结晶。"""
        lunar_system = self._get_lunar_system()
        if lunar_system:
            return lunar_system.can_trigger_lunar_crystallize(members)
        return False

    def _convert_to_lunar_bloom(
        self,
        res: ReactionResult,
        source_char: Any
    ) -> ReactionResult:
        """将绽放转换为月绽放。"""
        return ReactionResult(
            reaction_type=ElementalReactionType.LUNAR_BLOOM,
            category=ReactionCategory.LUNAR,
            source_element=res.source_element,
            target_element=res.target_element,
            multiplier=res.multiplier,
            gauge_consumed=res.gauge_consumed,
            data={
                **res.data,
                "original_reaction": ElementalReactionType.BLOOM,
            }
        )

    def _convert_to_lunar_charged(
        self,
        res: ReactionResult,
        source_char: Any
    ) -> ReactionResult:
        """将感电转换为月感电。"""
        return ReactionResult(
            reaction_type=ElementalReactionType.LUNAR_CHARGED,
            category=ReactionCategory.LUNAR,
            source_element=res.source_element,
            target_element=res.target_element,
            multiplier=res.multiplier,
            gauge_consumed=res.gauge_consumed,
            data={
                **res.data,
                "original_reaction": ElementalReactionType.ELECTRO_CHARGED,
                "source_characters": [source_char],
            }
        )

    def _convert_to_lunar_crystallize(
        self,
        res: ReactionResult,
        source_char: Any
    ) -> ReactionResult:
        """将水结晶转换为月结晶。"""
        return ReactionResult(
            reaction_type=ElementalReactionType.LUNAR_CRYSTALLIZE,
            category=ReactionCategory.LUNAR,
            source_element=res.source_element,
            target_element=res.target_element,
            multiplier=res.multiplier,
            gauge_consumed=res.gauge_consumed,
            data={
                **res.data,
                "original_reaction": ElementalReactionType.CRYSTALLIZE,
                "source_characters": [source_char],
            }
        )

    def _apply_reaction_effect(self, event: GameEvent, res: ReactionResult) -> None:
        """根据反应类别分发逻辑。"""
        source_char = event.source
        target = event.data.get("target")

        get_emulation_logger().log_reaction(
            source_char=source_char,
            reaction_type=res.reaction_type.value,
            target=target,
        )

        # 月曜反应分支
        if res.category == ReactionCategory.LUNAR:
            self._apply_lunar_reaction_effect(event, res)
            return

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

    def _apply_lunar_reaction_effect(self, event: GameEvent, res: ReactionResult) -> None:
        """月曜反应效果分发。"""
        if res.reaction_type == ElementalReactionType.LUNAR_BLOOM:
            self._handle_lunar_bloom(event, res)
        elif res.reaction_type == ElementalReactionType.LUNAR_CHARGED:
            self._handle_lunar_charged(event, res)
        elif res.reaction_type == ElementalReactionType.LUNAR_CRYSTALLIZE:
            self._handle_lunar_crystallize(event, res)

    def _handle_lunar_bloom(self, event: GameEvent, res: ReactionResult) -> None:
        """
        处理月绽放反应：
        1. 生成草原核（保持原有绽放机制不变）
        2. 额外触发草露资源恢复

        注：丰穰之核由角色技能触发生成，非月绽放反应直接产物。
        """
        from core.entities.elemental_entities import DendroCoreEntity
        from core.systems.lunar_system import LunarReactionSystem

        target = event.data.get("target")
        source_char = event.source

        if target is None:
            return

        # 生成草原核（保持原有绽放机制）
        core = DendroCoreEntity(
            creator=source_char,
            pos=tuple(target.pos),
        )

        if self.context and self.context.space:
            self.context.space.register(core)

        # 额外触发草露恢复（月绽放特有）
        lunar_system = self.context.get_system(LunarReactionSystem) if self.context else None
        if lunar_system:
            lunar_system.start_grass_dew_recovery()

        # 发布月绽放事件
        if self.engine:
            self.engine.publish(GameEvent(
                event_type=EventType.AFTER_LUNAR_BLOOM,
                frame=get_current_time(),
                source=source_char,
                data={"target": target, "core": core},
            ))

    def _handle_lunar_charged(self, event: GameEvent, res: ReactionResult) -> None:
        """
        处理月感电反应：
        1. 生成/刷新雷暴云
        2. 取消普通感电的持续攻击
        """
        from core.entities.lunar_entities import ThunderCloudEntity

        target = event.data.get("target")
        source_char = event.source

        if target is None:
            return

        # 取消普通感电状态
        target.aura.is_electro_charged = False

        # 获取或创建雷暴云
        existing_cloud = self._find_nearby_thunder_cloud(target.pos)

        if existing_cloud:
            existing_cloud.refresh()
            existing_cloud.add_source_character(source_char)
        else:
            cloud = ThunderCloudEntity(
                creator=source_char,
                pos=self._calculate_cloud_position(source_char, target),
                source_characters=[source_char],
            )
            if self.context and self.context.space:
                self.context.space.register(cloud)

        # 发布月感电事件
        if self.engine:
            self.engine.publish(GameEvent(
                event_type=EventType.AFTER_LUNAR_CHARGED,
                frame=get_current_time(),
                source=source_char,
                data={"target": target},
            ))

    def _handle_lunar_crystallize(self, event: GameEvent, res: ReactionResult) -> None:
        """
        处理月结晶反应：
        1. 不生成晶片
        2. 尝试生成月笼（最多3枚）
        3. 累积触发计数
        """
        from core.entities.lunar_entities import LunarCageEntity
        from core.systems.lunar_system import LunarReactionSystem

        target = event.data.get("target")
        source_char = event.source

        if target is None:
            return

        # 计算应生成的月笼数量
        existing_cages = LunarCageEntity.count_nearby_cages(target.pos)
        cages_to_create = max(0, 3 - existing_cages)

        # 生成月笼
        for i in range(cages_to_create):
            cage_pos = self._calculate_cage_position(target.pos, i, cages_to_create)
            cage = LunarCageEntity(
                creator=source_char,
                pos=cage_pos,
            )
            if self.context and self.context.space:
                self.context.space.register(cage)

        # 累积触发计数
        lunar_system = self.context.get_system(LunarReactionSystem) if self.context else None
        if lunar_system:
            triggered, sources = lunar_system.check_and_reset_lunar_cage_counter()
            lunar_system.add_lunar_cage_counter(source_char)

            # 如果达到阈值，触发谐奏攻击
            if triggered:
                LunarCageEntity.trigger_attack(target, sources)

        # 发布月结晶事件
        if self.engine:
            self.engine.publish(GameEvent(
                event_type=EventType.AFTER_LUNAR_CRYSTALLIZE,
                frame=get_current_time(),
                source=source_char,
                data={"target": target, "cages_created": cages_to_create},
            ))

    def _handle_lunar_charged_tick(self, event: GameEvent) -> None:
        """
        处理雷暴云攻击：
        - 每2秒结算一次
        - 基于所有附着来源角色计算加权伤害
        """
        cloud = event.data.get("cloud")
        target = event.data.get("target")
        source_characters = event.data.get("source_characters", [])

        if not source_characters or target is None:
            return

        # 计算各角色的伤害组分
        damage_components = []
        for char in source_characters:
            component_dmg = self._calculate_lunar_charged_component(char, target)
            damage_components.append((char, component_dmg))

        # 加权求和
        final_damage = self._calculate_weighted_damage(damage_components)

        # 造成月曜伤害
        self._apply_lunar_damage(
            source=cloud,
            target=target,
            damage=final_damage,
            reaction_type=ElementalReactionType.LUNAR_CHARGED,
            element=Element.ELECTRO,
        )

    def _handle_lunar_crystallize_attack(self, event: GameEvent) -> None:
        """
        处理月笼谐奏攻击：
        - 基于3次月结晶中参与的角色计算加权伤害
        """
        cage = event.data.get("cage")
        target = event.data.get("target")
        source_characters = event.data.get("source_characters", [])

        if not source_characters or target is None:
            return

        # 计算各角色的伤害组分
        damage_components = []
        for char in source_characters:
            component_dmg = self._calculate_lunar_crystallize_component(char, target)
            damage_components.append((char, component_dmg))

        # 加权求和
        final_damage = self._calculate_weighted_damage(damage_components)

        # 造成月曜伤害
        self._apply_lunar_damage(
            source=cage,
            target=target,
            damage=final_damage,
            reaction_type=ElementalReactionType.LUNAR_CRYSTALLIZE,
            element=Element.GEO,
        )

    def _calculate_lunar_charged_component(
        self,
        character: Any,
        target: Any
    ) -> float:
        """
        计算单个角色的月感电伤害组分。

        反应倍率：1.8
        """
        level_coeff = get_reaction_multiplier(character.level)
        reaction_mult = 1.8  # 反应月感电倍率

        em = getattr(character, 'elemental_mastery', 0)
        lunar_em_coeff = 6 * em / (em + 2000)

        reaction_boost = 1 + lunar_em_coeff

        base_damage = level_coeff * reaction_mult * reaction_boost

        # 暴击判定
        crit_rate = getattr(character, 'crit_rate', 0)
        crit_dmg = getattr(character, 'crit_dmg', 0)

        if random.uniform(0, 100) <= crit_rate:
            base_damage *= (1 + crit_dmg / 100)

        # 抗性区
        res_coeff = self._get_resistance_coeff(target, Element.ELECTRO)

        return base_damage * res_coeff

    def _calculate_lunar_crystallize_component(
        self,
        character: Any,
        target: Any
    ) -> float:
        """
        计算单个角色的月结晶伤害组分。

        反应倍率：0.96
        """
        level_coeff = get_reaction_multiplier(character.level)
        reaction_mult = 0.96  # 反应月结晶倍率

        em = getattr(character, 'elemental_mastery', 0)
        lunar_em_coeff = 6 * em / (em + 2000)

        reaction_boost = 1 + lunar_em_coeff

        base_damage = level_coeff * reaction_mult * reaction_boost

        # 暴击判定
        crit_rate = getattr(character, 'crit_rate', 0)
        crit_dmg = getattr(character, 'crit_dmg', 0)

        if random.uniform(0, 100) <= crit_rate:
            base_damage *= (1 + crit_dmg / 100)

        # 抗性区
        res_coeff = self._get_resistance_coeff(target, Element.GEO)

        return base_damage * res_coeff

    def _calculate_weighted_damage(
        self,
        damage_components: list[tuple[Any, float]]
    ) -> float:
        """
        加权求和计算月曜伤害。

        公式：最终伤害 = 最高 + 次高÷2 + 其余之和÷12
        """
        if not damage_components:
            return 0.0

        damages = sorted([d[1] for d in damage_components], reverse=True)

        if len(damages) == 1:
            return damages[0]
        elif len(damages) == 2:
            return damages[0] + damages[1] / 2
        else:
            return damages[0] + damages[1] / 2 + sum(damages[2:]) / 12

    def _get_resistance_coeff(self, target: Any, element: Element) -> float:
        """计算抗性区系数。"""
        from core.systems.utils import AttributeCalculator

        el_name = element.value
        res = AttributeCalculator.get_val_by_name(target, f"{el_name}元素抗性") / 100.0

        if res < 0:
            return 1 - res / 2
        elif res > 0.75:
            return 1 / (1 + 4 * res)
        else:
            return 1 - res

    def _apply_lunar_damage(
        self,
        source: Any,
        target: Any,
        damage: float,
        reaction_type: ElementalReactionType,
        element: Element,
    ) -> None:
        """应用月曜伤害。"""
        dmg = Damage(
            damage_multiplier=(0.0,),
            element=(element, 0.0),  # 无附着
            config=AttackConfig(attack_tag=f"{reaction_type.value}伤害"),
            name=reaction_type.value,
        )
        dmg.damage = damage
        dmg.set_source(source)
        dmg.set_target(target)

        if self.engine:
            self.engine.publish(GameEvent(
                event_type=EventType.BEFORE_DAMAGE,
                frame=get_current_time(),
                source=source,
                data={"character": source, "target": target, "damage": dmg},
            ))

    def _find_nearby_thunder_cloud(self, pos: tuple[float, float, float]) -> Any | None:
        """查找附近的雷暴云。"""
        from core.entities.lunar_entities import ThunderCloudEntity

        for cloud in ThunderCloudEntity.active_clouds:
            dx = cloud.pos[0] - pos[0]
            dz = cloud.pos[1] - pos[1]
            if (dx * dx + dz * dz) ** 0.5 <= 8.0:
                return cloud
        return None

    def _calculate_cloud_position(
        self,
        source_char: Any,
        target: Any
    ) -> tuple[float, float, float]:
        """计算雷暴云生成位置。"""
        # 简化：在目标和角色之间生成
        if source_char and target:
            x = (source_char.pos[0] + target.pos[0]) / 2
            z = (source_char.pos[1] + target.pos[1]) / 2
            y = max(source_char.pos[2], target.pos[2]) + 1.0
            return (x, z, y)
        return tuple(target.pos) if target else (0.0, 0.0, 1.0)

    def _calculate_cage_position(
        self,
        target_pos: tuple[float, float, float],
        index: int,
        total: int
    ) -> tuple[float, float, float]:
        """计算月笼生成位置。"""
        import math

        radius = 3.0 + (index * 0.25)  # 3~3.5米
        angle = (2 * math.pi * index / total) if total > 0 else 0

        x = target_pos[0] + radius * math.cos(angle)
        z = target_pos[1] + radius * math.sin(angle)
        y = target_pos[2]

        return (x, z, y)
