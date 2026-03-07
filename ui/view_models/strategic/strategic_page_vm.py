import flet as ft
from dataclasses import dataclass, field
from typing import List, Optional
from ui.view_models.strategic.character_vm import CharacterViewModel
from ui.view_models.strategic.active_character_vm import ActiveCharacterProxy

@ft.observable
@dataclass
class StrategicPageViewModel:
    """
    战略页面顶层视图模型。
    协调侧边栏列表与详情面板的同步。
    """
    team_vms: List[CharacterViewModel] = field(default_factory=list)
    current_index: int = 0
    active_character_proxy: ActiveCharacterProxy = field(default_factory=ActiveCharacterProxy)

    def __post_init__(self):
        if self.team_vms:
            self.active_character_proxy.bind_to(self.team_vms[0])

    def select_member(self, index: int):
        if 0 <= index < len(self.team_vms):
            self.current_index = index
            self.active_character_proxy.bind_to(self.team_vms[index])
            self.notify()

    def update_team(self, vms: List[CharacterViewModel]):
        self.team_vms = vms
        self.select_member(self.current_index)
        self.notify()
