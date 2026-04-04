"""属性效果规则类型。"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from core.rules.base import RuleTypeBase, ApplyMode
from core.registry import register_rule_type

if TYPE_CHECKING:
    from core.context import SimulationContext


@register_rule_type("stat_effect")
class StatEffectRule(RuleTypeBase):
    """
    属性效果规则。

    为角色添加永久属性修改效果。
    应用模式：一次性。
    """

    rule_type_id = "stat_effect"
    display_name = "属性效果"
    description = "为角色或目标添加属性效果"
    apply_mode = ApplyMode.ONCE

    param_schema = [
        {
            "key": "stat",
            "label": "属性",
            "type": "select",
            "default": "攻击力%",
            "options": [
                "攻击力%", "攻击力", "生命值%", "生命值",
                "防御力%", "防御力", "元素精通", "暴击率",
                "暴击伤害", "伤害加成", "火元素伤害加成",
                "水元素伤害加成", "雷元素伤害加成", "冰元素伤害加成",
                "风元素伤害加成", "岩元素伤害加成", "草元素伤害加成",
                "物理伤害加成", "火元素抗性", "水元素抗性",
                "雷元素抗性", "冰元素抗性", "风元素抗性",
                "岩元素抗性", "草元素抗性", "物理抗性"
            ]
        },
        {
            "key": "value",
            "label": "数值",
            "type": "number",
            "default": 15.0,
            "min": -200,
            "max": 500
        }
    ]

    def apply(
        self,
        params: dict[str, Any],
        ctx: SimulationContext
    ) -> None:
        """
        应用属性效果到所有角色。

        Args:
            params: 参数字典，包含 stat, value
            ctx: 模拟上下文
        """
        from core.effect.common import StatModifierEffect

        stat = params.get("stat", "攻击力%")
        value = params.get("value", 0)

        # 获取所有角色
        if ctx.space is None or ctx.space.team is None:
            return

        targets = ctx.space.team.get_members()
        for target in targets:
            # 创建永久效果 (duration=-1 表示永久)
            effect = StatModifierEffect(
                owner=target,
                name=f"规则效果:{stat}",
                stats={stat: value},
                duration=-1
            )
            # 应用效果
            effect.apply()
