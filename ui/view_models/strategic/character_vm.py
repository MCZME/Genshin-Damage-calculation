import flet as ft
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
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
    """
    def __post_init__(self):
        # 预加载子 VM
        self._weapon_vm = WeaponViewModel(self.model.weapon)
        
        # 预加载 5 个槽位的圣遗物 VM
        self._artifact_vms: Dict[str, ArtifactPieceViewModel] = {}
        slots = ["Flower", "Plume", "Sands", "Goblet", "Circlet"]
        for slot in slots:
            self._artifact_vms[slot] = ArtifactPieceViewModel(
                self.model.artifacts.get_slot(slot), 
                slot_name=slot
            )

    @property
    def name(self) -> str: return self.model.name
    
    @property
    def element(self) -> str: return self.model.element

    @property
    def level(self) -> int: return self.model.level
    def set_level(self, val: int):
        self.model.level = val
        self.notify_update()

    @property
    def constellation(self) -> int: return self.model.constellation
    def set_constellation(self, val: int):
        self.model.constellation = val
        self.notify_update()

    # --- 天赋代理 ---
    @property
    def talent_na(self) -> int: return self.model.talent_levels.get("na", 1)
    def set_talent_na(self, val: int):
        self.model.set_talent("na", val)
        self.notify_update()

    @property
    def talent_e(self) -> int: return self.model.talent_levels.get("e", 1)
    def set_talent_e(self, val: int):
        self.model.set_talent("e", val)
        self.notify_update()

    @property
    def talent_q(self) -> int: return self.model.talent_levels.get("q", 1)
    def set_talent_q(self, val: int):
        self.model.set_talent("q", val)
        self.notify_update()

    # --- 子 VM 访问 ---
    @property
    def weapon(self) -> WeaponViewModel:
        return self._weapon_vm

    @property
    def artifacts(self) -> Dict[str, ArtifactPieceViewModel]:
        return self._artifact_vms

    @property
    def is_empty(self) -> bool:
        return self.model.id is None
