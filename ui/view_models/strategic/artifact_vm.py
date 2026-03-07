import flet as ft
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from ui.view_models.base_vm import BaseViewModel
from core.data_models.team_data_model import ArtifactDataModel

@ft.observable
@dataclass
class ArtifactPieceViewModel(BaseViewModel[ArtifactDataModel]):
    """
    单个圣遗物部位的视图模型。
    """
    slot_name: str # Flower, Plume, etc.

    @property
    def set_name(self) -> str:
        return self.model.set_name

    def set_set_name(self, value: str):
        self.model.set_name = value
        self.notify_update()

    @property
    def main_stat(self) -> str:
        return self.model.main_stat

    def set_main_stat(self, value: str):
        self.model.main_stat = value
        self.notify_update()

    @property
    def main_val(self) -> str:
        # UI 输入通常期望字符串，内部 DataModel 处理数值转换
        return str(self.model.raw_data.get("main_val", "0"))

    def set_main_val(self, value: str):
        self.model.main_val = value
        self.notify_update()

    @property
    def sub_stats(self) -> List[List[str]]:
        """暴露副词条列表供 UI 循环渲染"""
        return self.model.sub_stats

    def update_sub_stat_key(self, index: int, new_key: str):
        """仅更新副词条的属性名"""
        current_val = self.model.sub_stats[index][1]
        self.model.set_sub_stat(index, new_key, current_val)
        self.notify_update()

    def update_sub_stat_value(self, index: int, new_val: str):
        """仅更新副词条的数值"""
        current_key = self.model.sub_stats[index][0]
        self.model.set_sub_stat(index, current_key, new_val)
        self.notify_update()

    def set_sub_stat(self, index: int, key: str, value: str):
        """同时更新属性名和数值"""
        self.model.set_sub_stat(index, key, value)
        self.notify_update()

    def add_sub_stat(self):
        """添加一个新的空副词条，上限 4 个"""
        current_subs = self.model.sub_stats
        if len(current_subs) < 4:
            self.model.set_sub_stat(len(current_subs), "", "0")
            self.notify_update()

    def remove_sub_stat(self, index: int):
        """移除指定索引的副词条"""
        current_subs = self.model.sub_stats
        if 0 <= index < len(current_subs):
            current_subs.pop(index)
            self.notify_update()


