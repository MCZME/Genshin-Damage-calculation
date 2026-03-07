from typing import Dict, Any, List, Optional
import time
from core.data_models.team_data_model import BaseDataModel

class ActionDataModel(BaseDataModel):
    """
    单个动作配置模型。
    替代原 ActionUnit 的底层数据部分。
    """
    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)
        # 确保基础 UID 存在 (用于 UI 追踪)
        if "uid" not in self._data:
            self._data["uid"] = f"{self.action_key}_{time.time_ns()}"

    @property
    def uid(self) -> str:
        return self._data.get("uid")

    @property
    def char_id(self) -> str:
        return self._data.get("char_id", "unknown")

    @char_id.setter
    def char_id(self, value: str):
        self._data["char_id"] = value

    @property
    def action_key(self) -> str:
        return self._data.get("action_type", "Wait")

    @property
    def params(self) -> Dict[str, Any]:
        """动态参数字典"""
        if "params" not in self._data:
            self._data["params"] = {}
        return self._data["params"]

    def set_param(self, key: str, value: Any):
        self.params[key] = value

    def to_simulator_format(self, char_name: str) -> Dict[str, Any]:
        """转换为仿真引擎期望的格式"""
        return {
            "character_name": char_name,
            "action_key": self.action_key,
            "params": self.params
        }

    @staticmethod
    def create(char_id: str, action_type: str, params: Dict = None) -> 'ActionDataModel':
        return ActionDataModel({
            "char_id": char_id,
            "action_type": action_type,
            "params": params or {}
        })
