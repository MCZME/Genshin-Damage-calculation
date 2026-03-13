from typing import Any

# 槽位名映射：中文/大写英文 -> 小写英文
_SLOT_NAME_MAP: dict[str, str] = {
    "生之花": "flower", "死之羽": "plume", "时之沙": "sands",
    "空之杯": "goblet", "理之冠": "circlet",
    "Flower": "flower", "Plume": "plume", "Sands": "sands",
    "Goblet": "goblet", "Circlet": "circlet",
    "flower": "flower", "plume": "plume", "sands": "sands",
    "goblet": "goblet", "circlet": "circlet",
}

# 槽位名反向映射：小写英文 -> 大写英文
_SLOT_NAME_REVERSE: dict[str, str] = {
    "flower": "Flower", "plume": "Plume", "sands": "Sands",
    "goblet": "Goblet", "circlet": "Circlet",
}


class BaseDataModel:
    """
    配置模型基类：提供对原始字典的代理访问。
    """
    def __init__(self, data: dict[str, Any]):
        self._data = data

    @property
    def raw_data(self) -> dict[str, Any]:
        """暴露原始字典供序列化/持久化使用"""
        return self._data


class ArtifactDataModel(BaseDataModel):
    """
    单个圣遗物槽位的数据模型。
    统一使用仿真格式: { "set_name": str, "main_stat": dict[str, float], "sub_stats": dict[str, float] }
    同时提供 UI 便捷访问接口。
    """
    @property
    def set_name(self) -> str:
        return self._data.get("set_name", self._data.get("name", ""))

    @set_name.setter
    def set_name(self, value: str):
        self._data["set_name"] = value
        # 兼容旧字段
        if "name" in self._data:
            del self._data["name"]

    @property
    def main_stat(self) -> dict[str, float]:
        """主词条字典，如 {"生命值": 4780.0}"""
        # 优先使用新格式
        main = self._data.get("main_stat")
        if isinstance(main, dict):
            return main

        # 兼容旧格式: "main" + "main_val"
        old_main = self._data.get("main", "")
        old_val = self._data.get("main_val", 0)
        if old_main:
            try:
                val = float(old_val)
            except (ValueError, TypeError):
                val = 0.0
            return {old_main: val}
        return {}

    @main_stat.setter
    def main_stat(self, value: dict[str, float]):
        self._data["main_stat"] = value
        # 清理旧字段
        for old_key in ["main", "main_val", "value"]:
            if old_key in self._data:
                del self._data[old_key]

    @property
    def main_stat_name(self) -> str:
        """UI 便捷访问：主词条名称"""
        main = self.main_stat
        return next(iter(main.keys()), "") if main else ""

    @property
    def main_stat_value(self) -> float:
        """UI 便捷访问：主词条数值"""
        main = self.main_stat
        return next(iter(main.values()), 0.0) if main else 0.0

    @property
    def sub_stats(self) -> dict[str, float]:
        """副词条字典，如 {"暴击率": 10.5, "暴击伤害": 20.0}"""
        # 优先使用新格式
        sub = self._data.get("sub_stats")
        if isinstance(sub, dict):
            return sub

        # 兼容旧格式: "subs" 列表
        old_subs = self._data.get("subs", [])
        if isinstance(old_subs, list):
            normalized: dict[str, float] = {}
            for s in old_subs:
                if isinstance(s, dict):
                    key = s.get("key", "")
                    val = s.get("value", 0)
                    if key:
                        try:
                            normalized[key] = float(val)
                        except (ValueError, TypeError):
                            normalized[key] = 0.0
                elif isinstance(s, list) and len(s) >= 2:
                    try:
                        normalized[s[0]] = float(s[1])
                    except (ValueError, TypeError):
                        normalized[s[0]] = 0.0
            return normalized
        return {}

    @sub_stats.setter
    def sub_stats(self, value: dict[str, float]):
        self._data["sub_stats"] = value
        # 清理旧字段
        if "subs" in self._data:
            del self._data["subs"]

    @property
    def sub_stats_list(self) -> list[list[str]]:
        """UI 兼容：副词条列表格式 [["暴击率", "10.5"], ...]"""
        return [[k, str(v)] for k, v in self.sub_stats.items()]

    def set_sub_stat(self, key: str, value: float):
        """设置单个副词条"""
        if "sub_stats" not in self._data:
            self._data["sub_stats"] = {}
        self._data["sub_stats"][key] = value
        # 清理旧字段
        if "subs" in self._data:
            del self._data["subs"]

    def set_sub_stat_by_index(self, index: int, key: str, value: str):
        """UI 兼容：按索引设置副词条"""
        sub_stats = self.sub_stats
        keys = list(sub_stats.keys())

        if 0 <= index < len(keys):
            # 更新现有词条
            old_key = keys[index]
            del sub_stats[old_key]
            # 保持顺序
            new_keys = keys[:index] + [key] + keys[index + 1:]
            new_stats: dict[str, float] = {}
            for k in new_keys:
                if k == key:
                    try:
                        new_stats[k] = float(value)
                    except (ValueError, TypeError):
                        new_stats[k] = 0.0
                else:
                    new_stats[k] = sub_stats.get(k, 0.0)
            self.sub_stats = new_stats
        elif index == len(keys):
            # 添加新词条
            try:
                sub_stats[key] = float(value)
            except (ValueError, TypeError):
                sub_stats[key] = 0.0
            self.sub_stats = sub_stats

