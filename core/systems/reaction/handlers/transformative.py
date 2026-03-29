"""剧变反应处理器模块。"""

from typing import Any

from core.systems.contract.attack import AttackConfig
from core.systems.contract.damage import Damage
from core.systems.contract.reaction import ElementalReactionType
from core.event import EventType, GameEvent
from core.mechanics.aura import Element
from core.tool import get_current_time, get_reaction_multiplier

from ..icd import ICDManager


class TransformativeHandler:
    """
    剧变反应处理器。

    处理感电、燃烧、超载、超导等剧变反应的伤害生成。
    """

    def __init__(self, icd_manager: ICDManager):
        self._icd_manager = icd_manager
        self._context: Any = None
        self._engine: Any = None

    def set_context(self, context: Any) -> None:
        """设置仿真上下文。"""
        self._context = context

    def set_engine(self, engine: Any) -> None:
        """设置事件引擎。"""
        self._engine = engine

    def handle_ec_tick(self, event: GameEvent) -> None:
        """处理感电周期性跳电伤害。

        感电机制：
        1. 对被触发目标自身造成感电伤害
        2. 对范围内有水附着的同阵营目标造成传导攻击
        """
        target = event.data.get("target")
        if target is None:
            return

        # 1. 对目标自身造成感电伤害 (倍率 1.2)
        self._generate_transformative_damage(
            source_char=target,  # Tick 伤害源简化处理为目标自身
            target=target,
            r_type=ElementalReactionType.ELECTRO_CHARGED,
            multiplier=1.2,
            element=Element.ELECTRO,
        )

        # 2. 传导攻击：对范围内水附着目标造成伤害
        if self._context and self._context.space:
            self._conduct_ec_damage(target)

    def _conduct_ec_damage(self, source_target: Any) -> None:
        """感电传导：对范围内水附着目标造成伤害。

        规则：
        - 范围约 5 米
        - 目标需与被触发目标同阵营
        - 目标需有水附着
        - 不会对源目标自身造成传导伤害
        """
        if not self._context or not self._context.space:
            return

        targets = self._context.space.get_entities_in_range(
            origin=(source_target.pos[0], source_target.pos[1]),
            radius=5.0,
            faction=source_target.faction,  # 同阵营
        )

        for t in targets:
            if t == source_target:
                continue
            # 检查是否有水附着
            if self._has_hydro_aura(t):
                self._generate_transformative_damage(
                    source_char=source_target,
                    target=t,
                    r_type=ElementalReactionType.ELECTRO_CHARGED,
                    multiplier=1.2,
                    element=Element.ELECTRO,
                )

    def _has_hydro_aura(self, target: Any) -> bool:
        """检查目标是否有水附着。"""
        if not hasattr(target, "aura"):
            return False
        return any(a.element == Element.HYDRO for a in target.aura.auras)

    def handle_burning_tick(self, event: GameEvent) -> None:
        """处理燃烧周期性范围伤害。"""
        from core.systems.contract.attack import HitboxConfig, AOEShape

        target = event.data.get("target")

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

        if self._context and self._context.space:
            self._context.space.broadcast_damage(target, react_dmg)

    def handle_transformative(self, event: GameEvent, res: Any) -> None:
        """处理剧变类反应伤害产生逻辑。"""
        source_char = event.source
        target = event.data.get("target")

        # 检查受击 ICD
        if not self._icd_manager.check(target, res.reaction_type):
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
        if not self._icd_manager.check(target, r_type):
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

        if self._engine:
            self._engine.publish(
                GameEvent(
                    event_type=EventType.BEFORE_DAMAGE,
                    frame=get_current_time(),
                    source=source_char,
                    data={"character": source_char, "target": target, "damage": dmg},
                )
            )
