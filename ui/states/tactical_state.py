from __future__ import annotations
import flet as ft
from typing import Any
from collections.abc import Callable
from core.data_models.action_data_model import ActionDataModel
from ui.view_models.tactical.tactical_page_vm import TacticalPageViewModel

@ft.observable
class TacticalState:
    """
    战术视图的状态管理器 (MVVM V5.0)。
    """
    def __init__(self):
        # 底层数据列表
        self.sequence_data: list[ActionDataModel] = [] 
        
        # 顶层页面 VM
        self.page_vm = TacticalPageViewModel()
        
        # 初始动作模拟 (保持原有逻辑)
        self.add_action(ActionDataModel.create("hu_tao", "elemental_skill"))
        self.add_action(ActionDataModel.create("hu_tao", "normal_attack"))

    @property
    def sequence(self) -> list[ActionDataModel]:
        """兼容性属性：返回 DataModel 列表"""
        return self.sequence_data

    def add_action(self, model: ActionDataModel):
        self.sequence_data.append(model)
        self.page_vm.add_action(model)

    def remove_action(self, index: int):
        if 0 <= index < len(self.sequence_data):
            self.sequence_data.pop(index)
            self.page_vm.remove_action(index)

    def move_action(self, old_index: int, new_index: int):
        if 0 <= old_index < len(self.sequence_data) and 0 <= new_index < len(self.sequence_data):
            item = self.sequence_data.pop(old_index)
            self.sequence_data.insert(new_index, item)
            self.page_vm.move_action(old_index, new_index)

    def clear_sequence(self):
        """清空所有动作数据与 VM"""
        self.sequence_data.clear()
        self.page_vm.clear_sequence()

    def load_from_dict(self, sequence_config: list[dict[str, Any]]):
        """配置重载"""
        self.sequence_data = [ActionDataModel(d) for d in sequence_config]
        self.page_vm.load_sequence(self.sequence_data)
