from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class DataRepository(ABC):
    """
    数据仓库接口，定义了获取角色、武器和技能元数据的标准方法。
    """
    @abstractmethod
    def get_character_data(self, character_id: int) -> Dict[str, Any]:
        """获取角色基础统计数据 (role_stats)"""
        pass

    @abstractmethod
    def get_weapon_data(self, weapon_name: str) -> Dict[str, Any]:
        """获取武器基础属性"""
        pass

    @abstractmethod
    def query(self, sql: str) -> List[Any]:
        """执行通用查询 (用于兼容旧逻辑)"""
        pass

class MySQLDataRepository(DataRepository):
    """
    MySQL 数据仓库实现，包装现有的 DataRequest 逻辑。
    """
    def __init__(self):
        from DataRequest import DR
        self.dr = DR

    def get_character_data(self, character_id: int) -> Dict[str, Any]:
        sql = f"SELECT * FROM `role_stats` WHERE role_id = {character_id}"
        result = self.dr.read_data(sql)
        if not result:
            raise ValueError(f"Character ID {character_id} not found in database.")
        return result[0]

    def get_weapon_data(self, weapon_name: str) -> Dict[str, Any]:
        # 假设武器数据也在 MySQL 中，具体 SQL 需根据实际表结构调整
        # 这里先提供通用查询
        sql = f"SELECT * FROM `weapon_stats` WHERE name = '{weapon_name}'"
        result = self.dr.read_data(sql)
        return result[0] if result else {}

    def query(self, sql: str) -> List[Any]:
        return self.dr.read_data(sql)

class MockDataRepository(DataRepository):
    """
    用于单元测试的 Mock 仓库。
    """
    def __init__(self, char_map=None, weapon_map=None):
        self.char_map = char_map or {}
        self.weapon_map = weapon_map or {}

    def get_character_data(self, character_id: int) -> Dict[str, Any]:
        return self.char_map.get(character_id, {})

    def get_weapon_data(self, weapon_name: str) -> Dict[str, Any]:
        return self.weapon_map.get(weapon_name, {})

    def query(self, sql: str) -> List[Any]:
        return []
