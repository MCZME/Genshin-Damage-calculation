from __future__ import annotations
from typing import Any, cast
import time
from core.data_models.team_data_model import BaseDataModel

class ActionDataModel(BaseDataModel):
    """
    单个动作配置模型。
    替代原 ActionUnit 的底层数据部分。
    """
    def __init__(self, data: dict[str, Any]):
        super().__init__(data)
        # 确保基础 UID 存在 (用于 UI 追踪)
        if "uid" not in self._data:
            self._data["uid"] = f"{self.action_key}_{time.time_ns()}"

    @property
    def uid(self) -> str:
        # [FIX] 确保返回 str 而非 Any | None
        return str(self._data.get("uid", ""))

    @property
    def character_name(self) -> str:
        return str(self._data.get("character_name", "unknown"))

    @character_name.setter
    def character_name(self, value: str):
        self._data["character_name"] = value

    @property
    def action_key(self) -> str:
        return str(self._data.get("action_key", "Wait"))

    @action_key.setter
    def action_key(self, value: str):
        self._data["action_key"] = value

    @property
    def params(self) -> dict[str, Any]:
        """动态参数字典"""
        if "params" not in self._data:
            self._data["params"] = {}
        return cast(dict[str, Any], self._data["params"])

    def set_param(self, key: str, value: Any):
        self.params[key] = value

    def to_simulator_format(self) -> dict[str, Any]:
        """转换为仿真引擎期望的格式"""
        return {
            "character_name": self.character_name,
            "action_key": self.action_key,
            "params": self.params
        }

    @staticmethod
    def create(character_name: str, action_key: str, params: dict | None = None) -> ActionDataModel:
        return ActionDataModel({
            "character_name": character_name,
            "action_key": action_key,
            "params": params if params is not None else {}
        })
