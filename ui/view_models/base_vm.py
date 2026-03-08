from __future__ import annotations
import flet as ft
from typing import Generic, TypeVar, Any, cast
from dataclasses import dataclass

T = TypeVar("T") # 对应的 Data Model 类型

@ft.observable
@dataclass
class BaseViewModel(Generic[T]):
    """
    视图模型基类。
    利用 Flet 的 @ft.observable 实现响应式，通过代理模式操作底层 Data Model。
    """
    model: T | None

    def notify_update(self):
        """
        显式触发 UI 变更通知。
        解决 Pylance 无法识别运行时注入的 notify() 的问题。
        """
        cast(Any, self).notify()
