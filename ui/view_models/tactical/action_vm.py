from __future__ import annotations
import flet as ft
from dataclasses import dataclass
from typing import Any
from ui.view_models.base_vm import BaseViewModel
from core.data_models.action_data_model import ActionDataModel


@ft.observable
@dataclass
class ActionViewModel(BaseViewModel[ActionDataModel]):
    """
    单个动作单元的视图模型。
    """
    @property
    def uid(self) -> str:
        if self.model is None:
            return ""
        return self.model.uid

    @property
    def action_key(self) -> str:
        if self.model is None:
            return ""
        return self.model.action_key

    @property
    def char_id(self) -> str:
        """代理到 character_name，保持属性名兼容"""
        if self.model is None:
            return ""
        return self.model.character_name

    @property
    def params(self) -> dict[str, Any]:
        if self.model is None:
            return {}
        return self.model.params

    def set_param(self, key: str, value: Any):
        if self.model is None:
            return
        self.model.set_param(key, value)
        self.notify_update()

    def get_display_label(self) -> str:
        """获取映射后的中文标签 (待与 MetadataService 整合)"""
        mapping = {
            "normal_attack": "普攻",
            "elemental_skill": "战技",
            "elemental_burst": "爆发",
            "charged_attack": "重击",
            "dash": "冲刺",
            "skip": "等待"
        }
        return mapping.get(self.action_key, self.action_key)
