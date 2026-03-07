import flet as ft
from dataclasses import dataclass
from typing import Optional
from ui.view_models.base_vm import BaseViewModel
from core.data_models.team_data_model import WeaponDataModel

@ft.observable
@dataclass
class WeaponViewModel(BaseViewModel[WeaponDataModel]):
    """
    武器装备的视图模型。
    """
    @property
    def name(self) -> str:
        return self.model.name

    def set_weapon_id(self, weapon_id: str):
        """更换武器ID，并重置等级"""
        self.model.name = weapon_id
        # 业务逻辑：更换武器后通常保持 90 级或重置？
        # 这里保持原有逻辑
        self.notify_update()

    @property
    def level(self) -> int:
        return self.model.level

    def set_level(self, val: int):
        self.model.level = val
        self.notify_update()

    @property
    def refinement(self) -> int:
        return self.model.refinement

    def set_refinement(self, val: int):
        self.model.refinement = val
        self.notify_update()

    @property
    def display_name(self) -> str:
        return self.name.upper() if self.name else "未装备武器"
