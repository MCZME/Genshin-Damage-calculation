from __future__ import annotations
import flet as ft
from typing import Any
from collections.abc import Callable
from core.data_models.team_data_model import CharacterDataModel
from core.data_models.scene_data_model import TargetDataModel
from ui.view_models.strategic.character_vm import CharacterViewModel
from ui.view_models.strategic.active_character_vm import ActiveCharacterProxy
from ui.view_models.scene.target_vm import TargetViewModel

@ft.observable
class StrategicState:
    """
    战略视图的状态管理器 (MVVM V5.0)。
    负责维护 4 人编队的 DataModel 与 ViewModel 映射。
    """
    def __init__(self):
        # 1. 成员数据 (DataModel 与 VM 树)
        self.team_data: list[dict[str, Any]] = [CharacterDataModel.create_empty().raw_data for _ in range(4)]
        self.team_vms: list[CharacterViewModel] = [CharacterViewModel(CharacterDataModel(d)) for d in self.team_data]
        
        # 详情面板常驻代理
        self.active_character_proxy = ActiveCharacterProxy()
        self.active_character_proxy.bind_to(self.team_vms[0])
        
        self.current_index: int = 0
        self.current_tab: str = "Character"
        
        # 2. 目标实体列表
        self.targets_data: list[dict[str, Any]] = [TargetDataModel.create_default("target_0", "遗迹守卫")]
        self.selected_target_index: int = 0
        
        # 3. 战场空间
        self.spatial_data: dict[str, Any] = {
            "player_pos": {"x": 0.0, "z": 0.0},
            "target_positions": {
                "target_0": {"x": 0.0, "z": 5.0}
            }
        }
        
        # 初始化目标 VM
        self.target_vms: list[TargetViewModel] = [
            TargetViewModel(TargetDataModel(d, self.spatial_data["target_positions"])) 
            for d in self.targets_data
        ]
        
        # 4. 场景与环境
        self.scene_data: dict[str, Any] = {
            "weather": "Clear",
            "field": "Neutral",
            "manual_buffs": []
        }

    # --- 静态类型检查辅助 (由 @ft.observable 注入) ---
    def notify(self) -> None: ...
    def subscribe(self, handler: Callable[..., Any]) -> None: ...
    def unsubscribe(self, handler: Callable[..., Any]) -> None: ...

    def rebind_all_vms(self):
        """配置重载后强制重建 VM 树"""
        self.team_vms = [CharacterViewModel(CharacterDataModel(d)) for d in self.team_data]
        self.target_vms = [
            TargetViewModel(TargetDataModel(d, self.spatial_data["target_positions"])) 
            for d in self.targets_data
        ]
        self.active_character_proxy.bind_to(self.team_vms[self.current_index])
        # 核心修复：发送信号告知引用已变
        self.notify()

    def add_target(self, name: str = "遗迹守卫"):
        new_id = f"target_{len(self.targets_data)}"
        new_raw = TargetDataModel.create_default(new_id, name)
        self.targets_data.append(new_raw)
        self.spatial_data["target_positions"][new_id] = {"x": 0.0, "z": 5.0}
        
        new_vm = TargetViewModel(TargetDataModel(new_raw, self.spatial_data["target_positions"]))
        self.target_vms.append(new_vm)
        self.selected_target_index = len(self.target_vms) - 1
        self.notify()

    def remove_target(self, index: int):
        if len(self.target_vms) > 1:
            target_id = self.target_vms[index].id
            self.targets_data.pop(index)
            self.target_vms.pop(index)
            if target_id in self.spatial_data["target_positions"]:
                del self.spatial_data["target_positions"][target_id]
            self.selected_target_index = min(self.selected_target_index, len(self.target_vms) - 1)
            self.notify()

    @property
    def current_target_vm(self) -> TargetViewModel:
        return self.target_vms[self.selected_target_index]

    @property
    def current_member_vm(self) -> CharacterViewModel:
        return self.team_vms[self.current_index]

    def select_member(self, index: int):
        self.current_index = index
        self.active_character_proxy.bind_to(self.team_vms[index])
        self.notify()

    def add_member(self, index: int, char_data: dict[str, Any]):
        """初始化并分配成员基础数据"""
        model = CharacterDataModel.create_empty()
        model.id = char_data['id']
        model.name = char_data['name']
        model.element = char_data.get('element', 'Neutral')
        model.raw_data.update({
            "type": char_data.get('type', '单手剑'),
            "rarity": char_data.get('rarity', 5)
        })
        self.team_data[index] = model.raw_data
        # 重建该槽位的 VM
        self.team_vms[index] = CharacterViewModel(model)
        # 如果是当前槽位，更新代理
        if self.current_index == index:
            self.active_character_proxy.bind_to(self.team_vms[index])
        self.notify()

    def remove_member(self, index: int):
        """清空成员数据"""
        new_model = CharacterDataModel.create_empty()
        self.team_data[index] = new_model.raw_data
        self.team_vms[index] = CharacterViewModel(new_model)
        if self.current_index == index:
            self.active_character_proxy.bind_to(self.team_vms[index])
        self.notify()

    @property
    def current_member(self) -> dict[str, Any]:
        """兼容性属性：返回原始字典"""
        return self.team_data[self.current_index]

    @property
    def targets(self) -> list[dict[str, Any]]:
        """兼容性属性"""
        return self.targets_data

    @property
    def current_target(self) -> dict[str, Any]:
        """兼容性属性"""
        return self.targets_data[self.selected_target_index]

    def to_config_dict(self) -> list[dict[str, Any]]:
        return self.team_data
