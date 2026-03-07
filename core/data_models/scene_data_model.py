from typing import Dict, Any, List, Optional
from core.data_models.team_data_model import BaseDataModel

class TargetDataModel(BaseDataModel):
    """
    单个怪物目标的数据模型。
    聚合了怪物属性与空间坐标。
    """
    def __init__(self, data: Dict[str, Any], spatial_ref: Dict[str, Dict[str, float]]):
        super().__init__(data)
        self._spatial_ref = spatial_ref # 引用 StrategicState.spatial_data['target_positions']

    @property
    def id(self) -> str:
        return self._data.get("id", "")

    @property
    def name(self) -> str:
        return self._data.get("name", "Unknown Target")

    @name.setter
    def name(self, value: str):
        self._data["name"] = value

    @property
    def level(self) -> int:
        try:
            return int(self._data.get("level", 90))
        except (ValueError, TypeError):
            return 90

    @level.setter
    def level(self, value: int):
        self._data["level"] = str(value)

    @property
    def resists(self) -> Dict[str, float]:
        """抗性字典 (int/str -> float)"""
        raw = self._data.get("resists", {})
        return {k: float(v) for k, v in raw.items()}

    def set_resistance(self, element: str, value: float):
        if "resists" not in self._data:
            self._data["resists"] = {}
        self._data["resists"][element] = str(value)

    # --- 空间坐标代理 ---
    @property
    def x(self) -> float:
        return self._spatial_ref.get(self.id, {}).get("x", 0.0)

    @x.setter
    def x(self, value: float):
        if self.id not in self._spatial_ref:
            self._spatial_ref[self.id] = {"x": 0.0, "z": 5.0}
        self._spatial_ref[self.id]["x"] = float(value)

    @property
    def z(self) -> float:
        return self._spatial_ref.get(self.id, {}).get("z", 5.0)

    @z.setter
    def z(self, value: float):
        if self.id not in self._spatial_ref:
            self._spatial_ref[self.id] = {"x": 0.0, "z": 5.0}
        self._spatial_ref[self.id]["z"] = float(value)

    def to_simulator_format(self) -> Dict[str, Any]:
        """转换为仿真引擎格式"""
        return {
            "id": self.id,
            "name": self.name,
            "level": self.level,
            "position": {"x": self.x, "z": self.z},
            "resists": self.resists
        }

    @staticmethod
    def create_default(target_id: str, name: str = "遗迹守卫") -> Dict[str, Any]:
        """创建默认的怪物字典数据结构"""
        return {
            "id": target_id,
            "name": name,
            "level": "90",
            "resists": {
                "火": "10", "水": "10", "草": "10", "雷": "10", 
                "风": "10", "冰": "10", "岩": "10", "物理": "10"
            }
        }

class SceneDataModel(BaseDataModel):
    """
    场景全量数据模型。
    管理多目标列表。
    """
    def __init__(self, data: Dict[str, Any], spatial_data: Dict[str, Any]):
        super().__init__(data)
        self._spatial_data = spatial_data

    @property
    def targets(self) -> List[TargetDataModel]:
        """获取包装后的目标列表"""
        raw_targets = self._data.get("targets", [])
        return [TargetDataModel(t, self._spatial_data["target_positions"]) for t in raw_targets]

    @property
    def weather(self) -> str:
        return self._data.get("weather", "Clear")

    @property
    def field_type(self) -> str:
        return self._data.get("field", "Neutral")
