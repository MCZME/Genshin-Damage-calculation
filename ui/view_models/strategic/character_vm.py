from __future__ import annotations
import flet as ft
from dataclasses import dataclass
from ui.view_models.base_vm import BaseViewModel
from core.data_models.team_data_model import CharacterDataModel
from ui.view_models.strategic.weapon_vm import WeaponViewModel
from ui.view_models.strategic.artifact_vm import ArtifactPieceViewModel

@ft.observable
@dataclass
class CharacterViewModel(BaseViewModel[CharacterDataModel]):
    """
    角色全量视图模型 (聚合根)。
    组合了 WeaponVM 和 ArtifactVMs。
    支持 model 为 None 的空角色槽位。
    """
    def __post_init__(self):
        # 预加载子 VM，支持空模型
        if self.model:
            self._weapon_vm = WeaponViewModel(self.model.weapon)
            self._artifact_vms: dict[str, ArtifactPieceViewModel] = {}
            slots = ["Flower", "Plume", "Sands", "Goblet", "Circlet"]
            for slot in slots:
                self._artifact_vms[slot] = ArtifactPieceViewModel(
                    self.model.artifacts.get_slot(slot), 
                    slot_name=slot
                )
        else:
            # 构造空槽位专用的子 VM
            self._weapon_vm = WeaponViewModel(None)
            self._artifact_vms = {
                slot: ArtifactPieceViewModel(None, slot_name=slot)
                for slot in ["Flower", "Plume", "Sands", "Goblet", "Circlet"]
            }

    @property
    def name(self) -> str:
        return self.model.name if self.model else "未选择角色"
    
    @property
    def element(self) -> str:
        return self.model.element if self.model else "Neutral"

    @property
    def level(self) -> int:
        return self.model.level if self.model else 1
    
    def set_level(self, val: int):
        if self.model:
            self.model.level = val
            self.notify_update()

    @property
    def constellation(self) -> int:
        return self.model.constellation if self.model else 0
    
    def set_constellation(self, val: int):
        if self.model:
            self.model.constellation = val
            self.notify_update()

    # --- 天赋代理 ---
    @property
    def talent_na(self) -> int:
        return self.model.talent_levels.get("na", 1) if self.model else 1
    
    def set_talent_na(self, val: int):
        if self.model:
            self.model.set_talent("na", val)
            self.notify_update()

    @property
    def talent_e(self) -> int:
        return self.model.talent_levels.get("e", 1) if self.model else 1
    
    def set_talent_e(self, val: int):
        if self.model:
            self.model.set_talent("e", val)
            self.notify_update()

    @property
    def talent_q(self) -> int:
        return self.model.talent_levels.get("q", 1) if self.model else 1
    
    def set_talent_q(self, val: int):
        if self.model:
            self.model.set_talent("q", val)
            self.notify_update()

    # --- 子 VM 访问 ---
    @property
    def weapon(self) -> WeaponViewModel:
        return self._weapon_vm

    @property
    def artifacts(self) -> dict[str, ArtifactPieceViewModel]:
        return self._artifact_vms

    @property
    def is_empty(self) -> bool:
        return self.model is None or self.model.id is None
