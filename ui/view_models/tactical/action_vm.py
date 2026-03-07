import flet as ft
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from ui.view_models.base_vm import BaseViewModel
from core.data_models.action_data_model import ActionDataModel

@ft.observable
@dataclass
class ActionViewModel(BaseViewModel[ActionDataModel]):
    """
    单个动作单元的视图模型。
    """
    @property
    def uid(self) -> str: return self.model.uid
    @property
    def action_key(self) -> str: return self.model.action_key
    @property
    def char_id(self) -> str: return self.model.char_id

    @property
    def params(self) -> Dict[str, Any]:
        return self.model.params

    def set_param(self, key: str, value: Any):
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
