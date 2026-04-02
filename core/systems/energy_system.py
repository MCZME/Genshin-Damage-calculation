"""能量系统模块。"""
from typing import Any

from core.systems.base_system import GameSystem
from core.event import GameEvent, EventType
from core.systems.utils import AttributeCalculator
from core.logger import get_emulation_logger
from core.tool import get_current_time

# 类型别名 (Python 3.10+ 语法)
EnergyAmount = float | tuple[str, float]


class EnergySystem(GameSystem):
    """
    能量系统：处理微粒/球获取及固定数值恢复。

    负责计算能量获取系数并更新角色能量状态。
    """

    # 能量获取系数表: {元素匹配类型: {站场状态: 系数}}
    ENERGY_RATES: dict[str, dict[bool, float]] = {
        "同元素": {True: 3.0, False: 1.8},
        "异元素": {True: 1.0, False: 0.6},
        "无元素": {True: 2.0, False: 1.2},
    }

    def register_events(self, engine) -> None:
        """订阅能量变化前置事件。"""
        engine.subscribe(EventType.BEFORE_ENERGY_CHANGE, self)

    def handle_event(self, event: GameEvent) -> None:
        """事件分发处理。"""
        if event.event_type == EventType.BEFORE_ENERGY_CHANGE:
            self._handle_energy_change(event)

    def _handle_energy_change(self, event: GameEvent) -> None:
        """处理能量变化事件。"""
        data = event.data
        character = data["character"]
        amount: EnergyAmount = data["amount"]
        is_fixed = data.get("is_fixed", False)
        is_alone = data.get("is_alone", False)

        team_obj = getattr(self.context, "team", None)
        source_character = data.get("source_character", character)

        self._apply_energy(
            character, amount, is_fixed, is_alone, team_obj, source_character
        )

    def _apply_energy(
        self,
        character: Any,
        amount: EnergyAmount,
        is_fixed: bool,
        is_alone: bool,
        team_obj: Any,
        source_character: Any,
    ) -> None:
        """
        应用能量恢复。

        Args:
            character: 目标角色
            amount: 能量值 (固定值) 或 (元素, 数量) 元组
            is_fixed: 是否为固定值恢复
            is_alone: 是否为独立计算
            team_obj: 队伍对象
            source_character: 能量来源角色
        """
        # 计算能量值
        if is_fixed:
            raw_value = amount[1] if isinstance(amount, tuple) else amount
            source_type = "固定值"
        else:
            if not isinstance(amount, tuple):
                raise TypeError("非固定值能量恢复需要 tuple[str, float] 类型")
            rate = self.get_rate(character, amount[0], team_obj)
            raw_value = amount[1] * rate
            source_type = f"{amount[0]}元素微粒"

        # 使用 ElementalEnergy.gain() 统一处理 (自动上限检查)
        actual_value = character.elemental_energy.gain(raw_value)

        # 记录日志
        get_emulation_logger().log_energy(
            character, actual_value, source_type=source_type
        )

        # 发布能量变动后置事件
        if self.engine:
            self.engine.publish(
                GameEvent(
                    event_type=EventType.AFTER_ENERGY_CHANGE,
                    frame=get_current_time(),
                    source=character,
                    data={
                        "character": character,
                        "new_energy": character.elemental_energy.current_energy,
                        "delta": actual_value,
                        "source_type": source_type,
                    }
                )
            )

    def get_rate(self, character: Any, particle_element: str, team_obj: Any) -> float:
        """
        计算微粒获取系数。

        Args:
            character: 目标角色
            particle_element: 微粒元素类型
            team_obj: 队伍对象

        Returns:
            float: 最终获取系数
        """
        char_element = character.elemental_energy.element
        is_same = particle_element == char_element
        is_neutral = particle_element == "无"
        on_field = getattr(character, "on_field", True)

        # 确定元素匹配类型
        if is_neutral:
            match_type = "无元素"
        elif is_same:
            match_type = "同元素"
        else:
            match_type = "异元素"

        # 获取基础系数
        base = self.ENERGY_RATES[match_type][on_field]

        # 应用充能效率
        energy_rate = AttributeCalculator.get_final_er(character) / 100.0
        return base * energy_rate
