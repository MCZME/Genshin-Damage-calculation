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

    在模拟开始时设置角色的初始能量百分比。
    应用模式：一次性。
    """

    rule_type_id = "energy_set"
    display_name = "能量设置"
    description = "设置角色的初始能量百分比"
    apply_mode = ApplyMode.ONCE

    param_schema = [
        {
            "key": "energy_percent",
            "label": "能量百分比",
            "type": "number",
            "default": 100,
            "min": 0,
            "max": 100,
            "unit": "%"
        }
    ]

    def apply(
        self,
        target: Any,
        params: dict[str, Any],
        ctx: SimulationContext
    ) -> None:
        """
        应用能量设置。

        Args:
            target: 目标实体（角色）
            params: 参数字典，包含 energy_percent
            ctx: 模拟上下文
        """
        percent = params.get("energy_percent", 100) / 100.0

        if hasattr(target, 'elemental_energy') and target.elemental_energy:
            target.elemental_energy.current_energy = (
                target.elemental_energy.max_energy * percent
            )
