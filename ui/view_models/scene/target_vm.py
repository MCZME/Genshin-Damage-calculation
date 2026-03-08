import flet as ft
from dataclasses import dataclass
from typing import Dict, Any
from ui.view_models.base_vm import BaseViewModel
from core.data_models.scene_data_model import TargetDataModel

@ft.observable
@dataclass
class TargetViewModel(BaseViewModel[TargetDataModel]):
    """
    单个怪物目标的视图模型。
    聚合了属性编辑与位置同步逻辑。
    """
    @property
    def id(self) -> str: return self.model.id
    @property
    def name(self) -> str: return self.model.name
    
    def set_name(self, val: str):
        self.model.name = val
        self.notify_update()

    @property
    def level(self) -> int: return self.model.level
    def set_level(self, val: int):
        self.model.level = val
        self.notify_update()

    # --- 坐标代理 ---
    @property
    def x(self) -> float: return self.model.x
    def set_x(self, val: float):
        self.model.x = val
        self.notify_update()

    @property
    def z(self) -> float: return self.model.z
    def set_z(self, val: float):
        self.model.z = val
        self.notify_update()

    # --- 抗性代理 ---
    @property
    def resistances(self) -> Dict[str, float]:
        return self.model.resists

    def set_resistance(self, element: str, value: float):
        self.model.set_resistance(element, value)
        self.notify_update()

    def reset_position(self):
        self.model.x = 0.0
        self.model.z = 5.0
        self.notify_update()

    def to_simulator_format(self) -> Dict[str, Any]:
        """代理底层 DataModel 的序列化逻辑"""
        return self.model.to_simulator_format()

