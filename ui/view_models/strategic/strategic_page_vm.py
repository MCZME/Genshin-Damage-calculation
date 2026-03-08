from __future__ import annotations
import flet as ft
from dataclasses import dataclass, field
from typing import Any, cast
from ui.view_models.strategic.character_vm import CharacterViewModel
from ui.view_models.strategic.active_character_vm import ActiveCharacterProxy

@ft.observable
@dataclass
class StrategicPageViewModel:
    """
    战略页面视图模型。
    管理队伍中 4 个角色的 VM 及其代理状态。
    """
    team_vms: list[CharacterViewModel] = field(default_factory=list)
    active_index: int = 0
    active_char_proxy: ActiveCharacterProxy | None = None

    def __post_init__(self):
        # 初始化 4 个空槽位
        if not self.team_vms:
            self.team_vms = [CharacterViewModel(None) for _ in range(4)]
        self._update_proxy()

    def notify_update(self):
        """显式触发变更通知，解决静态检查报错"""
        cast(Any, self).notify()

    def select_character(self, index: int):
        if 0 <= index < 4:
            self.active_index = index
            self._update_proxy()
            self.notify_update()

    def _update_proxy(self):
        """更新当前活动角色的属性代理"""
        target_vm = self.team_vms[self.active_index]
        self.active_char_proxy = ActiveCharacterProxy(target_vm)

    def swap_character(self, idx1: int, idx2: int):
        if 0 <= idx1 < 4 and 0 <= idx2 < 4:
            self.team_vms[idx1], self.team_vms[idx2] = self.team_vms[idx2], self.team_vms[idx1]
            self._update_proxy()
            self.notify_update()
