"""能量设置规则类型。"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from core.rules.base import RuleTypeBase, ApplyMode
from core.registry import register_rule_type

if TYPE_CHECKING:
    from core.context import SimulationContext


@register_rule_type("energy_set")
class EnergySetRule(RuleTypeBase):
    """
    能量设置规则。

    在模拟开始时设置角色的初始能量状态。
    应用模式：一次性。
    """

    rule_type_id = "energy_set"
    display_name = "能量设置"
    description = "设置角色的初始能量状态"
    apply_mode = ApplyMode.ONCE

    param_schema = [
        {
            "key": "energy_state",
            "label": "能量状态",
            "type": "select",
            "default": "full",
            "options": {
                "full": "满能量",
                "empty": "零能量"
            }
        }
    ]

    def apply(
        self,
        params: dict[str, Any],
        ctx: SimulationContext
    ) -> None:
        """
        应用能量设置到所有角色。

        Args:
            params: 参数字典，包含 energy_state
            ctx: 模拟上下文
        """
        from core.event import GameEvent, EventType
        from core.tool import get_current_time

        energy_state = params.get("energy_state", "full")

        # 获取所有角色
        if ctx.space is None or ctx.space.team is None:
            return

        targets = ctx.space.team.get_members()
        for target in targets:
            if hasattr(target, 'elemental_energy') and target.elemental_energy:
                old_energy = target.elemental_energy.current_energy

                if energy_state == "full":
                    target.elemental_energy.fill()
                else:
                    target.elemental_energy.clear()

                new_energy = target.elemental_energy.current_energy
                delta = new_energy - old_energy

                # 发布能量变动事件
                if ctx.event_engine:
                    ctx.event_engine.publish(
                        GameEvent(
                            event_type=EventType.AFTER_ENERGY_CHANGE,
                            frame=get_current_time(),
                            source=target,
                            data={
                                "character": target,
                                "new_energy": new_energy,
                                "delta": delta,
                                "source_type": "规则设置",
                            }
                        )
                    )
