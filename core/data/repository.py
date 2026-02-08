from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from core.tool import level as level_to_idx, attributeId as attr_id_to_name
from core.data.database import db_manager

class DataRepository(ABC):
    """
    数据仓库接口，定义了获取角色、武器和技能元数据的标准方法。
    """
    @abstractmethod
    def get_character_base_stats(self, character_id: int, level: int) -> Dict[str, Any]:
        """获取角色在特定等级的基础属性"""
        pass

    @abstractmethod
    def get_weapon_base_stats(self, weapon_name: str, level: int) -> Dict[str, Any]:
        """获取武器在特定等级的基础属性"""
        pass

    @abstractmethod
    def get_all_characters(self) -> List[Dict[str, Any]]:
        """获取所有可用角色的简要信息 (ID, Name, Element, Type)"""
        pass

    @abstractmethod
    def get_weapons_by_type(self, weapon_type: str) -> List[str]:
        """获取特定类型的所有武器名称"""
        pass

    @abstractmethod
    def get_all_artifact_sets(self) -> List[str]:
        """获取所有圣遗物套装名称"""
        pass

    @abstractmethod
    def query(self, sql: str, params: Optional[tuple] = None) -> List[Any]:
        """执行通用查询"""
        pass

class MySQLDataRepository(DataRepository):
    """
    MySQL 数据仓库实现，深度整合项目数据库表结构。
    """
    def __init__(self):
        self.db = db_manager
        self.level_cols = ['1', '20', '40', '50', '60', '70', '80', '90']

    def get_all_characters(self) -> List[Dict[str, Any]]:
        """获取所有角色的 ID, Name, Element, Type"""
        rows = self.db.execute_query("SELECT ID, Name, Element, Type FROM `character`")
        return [
            {"id": row[0], "name": row[1], "element": row[2], "type": row[3]}
            for row in rows
        ]

    def get_weapons_by_type(self, weapon_type: str) -> List[str]:
        """获取特定类型的所有武器名称"""
        rows = self.db.execute_query(f"SELECT Name FROM `weapon` WHERE Type = '{weapon_type}'")
        return [row[0] for row in rows]

    def get_all_artifact_sets(self) -> List[str]:
        """从数据库获取所有圣遗物套装名称"""
        try:
            rows = self.db.execute_query("SELECT Name FROM `artifact` ORDER BY Name ASC")
            return [row[0] for row in rows]
        except Exception:
            # 如果表不存在，返回空列表或 Mock 数据
            return ["炽烈的炎之魔女", "沉沦之心", "翠绿之影", "深林的记忆", "绝缘之旗印", "角斗士的终幕礼"]

    def get_character_base_stats(self, character_id: int, level: int) -> Dict[str, Any]:
        idx = level_to_idx(level)
        col = self.level_cols[idx]
        
        char_info = self.db.execute_query(f"SELECT Name, Element, type FROM `character` WHERE ID = {character_id}")
        if not char_info:
            raise ValueError(f"Character ID {character_id} not found.")
        name, element, ctype = char_info[0]

        hp = self.db.execute_query(f"SELECT `{col}` FROM `basehp` WHERE ID = {character_id}")[0][0]
        atk = self.db.execute_query(f"SELECT `{col}` FROM `baseatk` WHERE ID = {character_id}")[0][0]
        df = self.db.execute_query(f"SELECT `{col}` FROM `basedef` WHERE ID = {character_id}")[0][0]

        breakthrough = self.db.execute_query(f"SELECT `{col}`, AttributeId FROM `breakthrough_attribute` WHERE ID = {character_id}")
        bt_val, bt_id = breakthrough[0]
        bt_name = attr_id_to_name(bt_id)

        return {
            "name": name,
            "element": element,
            "type": ctype,
            "base_hp": float(hp),
            "base_atk": float(atk),
            "base_def": float(df),
            "breakthrough_attribute": bt_name,
            "breakthrough_value": float(bt_val)
        }

    def get_weapon_base_stats(self, weapon_name: str, level: int) -> Dict[str, Any]:
        idx = level_to_idx(level)
        col = self.level_cols[idx]

        w_info = self.db.execute_query(f"SELECT ID, type, Rarity FROM `weapon` WHERE Name = '{weapon_name}'")
        if not w_info:
            raise ValueError(f"Weapon {weapon_name} not found.")
        wid, wtype, rarity = w_info[0]

        atk = self.db.execute_query(f"SELECT `{col}` FROM `w_atk` WHERE ID = {wid}")[0][0]
        sub_info = self.db.execute_query(f"SELECT `{col}`, AttributeId FROM `w_secondary_attribute` WHERE ID = {wid}")
        
        stats = {
            "name": weapon_name,
            "type": wtype,
            "rarity": rarity,
            "base_atk": float(atk),
            "secondary_attribute": None,
            "secondary_value": 0.0
        }

        if sub_info:
            val, aid = sub_info[0]
            stats["secondary_attribute"] = attr_id_to_name(aid)
            stats["secondary_value"] = float(val)

        return stats

    def query(self, sql: str, params: Optional[tuple] = None) -> List[Any]:
        return self.db.execute_query(sql, params)

class MockDataRepository(DataRepository):
    """用于单元测试的 Mock 仓库"""
    def __init__(self, char_data=None, weapon_data=None):
        self.char_data = char_data or {}
        self.weapon_data = weapon_data or {}

    def get_character_base_stats(self, character_id: int, level: int) -> Dict[str, Any]:
        return self.char_data.get(character_id, {})

    def get_weapon_base_stats(self, weapon_name: str, level: int) -> Dict[str, Any]:
        return self.weapon_data.get(weapon_name, {})

    def get_all_characters(self) -> List[Dict[str, Any]]:
        return []

    def get_weapons_by_type(self, weapon_type: str) -> List[str]:
        return []

    def get_all_artifact_sets(self) -> List[str]:
        return []

    def query(self, sql: str) -> List[Any]:
        return []
