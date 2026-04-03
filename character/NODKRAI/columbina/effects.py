"""哥伦比娅效果类：新月之示、月诱、皎辉等。"""

from __future__ import annotations
from typing import Any

from core.effect.base import BaseEffect, StackingRule
from core.effect.common import StatModifierEffect
from core.logger import get_emulation_logger
from core.systems.utils import AttributeCalculator


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

class RadianceEffect(StatModifierEffect):
    """
    皎辉效果。

    C2命座触发引力干涉时获得，持续8秒。
    生命值上限提升40%。

    皎辉期间触发引力干涉时，会同时触发月兆·满辉效果。
    """

    def __init__(self, owner: Any):
        super().__init__(
            owner=owner,
            name="皎辉",
            stats={"生命值%": 40.0},
            duration=480,  # 8秒
        )
        self.stacking_rule = StackingRule.REFRESH

    def on_apply(self) -> None:
        """应用皎辉效果。"""
        super().on_apply()
        get_emulation_logger().log_info(
            f"[皎辉] {self.owner.name} 获得皎辉效果，生命值上限提升40%",
            sender="RadianceEffect"
        )

    def on_remove(self) -> None:
        """移除皎辉效果。"""
        super().on_remove()
        get_emulation_logger().log_info(
            f"[皎辉] {self.owner.name} 的皎辉效果结束",
            sender="RadianceEffect"
        )

    def on_stack_added(self, other: "BaseEffect") -> None:
        """刷新时重新应用modifier。"""
        # 刷新持续时间
        self.duration = self.max_duration


class C2StatBonusEffect(StatModifierEffect):
    """
    C2月兆·满辉属性加成效果。

    月兆·满辉状态下，皎辉期间触发引力干涉时，根据月曜类型为场上角色提供属性加成：
    - 月感电：固定攻击力 + 生命值上限的1%
    - 月绽放：元素精通 + 生命值上限的0.35%
    - 月结晶：固定防御力 + 生命值上限的1%

    加成持续到皎辉效果结束。
    """

    # 月曜类型 -> (属性名, 生命值倍率)
    LUNAR_BONUS_MAP = {
        "月感电": ("固定攻击力", 0.01),
        "月绽放": ("元素精通", 0.0035),
        "月结晶": ("固定防御力", 0.01),
    }

    def __init__(self, owner: Any, source_char: Any, lunar_type: str, duration: float):
        """
        Args:
            owner: 效果持有者（场上角色）
            source_char: 哥伦比娅（用于计算生命值上限）
            lunar_type: 月曜反应类型
            duration: 持续帧数（应与皎辉剩余时间一致）
        """
        self.source_char = source_char
        self.lunar_type = lunar_type

        # 计算属性加成
        stat_name, multiplier = self.LUNAR_BONUS_MAP.get(lunar_type, ("元素精通", 0.0035))
        source_hp = AttributeCalculator.get_val_by_name(source_char, "生命值")
        bonus_value = source_hp * multiplier

        super().__init__(
            owner=owner,
            name=f"C2月兆·满辉-{lunar_type}",
            stats={stat_name: bonus_value},
            duration=duration,
        )

        self.bonus_value = bonus_value

    def on_apply(self) -> None:
        """应用属性加成。"""
        super().on_apply()
        stat_name = list(self.stats.keys())[0]
        get_emulation_logger().log_info(
            f"[C2月兆·满辉] {self.lunar_type}为 {self.owner.name} 提供 {stat_name}+{round(self.bonus_value, 1)}",
            sender="C2StatBonusEffect"
        )
