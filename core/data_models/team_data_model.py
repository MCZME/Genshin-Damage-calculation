from typing import Dict, Any, List, Optional, Union

class BaseDataModel:
    """
    配置模型基类：提供对原始字典的代理访问。
    """
    def __init__(self, data: Dict[str, Any]):
        self._data = data

    @property
    def raw_data(self) -> Dict[str, Any]:
        """暴露原始字典供序列化/持久化使用"""
        return self._data

class ArtifactDataModel(BaseDataModel):
    """
    单个圣遗物槽位的数据模型。
    对应结构: { "name": "Set Name", "main": "ATK", "main_val": "100", "subs": [...] }
    """
    @property
    def set_name(self) -> str:
        return self._data.get("name", "")

    @set_name.setter
    def set_name(self, value: str):
        self._data["name"] = value

    @property
    def main_stat(self) -> str:
        return self._data.get("main", "")

    @main_stat.setter
    def main_stat(self, value: str):
        self._data["main"] = value

    @property
    def main_val(self) -> float:
        try:
            return float(self._data.get("main_val", 0))
        except (ValueError, TypeError):
            return 0.0

    @main_val.setter
    def main_val(self, value: Union[float, str]):
        self._data["main_val"] = str(value)

    @property
    def sub_stats(self) -> List[List[str]]:
        """副词条列表: [["暴击率%", "3.9"], ...]"""
        return self._data.get("subs", [])

    def set_sub_stat(self, index: int, key: str, value: str):
        """设置指定索引的副词条"""
        if "subs" not in self._data:
            self._data["subs"] = []
        
        while len(self._data["subs"]) <= index:
            self._data["subs"].append(["", "0"])
            
        self._data["subs"][index] = [key, value]

class ArtifactsDataModel(BaseDataModel):
    """
    圣遗物集合模型 (按槽位索引)。
    对应结构: { "Flower": {...}, "Plume": {...}, ... }
    """
    def get_slot(self, slot_name: str) -> ArtifactDataModel:
        """获取或初始化指定槽位的数据模型"""
        if slot_name not in self._data:
            self._data[slot_name] = {
                "name": "", "main": "", "main_val": "0", "subs": []
            }
        return ArtifactDataModel(self._data[slot_name])

    @property
    def flower(self) -> ArtifactDataModel: return self.get_slot("Flower")
    @property
    def plume(self) -> ArtifactDataModel: return self.get_slot("Plume")
    @property
    def sands(self) -> ArtifactDataModel: return self.get_slot("Sands")
    @property
    def goblet(self) -> ArtifactDataModel: return self.get_slot("Goblet")
    @property
    def circlet(self) -> ArtifactDataModel: return self.get_slot("Circlet")

    def to_list(self) -> List[Dict[str, Any]]:
        """转换为仿真引擎期望的列表格式"""
        res = []
        for slot in ["Flower", "Plume", "Sands", "Goblet", "Circlet"]:
            data = self.get_slot(slot)
            if data.set_name:
                res.append({
                    "slot": slot.lower(),
                    "set_name": data.set_name,
                    "main_stat": data.main_stat,
                    "value": data.main_val,
                    "sub_stats": [{"key": s[0], "value": float(s[1] or 0)} for s in data.sub_stats if len(s) >= 2 and s[0]]
                })
        return res

class WeaponDataModel(BaseDataModel):
    """
    武器配置模型。
    对应结构: { "id": "WeaponName", "level": "90", "refinement": "1" }
    """
    @property
    def name(self) -> str:
        return self._data.get("id", "")

    @name.setter
    def name(self, value: str):
        self._data["id"] = value

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
    def refinement(self) -> int:
        try:
            return int(self._data.get("refinement", 1))
        except (ValueError, TypeError):
            return 1

    @refinement.setter
    def refinement(self, value: int):
        self._data["refinement"] = str(value)

