import flet as ft
from dataclasses import dataclass
from typing import Optional

@ft.observable
@dataclass
class LayoutViewModel:
    """
    主布局视图模型。
    管理导航、侧边栏折叠状态及全局仿真进度。
    """
    current_phase: str = "strategic"
    sim_status: str = "IDLE"
    sim_progress: float = 0.0
    is_simulating: bool = False

    def switch_tab(self, phase_id: str):
        self.current_phase = phase_id
        self.notify()

    def update_simulation(self, status: str, progress: float, is_running: bool):
        self.sim_status = status
        self.sim_progress = progress
        self.is_simulating = is_running
        self.notify()
