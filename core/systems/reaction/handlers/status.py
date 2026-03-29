"""状态类反应处理器模块。"""

from typing import Any

from core.event import GameEvent
from core.systems.contract.reaction import ElementalReactionType
from core.mechanics.aura import Element
from core.tool import get_reaction_multiplier


class StatusHandler:
    """
    状态类反应处理器。

    处理结晶、绽放、超导、扩散、冻结等不直接产生伤害的反应。
    """

    def __init__(self):
        self._context: Any = None

    def set_context(self, context: Any) -> None:
        """设置仿真上下文。"""
        self._context = context

    def handle_crystallize(self, event: GameEvent, res: Any) -> None:
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
        if self._context and self._context.space:
            self._context.space.register(shard)

    def handle_bloom(self, event: GameEvent, res: Any) -> None:
        """处理绽放反应。"""
        from core.entities.elemental_entities import DendroCoreEntity

        target = event.data.get("target")
        source_char = event.source
        if target is None:
            return
        core = DendroCoreEntity(creator=source_char, pos=tuple(target.pos))
        if self._context and self._context.space:
            self._context.space.register(core)

    def handle_superconduct(self, event: GameEvent, res: Any) -> None:
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

    def handle_swirl(self, event: GameEvent, res: Any) -> None:
        """处理扩散反应的空间传播。"""
        target = event.data.get("target")
        source_char = event.source

        element_to_spread = res.target_element
        if element_to_spread != Element.ANEMO:
            if target is None:
                return
            if self._context and self._context.space:
                self._context.space.broadcast_element(
                    source=source_char,
                    element=element_to_spread,
                    u_value=1.0,
                    origin=(target.pos[0], target.pos[1]),
                    radius=6.0,
                    exclude_target=target,
                )

    def handle_freeze(self, event: GameEvent, res: Any) -> None:
        """处理冻结状态。"""
        # 目前主要由 AuraManager 维护冻结元素量，此处可用于触发特定的 AFTER_FREEZE 事件
        pass