class CharacterDataModel(BaseDataModel):
    """
    角色配置模型 (聚合根)。
    对应结构: { "id": "CharName", "level": "90", "talents": {...}, "weapon": {...}, "artifacts": {...} }
    """
    @property
    def id(self) -> Optional[str]:
        return self._data.get("id")

    @id.setter
    def id(self, value: Optional[str]):
        self._data["id"] = value

    @property
    def name(self) -> str:
        return self._data.get("name", "Empty Slot")

    @name.setter
    def name(self, value: str):
        self._data["name"] = value

    @property
    def element(self) -> str:
        return self._data.get("element", "Neutral")

    @element.setter
    def element(self, value: str):
        self._data["element"] = value

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
    def constellation(self) -> int:
        try:
            return int(self._data.get("constellation", 0))
        except (ValueError, TypeError):
            return 0

    @constellation.setter
    def constellation(self, value: int):
        self._data["constellation"] = str(value)

    @property
    def talent_levels(self) -> Dict[str, int]:
        """获取天赋等级字典"""
        raw = self._data.get("talents", {"na": "1", "e": "1", "q": "1"})
        return {k: int(v) for k, v in raw.items()}

    def set_talent(self, key: str, value: int):
        if "talents" not in self._data:
            self._data["talents"] = {"na": "1", "e": "1", "q": "1"}
        self._data["talents"][key] = str(value)

    @property
    def weapon(self) -> WeaponDataModel:
        if "weapon" not in self._data:
            self._data["weapon"] = {"id": None, "level": "90", "refinement": "1"}
        return WeaponDataModel(self._data["weapon"])

    @property
    def artifacts(self) -> ArtifactsDataModel:
        raw_artifacts = self._data.get("artifacts")

        # 核心修复：处理 artifacts 可能是列表或字典的情况
        if isinstance(raw_artifacts, list):
            # 将列表转换为按槽位索引的字典
            # 兼容格式: [{"slot": "flower", ...}, ...] -> {"Flower": {...}}
            normalized = {}
            for item in raw_artifacts:
                slot = item.get("slot", "").capitalize()
                if slot:
                    normalized[slot] = item
            self._data["artifacts"] = normalized
        elif raw_artifacts is None:
            self._data["artifacts"] = {}

        return ArtifactsDataModel(self._data["artifacts"])

    def to_simulator_format(self) -> Dict[str, Any]:
        """导出为仿真引擎期望的扁平化嵌套字典"""
        talents = self.talent_levels
        return {
            "character": {
                "id": self.id,
                "name": self.name,
                "element": self.element,
                "level": self.level,
                "constellation": self.constellation,
                "talents": [talents.get("na", 1), talents.get("e", 1), talents.get("q", 1)],
                "type": self._data.get("type", "Unknown")
            },
            "weapon": {
                "name": self.weapon.name if self.weapon.name else "未装备",
                "level": self.weapon.level,
                "refinement": self.weapon.refinement
            },
            "artifacts": self.artifacts.to_list(),
            "position": {"x": 0, "z": 0} # 默认值，由 Scene 覆盖
        }

    @staticmethod
    def create_empty() -> 'CharacterDataModel':
        """工厂方法：创建空的角色配置结构"""
        return CharacterDataModel({
            "id": None,
            "name": "Empty Slot",
            "element": "Neutral",
            "level": "90",
            "constellation": "0",
            "talents": {"na": "1", "e": "1", "q": "1"},
            "weapon": {"id": None, "level": "90", "refinement": "1"},
            "artifacts": {
                "Flower": {"name": "", "main": "生命值", "main_val": "0", "subs": []},
                "Plume": {"name": "", "main": "攻击力", "main_val": "0", "subs": []},
                "Sands": {"name": "", "main": "攻击力%", "main_val": "0", "subs": []},
                "Goblet": {"name": "", "main": "攻击力%", "main_val": "0", "subs": []},
                "Circlet": {"name": "", "main": "暴击率%", "main_val": "0", "subs": []},
            }
        })
