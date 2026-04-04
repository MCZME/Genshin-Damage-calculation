"""战略视图状态管理器。"""

from __future__ import annotations

import flet as ft
from typing import Any, cast

from core.data_models.team_data_model import CharacterDataModel
from ui.view_models.strategic.character_vm import CharacterViewModel
from ui.view_models.strategic.active_character_vm import ActiveCharacterProxy


@ft.observable
class StrategicState:
    """
    战略视图状态管理器 (MVVM V5.0)。

    负责维护 4 人编队的 DataModel 与 ViewModel 映射。
    场景相关状态已迁移至 SceneState。
    """

    def __init__(self) -> None:
        # 1. 成员数据 (DataModel 与 VM 树)
        self.team_data: list[dict[str, Any]] = [
            CharacterDataModel.create_empty().raw_data for _ in range(4)
        ]
        self.team_vms: list[CharacterViewModel] = [
            CharacterViewModel(CharacterDataModel(d)) for d in self.team_data
        ]

        # 2. 详情面板常驻代理
        self.active_character_proxy = ActiveCharacterProxy()
        self.active_character_proxy.bind_to(self.team_vms[0])

        # 3. 当前状态
        self.current_index: int = 0
        self.current_tab: str = "Character"

    def notify_update(self) -> None:
        """触发状态更新通知。"""
        cast(Any, self).notify()

    def rebind_all_vms(self) -> None:
        """配置重载后强制重建 VM 树。"""
        self.team_vms = [
            CharacterViewModel(CharacterDataModel(d)) for d in self.team_data
        ]
        self.active_character_proxy.bind_to(self.team_vms[self.current_index])
        self.notify_update()

    # === 成员管理 ===

    @property
    def current_member_vm(self) -> CharacterViewModel:
        """获取当前选中的成员 ViewModel。"""
        return self.team_vms[self.current_index]

    def select_member(self, index: int) -> None:
        """选中成员。"""
        self.current_index = index
        self.active_character_proxy.bind_to(self.team_vms[index])
        self.notify_update()

    def add_member(self, index: int, char_data: dict[str, Any]) -> None:
        """初始化并分配成员基础数据。"""
        model = CharacterDataModel.create_empty()
        model.id = char_data['id']
        model.name = char_data['name']
        model.element = char_data.get('element', 'Neutral')
        model.raw_data.update({
            "type": char_data.get('type', '单手剑'),
            "rarity": char_data.get('rarity', 5)
        })
        self.team_data[index] = model.raw_data
        self.team_vms[index] = CharacterViewModel(model)
        if self.current_index == index:
            self.active_character_proxy.bind_to(self.team_vms[index])
        self.notify_update()

    def remove_member(self, index: int) -> None:
        """清空成员数据。"""
        new_model = CharacterDataModel.create_empty()
        self.team_data[index] = new_model.raw_data
        self.team_vms[index] = CharacterViewModel(new_model)
        if self.current_index == index:
            self.active_character_proxy.bind_to(self.team_vms[index])
        self.notify_update()

    # === 兼容性属性 ===

    @property
    def current_member(self) -> dict[str, Any]:
        """兼容性属性：返回当前成员原始字典。"""
        return self.team_data[self.current_index]

    def to_config_dict(self) -> list[dict[str, Any]]:
        """导出为配置字典。"""
        return self.team_data
