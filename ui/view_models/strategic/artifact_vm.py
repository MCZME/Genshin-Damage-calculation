from __future__ import annotations
from typing import TYPE_CHECKING
import flet as ft
from dataclasses import dataclass
from ui.view_models.base_vm import BaseViewModel
from core.data_models.team_data_model import ArtifactDataModel
if TYPE_CHECKING:
    from ui.view_models.strategic.character_vm import CharacterViewModel

@ft.observable
@dataclass
class ArtifactPieceViewModel(BaseViewModel[ArtifactDataModel]):
    """
    单个圣遗物部位的视图模型。
    支持 model 为 None 的空槽位状态。
    """
    slot_name: str # Flower, Plume, etc.
    parent: CharacterViewModel | None = None # 引用父 VM，便于更新通知

    @property
    def set_name(self) -> str:
        return self.model.set_name if self.model else ""
    
    def notify_update(self) -> None:
        super().notify_update()
        # 级联通知父 VM 更新（如果存在）
        if self.parent:
            self.parent.notify_update()

    def set_set_name(self, value: str):
        if self.model:
            self.model.set_name = value
            self.notify_update()

    @property
    def main_stat(self) -> str:
        """主词条名称"""
        return self.model.main_stat_name if self.model else ""

    def set_main_stat(self, value: str):
        """设置主词条（名称和当前值）"""
        if self.model:
            current_val = self.model.main_stat_value
            self.model.main_stat = {value: current_val}
            self.notify_update()

    @property
    def main_val(self) -> str:
        """主词条数值"""
        if not self.model:
            return "0"
        return str(self.model.main_stat_value)

    def set_main_val(self, value: str):
        """设置主词条数值"""
        if self.model:
            current_name = self.model.main_stat_name
            if current_name:
                try:
                    self.model.main_stat = {current_name: float(value)}
                except (ValueError, TypeError):
                    self.model.main_stat = {current_name: 0.0}
            self.notify_update()

    @property
    def sub_stats(self) -> list[list[str]]:
        """暴露副词条列表供 UI 循环渲染"""
        return self.model.sub_stats_list if self.model else []

    def update_sub_stat_key(self, index: int, new_key: str):
        """仅更新副词条的属性名"""
        if self.model:
            sub_stats = self.model.sub_stats
            keys = list(sub_stats.keys())
            if 0 <= index < len(keys):
                old_key = keys[index]
                current_val = sub_stats[old_key]
                # 使用新的设置方法
                self.model.set_sub_stat_by_index(index, new_key, str(current_val))
                self.notify_update()

    def update_sub_stat_value(self, index: int, new_val: str):
        """仅更新副词条的数值"""
        if self.model:
            sub_stats = self.model.sub_stats
            keys = list(sub_stats.keys())
            if 0 <= index < len(keys):
                current_key = keys[index]
                self.model.set_sub_stat_by_index(index, current_key, new_val)
                self.notify_update()

    def set_sub_stat(self, index: int, key: str, value: str):
        """同时更新属性名和数值"""
        if self.model:
            self.model.set_sub_stat_by_index(index, key, value)
            self.notify_update()

    def add_sub_stat(self):
        """添加一个新的空副词条，上限 4 个"""
        if self.model:
            sub_stats = self.model.sub_stats
            if len(sub_stats) < 4:
                # 添加一个空词条
                self.model.set_sub_stat("", 0.0)
                self.notify_update()

    def remove_sub_stat(self, index: int):
        """移除指定索引的副词条"""
        if self.model:
            sub_stats = self.model.sub_stats
            keys = list(sub_stats.keys())
            if 0 <= index < len(keys):
                del sub_stats[keys[index]]
                self.model.sub_stats = sub_stats
                self.notify_update()
