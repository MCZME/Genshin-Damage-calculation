from __future__ import annotations
import flet as ft
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ui.states.analysis_state import AnalysisState
    from ui.services.analysis_data_service import DataSlot

class AnalysisTile(ABC):
    """
    分析磁贴基类 (V4.7 订阅制版)
    所有业务磁贴必须继承此类，通过引用计数机制按需获取数据。
    """
    def __init__(self, title: str, icon: ft.IconData, tile_type: str, state: AnalysisState):
        self.title = title
        self.icon = icon
        self.tile_type = tile_type
        self.state = state
        self.instance_id: str | None = None # 由 View 在创建时分配
        self.expand = False
        self.has_settings = False # [V8.8] 默认不支持设置按钮

    @abstractmethod
    def render(self) -> ft.Control:
        """渲染磁贴内容核心区"""
        pass

    async def subscribe_data(self) -> DataSlot | None:
        """
        向 DataManager 订阅本磁贴所需的数据切片。
        """
        if not self.instance_id:
            return None
        return await self.state.data_service.subscribe(self.tile_type, self.instance_id)

    async def unsubscribe_data(self):
        """
        释放订阅，允许 DataManager 在无引用时清理内存。
        """
        if self.instance_id:
            await self.state.data_service.unsubscribe(self.tile_type, self.instance_id)

    def on_settings_click(self, btn: ft.Control):
        """
        [V8.9] 设置按钮点击回调。由子类重写以实现具体的设置逻辑（如弹出对话框）。
        """
        pass

    def get_settings_items(self) -> list[ft.PopupMenuItem]:
        """
        [V9.0] 获取设置菜单项。若返回非空列表，容器将自动渲染为 PopupMenuButton。
        """
        return []
