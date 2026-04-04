"""规则类型基类定义。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from core.context import SimulationContext


class ApplyMode(Enum):
    """规则应用模式。"""
    ONCE = "once"           # 开始时应用一次
    SUBSCRIBE = "subscribe" # 订阅事件持续应用


class RuleTypeBase(ABC):
    """
    规则类型基类。

    定义规则的行为、参数 schema 和应用模式。
    子类需要实现 apply() 方法（一次性模式）或 on_event() 方法（订阅模式）。
    """

    # 类属性：类型标识
    rule_type_id: str
    # 类属性：UI 显示信息
    display_name: str
    description: str = ""
    # 类属性：应用模式
    apply_mode: ApplyMode = ApplyMode.ONCE
    # 类属性：参数 schema（用于 UI 渲染）
    param_schema: list[dict[str, Any]] = []

    @classmethod
    def get_schema(cls) -> dict[str, Any]:
        """
        获取完整的 UI schema。

        Returns:
            包含 display_name、description、params 的字典
        """
        return {
            "display_name": cls.display_name,
            "description": cls.description,
            "params": cls.param_schema
        }

    @abstractmethod
    def apply(self, target: Any, params: dict[str, Any], ctx: SimulationContext) -> None:
        """
        应用规则到目标。

        一次性模式：模拟开始时调用一次。
        订阅模式：可选实现，用于初始化。

        Args:
            target: 目标实体
            params: 实例参数
            ctx: 模拟上下文
        """
        ...

    def get_event_filter(self) -> str | None:
        """
        订阅模式：返回监听的事件类型。

        Returns:
            事件类型字符串，如 "on_damage_dealt"、"on_character_switch"
        """
        return None

    def on_event(
        self,
        event: Any,
        target: Any,
        params: dict[str, Any],
        ctx: SimulationContext
    ) -> None:
        """
        订阅模式：事件触发时的处理逻辑。

        Args:
            event: 事件对象
            target: 目标实体
            params: 实例参数
            ctx: 模拟上下文
        """
        pass

    def validate_params(self, params: dict[str, Any]) -> bool:
        """
        验证参数是否有效。

        默认实现检查必需参数是否存在且在范围内。
        子类可重写以实现更复杂的验证逻辑。

        Args:
            params: 参数字典

        Returns:
            参数是否有效
        """
        for param in self.param_schema:
            key = param.get("key")
            if key is None:
                continue

            value = params.get(key)

            # 检查必需参数
            if param.get("required", False) and value is None:
                return False

            # 检查数值范围
            if value is not None:
                if "min" in param and value < param["min"]:
                    return False
                if "max" in param and value > param["max"]:
                    return False

        return True
