from __future__ import annotations
import flet as ft
from dataclasses import dataclass
from ui.view_models.base_vm import BaseViewModel
from core.data_models.team_data_model import WeaponDataModel

@ft.observable
@dataclass
class WeaponViewModel(BaseViewModel[WeaponDataModel]):
    """
    武器装备的视图模型。
    支持 model 为 None 的空槽位状态。
    """
    @property
    def name(self) -> str:
        return self.model.name if self.model else ""

    def set_weapon_id(self, weapon_id: str):
        """更换武器ID，并重置等级"""
        if self.model:
            self.model.name = weapon_id
            self.notify_update()

    @property
    def level(self) -> int:
        return self.model.level if self.model else 1

    def set_level(self, val: int):
        if self.model:
            self.model.level = val
            self.notify_update()

    @property
    def refinement(self) -> int:
        return self.model.refinement if self.model else 1

    def set_refinement(self, val: int):
        if self.model:
            self.model.refinement = val
            self.notify_update()

    @property
    def display_name(self) -> str:
        return self.name.upper() if self.name else "未装备武器"
