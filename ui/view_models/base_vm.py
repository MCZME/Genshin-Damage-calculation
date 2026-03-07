import flet as ft
from typing import Generic, TypeVar, Dict, Any
from dataclasses import dataclass

T = TypeVar("T") # 对应的 Data Model 类型

@ft.observable
@dataclass
class BaseViewModel(Generic[T]):
    """
    视图模型基类。
    利用 Flet 的 @ft.observable 实现响应式，通过代理模式操作底层 Data Model。
    """
    model: T

    def notify_update(self):
        """
        显式触发 UI 变更通知。
        Flet V3 中，修改嵌套数据后必须调用此方法以确保 UI 刷新。
        """
        self.notify()
