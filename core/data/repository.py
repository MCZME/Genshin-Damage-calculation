from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
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

    def get_character_base_stats(self, character_id: int, level: int) -> Dict[str, Any]:
        idx = level_to_idx(level)
        col = self.level_cols[idx]
        
        # 1. 获取基础信息
        char_info = self.db.execute_query(f"SELECT Name, Element, type FROM `character` WHERE ID = {character_id}")
        if not char_info:
            raise ValueError(f"Character ID {character_id} not found.")
        name, element, ctype = char_info[0]

        # 2. 获取三围属性
        hp = self.db.execute_query(f"SELECT `{col}` FROM `basehp` WHERE ID = {character_id}")[0][0]
        atk = self.db.execute_query(f"SELECT `{col}` FROM `baseatk` WHERE ID = {character_id}")[0][0]
        df = self.db.execute_query(f"SELECT `{col}` FROM `basedef` WHERE ID = {character_id}")[0][0]

        # 3. 获取突破属性
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

    def query(self, sql: str) -> List[Any]:
        return []
