from __future__ import annotations
import flet as ft
from dataclasses import dataclass
from typing import Any, cast
from ui.view_models.strategic.character_vm import CharacterViewModel
from ui.view_models.strategic.weapon_vm import WeaponViewModel
from ui.view_models.strategic.artifact_vm import ArtifactPieceViewModel

@ft.observable
@dataclass
class ActiveCharacterProxy:
    """
    活跃角色代理 VM。
    用于详情面板的稳定绑定。切换角色时，面板绑定的实例不变，仅内部引用切换。
    """
    _target: CharacterViewModel | None = None

    def notify_update(self):
        """显式触发变更通知，解决静态检查报错"""
        cast(Any, self).notify()

    def bind_to(self, vm: CharacterViewModel):
        """重绑定目标 VM"""
        self._target = vm
        self.notify_update()

    @property
    def target(self) -> CharacterViewModel | None:
        return self._target

    @property
    def is_active(self) -> bool:
        return self._target is not None and not self._target.is_empty

    # --- 代理属性 (Getter/Setter) ---
    # 基础属性
    @property
    def name(self) -> str:
        return self._target.name if self._target else "未选中"

    @property
    def element(self) -> str:
        return self._target.element if self._target else "Neutral"
    
    @property
    def level(self) -> int:
        return self._target.level if self._target else 1

    def set_level(self, val: int):
        if self._target:
            self._target.set_level(val)
            self.notify_update()

    @property
    def constellation(self) -> int:
        return self._target.constellation if self._target else 0

    def set_constellation(self, val: int):
        if self._target:
            self._target.set_constellation(val)
            self.notify_update()

    # 天赋
    @property
    def talent_na(self) -> int:
        return self._target.talent_na if self._target else 1

    def set_talent_na(self, val: int):
        if self._target:
            self._target.set_talent_na(val)
            self.notify_update()

    @property
    def talent_e(self) -> int:
        return self._target.talent_e if self._target else 1

    def set_talent_e(self, val: int):
        if self._target:
            self._target.set_talent_e(val)
            self.notify_update()

    @property
    def talent_q(self) -> int:
        return self._target.talent_q if self._target else 1

    def set_talent_q(self, val: int):
        if self._target:
            self._target.set_talent_q(val)
            self.notify_update()

    # 子 VM 代理
    @property
    def weapon(self) -> WeaponViewModel | None:
        return self._target.weapon if self._target else None

    @property
    def artifacts(self) -> dict[str, ArtifactPieceViewModel]:
        return self._target.artifacts if self._target else {}
