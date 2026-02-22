import flet as ft

import time

class ActionUnit:
    """
    单个动作单元的模型。
    """
    def __init__(self, char_id: str, action_type: str, frames: int = 60, cancel_type: str = "None"):
        self.uid = f"{action_type}_{time.time_ns()}" # 唯一标识，用于拖拽排序
        self.char_id = char_id
        self.action_type = action_type # N, E, Q, C, Dash, Jump, Switch, Wait
        self.frames = frames
        self.cancel_type = cancel_type # None, Dash, Jump
        self.params = {} # 用于存储动态参数，例如 {"mode": "Press"}

class TacticalState:
    """
    战术视图的状态管理器。
    """
    def __init__(self):
        self.sequence = [] # List[ActionUnit]
        self.selected_index = -1
        
        # 初始动作模拟
        self.add_action(ActionUnit("hu_tao", "E", 45))
        self.add_action(ActionUnit("hu_tao", "N", 12))
        self.add_action(ActionUnit("hu_tao", "C", 30, "Dash"))

    @property
    def selected_action(self) -> ActionUnit:
        if 0 <= self.selected_index < len(self.sequence):
            return self.sequence[self.selected_index]
        return None

    def add_action(self, action: ActionUnit):
        self.sequence.append(action)

    def remove_action(self, index: int):
        if 0 <= index < len(self.sequence):
            self.sequence.pop(index)

    def move_action(self, old_index: int, new_index: int):
        if old_index == new_index: return
        item = self.sequence.pop(old_index)
        self.sequence.insert(new_index, item)
