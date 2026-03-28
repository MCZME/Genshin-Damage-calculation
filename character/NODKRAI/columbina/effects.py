"""哥伦比娅效果类：新月之示、月诱等。"""

from __future__ import annotations
from typing import Any

from core.effect.base import BaseEffect, StackingRule
from core.effect.common import StatModifierEffect


class CrescentSignEffect(BaseEffect):
    """
    新月之示效果。

    触发月曜反应或造成月曜伤害时获得，持续2秒。
    效果持续期间每2秒积攒20点引力值。
    """

    def __init__(self, owner: Any, lunar_type: str = "月绽放"):
        """
        Args:
            owner: 效果持有者（哥伦比娅）
            lunar_type: 触发时的月曜类型，用于确定引力值来源
        """
        super().__init__(
            owner,
            name="新月之示",
            duration=120,  # 2秒 = 120帧
            stacking_rule=StackingRule.REFRESH,
        )
        self.lunar_type = lunar_type
        self.accumulate_timer = 0
        self.accumulate_interval = 120  # 每2秒积攒一次

    def on_apply(self) -> None:
        """效果应用时重置积攒计时器。"""
        self.accumulate_timer = 0

    def on_tick(self, target: Any) -> None:
        """每帧更新，检查是否需要积攒引力值。"""
        self.accumulate_timer += 1

        if self.accumulate_timer >= self.accumulate_interval:
            # 积攒20点引力值
            self.owner.add_gravity(20, self.lunar_type)
            self.accumulate_timer = 0

    def on_stack_added(self, other: "BaseEffect") -> None:
        """
        刷新效果时更新月曜类型。

        如果新的效果来自不同的月曜类型，更新为最新类型。
        """
        if isinstance(other, CrescentSignEffect):
            self.lunar_type = other.lunar_type
            self.accumulate_timer = 0  # 重置计时器


class LunarInducementStack(StatModifierEffect):
    """
    月诱层数效果。

    每层提供5%暴击率，持续10秒。
    使用 ADD 堆叠规则，至多3层。
    """

    def __init__(self, owner: Any):
        super().__init__(
            owner=owner,
            name="月诱",
            stats={"暴击率": 5.0},
            duration=600,  # 10秒
        )
        self.stacking_rule = StackingRule.ADD
        self.max_stacks = 3
        self._stacks = 1

    def on_stack_added(self, other: "BaseEffect") -> None:
        """叠加时刷新持续时间并增加层数。"""
        if self._stacks < self.max_stacks:
            # 添加新的修饰符
            modifier = self.owner.add_modifier(self.name, "暴击率", 5.0)
            self.modifier_records.append(modifier)
            self._stacks += 1

        # 刷新持续时间
        self.duration = self.max_duration
