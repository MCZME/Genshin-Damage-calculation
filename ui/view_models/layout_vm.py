from __future__ import annotations
import flet as ft
from dataclasses import dataclass
from typing import Any, cast

@ft.observable
@dataclass
class LayoutViewModel:
    """
    布局视图模型。
    管理页面导航及抽屉/边栏的可见性状态。
    """
    current_phase: str = "strategic" # strategic, scene, tactical, review
    drawer_opened: bool = False
    settings_open: bool = False  # 设置对话框可见性

    def notify_update(self):
        """显式触发变更通知，解决静态检查报错"""
        cast(Any, self).notify()

    def switch_tab(self, phase_id: str):
        """切换导航标签页"""
        self.current_phase = phase_id
        self.notify_update()

    def toggle_drawer(self):
        """切换侧边抽屉状态"""
        self.drawer_opened = not self.drawer_opened
        self.notify_update()

    def toggle_settings(self):
        """切换设置对话框状态"""
        self.settings_open = not self.settings_open
        self.notify_update()
    
    def update_simulation(self, status: str, progress: float, is_running: bool):
        self.sim_status = status
        self.sim_progress = progress
        self.is_simulating = is_running
        self.notify_update()
