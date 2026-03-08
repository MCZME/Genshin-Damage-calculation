from __future__ import annotations
import flet as ft
from dataclasses import dataclass, field
from typing import Any, cast
from core.data_models.action_data_model import ActionDataModel
from ui.view_models.tactical.action_vm import ActionViewModel

@ft.observable
@dataclass
class TacticalPageViewModel:
    """
    战术页面视图模型。
    管理动作序列 VM 列表及当前选中的编辑项。
    """
    sequence_vms: list[ActionViewModel] = field(default_factory=list)
    selected_index: int = -1
    
    # 动作参数编辑器代理
    active_action_proxy: ActionViewModel | None = None

    def __post_init__(self):
        self.active_action_proxy = None # 初始不绑定

    def notify_update(self):
        """显式触发变更通知，解决静态检查报错"""
        # @ft.observable 注入了 notify() 方法，通过 cast(Any, self) 绕过静态检查
        cast(Any, self).notify()

    def load_sequence(self, sequence: list[ActionDataModel]):
        """从 DataModel 列表同步 VM 列表"""
        self.sequence_vms = [ActionViewModel(m) for m in sequence]
        self.selected_index = -1
        self.notify_update()

    def add_action(self, model: ActionDataModel):
        vm = ActionViewModel(model)
        self.sequence_vms.append(vm)
        self.select_action(len(self.sequence_vms) - 1)
        self.notify_update()

    def remove_action(self, index: int):
        if 0 <= index < len(self.sequence_vms):
            self.sequence_vms.pop(index)
            if self.selected_index == index:
                self.selected_index = -1
            elif self.selected_index > index:
                self.selected_index -= 1
            self.notify_update()

    def move_action(self, old_index: int, new_index: int):
        if 0 <= old_index < len(self.sequence_vms) and 0 <= new_index < len(self.sequence_vms):
            item = self.sequence_vms.pop(old_index)
            self.sequence_vms.insert(new_index, item)
            self.selected_index = new_index
            self.notify_update()

    def select_action(self, index: int):
        self.selected_index = index
        # 这里可以使用 Proxy 模式，但 Action 参数相对简单，直接传递 VM 引用给编辑器也可
        self.notify_update()

    def clear_sequence(self):
        self.sequence_vms.clear()
        self.selected_index = -1
        self.notify_update()