def _normalize_artifact(item: dict) -> dict:
    """将各种格式统一为仿真格式"""
    # 1. 槽位名统一为小写英文
    slot_raw = item.get("slot", "")
    slot = _SLOT_NAME_MAP.get(slot_raw, slot_raw.lower())

    # 2. 套装名
    set_name = item.get("set_name", item.get("name", ""))

    # 3. 主词条 -> Dict 格式
    main_stat = item.get("main_stat", {})
    if isinstance(main_stat, str):
        # 字符串格式 -> 使用 value/main_val 字段
        value = item.get("value", item.get("main_val", 0))
        try:
            main_stat = {main_stat: float(value)} if main_stat else {}
        except (ValueError, TypeError):
            main_stat = {}
    elif isinstance(main_stat, dict):
        pass  # 已经是正确格式

    # 4. 副词条 -> Dict 格式
    sub_stats = item.get("sub_stats", {})
    if isinstance(sub_stats, list):
        normalized = {}
        for s in sub_stats:
            if isinstance(s, dict):
                key = s.get("key", "")
                val = s.get("value", 0)
                if key:
                    try:
                        normalized[key] = float(val)
                    except (ValueError, TypeError):
                        normalized[key] = 0.0
            elif isinstance(s, list) and len(s) >= 2:
                try:
                    normalized[s[0]] = float(s[1])
                except (ValueError, TypeError):
                    normalized[s[0]] = 0.0
        sub_stats = normalized

    return {
        "slot": slot,
        "set_name": set_name,
        "main_stat": main_stat,
        "sub_stats": sub_stats,
    }


class ArtifactsDataModel(BaseDataModel):
    """
    圣遗物集合模型 (按槽位索引)。
    对应结构: { "Flower": {...}, "Plume": {...}, ... }
    内部使用仿真格式存储。
    """
    def get_slot(self, slot_name: str) -> ArtifactDataModel:
        """获取或初始化指定槽位的数据模型"""
        if slot_name not in self._data:
            self._data[slot_name] = {
                "set_name": "", "main_stat": {}, "sub_stats": {}
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

    def to_list(self) -> list[dict[str, Any]]:
        """导出为仿真引擎期望的列表格式"""
        res: list[dict[str, Any]] = []
        for slot in ["flower", "plume", "sands", "goblet", "circlet"]:
            slot_key = _SLOT_NAME_REVERSE.get(slot, slot.capitalize())
            data = self.get_slot(slot_key)
            if data.set_name and data.main_stat:
                res.append({
                    "slot": slot,
                    "set_name": data.set_name,
                    "main_stat": data.main_stat,
                    "sub_stats": data.sub_stats,
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
    def id(self) -> str | None:
        return self._data.get("id")

    @id.setter
    def id(self, value: str | None):
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
    def talent_levels(self) -> dict[str, int]:
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
            # 将列表转换为按槽位索引的字典，并统一为仿真格式
            normalized: dict[str, dict[str, Any]] = {}
            for item in raw_artifacts:
                artifact = _normalize_artifact(item)
                slot = artifact.pop("slot", "")
                slot_key = _SLOT_NAME_REVERSE.get(slot, slot.capitalize())
                if slot_key:
                    normalized[slot_key] = artifact
            self._data["artifacts"] = normalized
        elif raw_artifacts is None:
            self._data["artifacts"] = {}

        return ArtifactsDataModel(self._data["artifacts"])

    def to_simulator_format(self) -> dict[str, Any]:
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
    def create_empty() -> "CharacterDataModel":
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
                "Flower": {"set_name": "", "main_stat": {"生命值": 0.0}, "sub_stats": {}},
                "Plume": {"set_name": "", "main_stat": {"攻击力": 0.0}, "sub_stats": {}},
                "Sands": {"set_name": "", "main_stat": {"攻击力%": 0.0}, "sub_stats": {}},
                "Goblet": {"set_name": "", "main_stat": {"攻击力%": 0.0}, "sub_stats": {}},
                "Circlet": {"set_name": "", "main_stat": {"暴击率": 0.0}, "sub_stats": {}},
            }
        })
