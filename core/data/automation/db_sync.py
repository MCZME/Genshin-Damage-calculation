from typing import Any
from core.data.database import db_manager
from core.logger import get_emulation_logger


class DatabaseSync:
    """
    数据库同步器 (ID 适配版)。
    依赖数据库自增 ID，确保数据与本地资产库一致。
    """

    ATTR_NAME_TO_ID = {
        "暴击率": 1,
        "暴击伤害": 2,
        "生命值": 3,
        "防御力": 4,
        "攻击力": 5,
        "元素精通": 6,
        "元素充能效率": 7,
        "治疗加成": 8,
        "元素伤害加成": 9,
        "受治疗加成": 10,
        "生命值%": 11,
        "攻击力%": 12,
        "防御力%": 13,
        "物理伤害加成": 14,
        "火元素伤害加成": 15,
        "水元素伤害加成": 16,
        "冰元素伤害加成": 17,
        "雷元素伤害加成": 18,
        "风元素伤害加成": 19,
        "岩元素伤害加成": 20,
        "草元素伤害加成": 21,
    }

    def __init__(self) -> None:
        self.db = db_manager

    def sync_character(self, data: dict[str, Any]) -> int | None:
        """执行全量同步并返回数据库真实的 Character ID。"""
        char_name = data["metadata"]["name"]
        get_emulation_logger().log_info(
            f"开始同步数据库资产: {char_name}", sender="DBSync"
        )

        try:
            # 1. 确保表结构
            self._ensure_schema()

            # 2. 同步基础表 (不指定 ID，依赖 Name 进行更新)
            self._sync_base_info(data)

            # 3. 获取数据库中的真实 ID (如 75)
            real_id = self._get_real_id(char_name)
            if not real_id:
                raise ValueError(f"无法获取角色 {char_name} 的数据库 ID")

            # 4. 同步数值表 (使用真实 ID)
            self._sync_stats_table("basehp", real_id, data["base_stats"], "生命值")
            self._sync_stats_table("baseatk", real_id, data["base_stats"], "攻击力")
            self._sync_stats_table("basedef", real_id, data["base_stats"], "防御力")

            # 5. 同步突破加成
            self._sync_breakthrough(data, real_id)

            get_emulation_logger().log_info(
                f"数据库同步成功 (Real ID: {real_id})", sender="DBSync"
            )
            return real_id
        except Exception as e:
            get_emulation_logger().log_error(
                f"数据库同步失败: {str(e)}", sender="DBSync"
            )
            return None

    def sync_weapon(self, data: dict[str, Any]) -> int | None:
        """同步武器数据到数据库并返回真实 ID。"""
        weapon_name = data["metadata"]["name"]
        get_emulation_logger().log_info(
            f"开始同步武器数据: {weapon_name}", sender="DBSync"
        )

        try:
            # 1. 确保表结构
            self._ensure_weapon_schema()

            # 2. 同步基础信息
            self._sync_weapon_base_info(data)

            # 3. 获取数据库 ID
            real_id = self._get_weapon_id(weapon_name)
            if not real_id:
                raise ValueError(f"无法获取武器 {weapon_name} 的数据库 ID")

            # 4. 同步攻击力表
            self._sync_weapon_atk(real_id, data["base_atk"])

            # 5. 同步副属性表
            secondary = data.get("secondary_attribute", {})
            if secondary.get("name"):
                self._sync_weapon_secondary(real_id, secondary)

            get_emulation_logger().log_info(
                f"武器数据同步成功 (ID: {real_id})", sender="DBSync"
            )
            return real_id
        except Exception as e:
            get_emulation_logger().log_error(
                f"武器数据同步失败: {str(e)}", sender="DBSync"
            )
            return None

    def _ensure_weapon_schema(self) -> None:
        """确保武器相关表结构完整。"""
        pass

    def _sync_weapon_base_info(self, data: dict[str, Any]) -> None:
        """同步武器基础信息。"""
        m = data["metadata"]
        sql = """
            INSERT INTO `weapon` (Name, Type, Rarity)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
            Type = VALUES(Type),
            Rarity = VALUES(Rarity)
        """
        params = (m["name"], m["type"], m["rarity"])
        self.db.execute_non_query(sql, params)

    def _get_weapon_id(self, name: str) -> int | None:
        """获取武器的数据库 ID。"""
        sql = "SELECT ID FROM `weapon` WHERE Name = %s"
        result = self.db.execute_query(sql, (name,))
        return result[0][0] if result else None

    def _sync_weapon_atk(self, weapon_id: int, atk_data: dict[int, float]) -> None:
        """同步武器攻击力数据。"""
        levels = [1, 20, 40, 50, 60, 70, 80, 90]
        vals = [atk_data.get(lv, 0.0) for lv in levels]

        columns = ", ".join([f"`{lv}`" for lv in levels])
        placeholders = ", ".join(["%s"] * (len(levels) + 1))

        sql = f"REPLACE INTO `w_atk` (ID, {columns}) VALUES ({placeholders})"
        params = tuple([weapon_id] + vals)
        self.db.execute_non_query(sql, params)

    def _sync_weapon_secondary(
        self, weapon_id: int, secondary_data: dict[str, Any]
    ) -> None:
        """同步武器副属性数据。"""
        prop_name = secondary_data.get("name")
        values = secondary_data.get("values", {})
        attr_id = self.ATTR_NAME_TO_ID.get(prop_name, 0)

        levels = [1, 20, 40, 50, 60, 70, 80, 90]
        vals = [values.get(lv, 0.0) for lv in levels]

        columns = ", ".join([f"`{lv}`" for lv in levels])
        placeholders = ", ".join(["%s"] * (len(levels) + 2))

        sql = f"REPLACE INTO `w_secondary_attribute` (ID, {columns}, AttributeId) VALUES ({placeholders})"
        params = tuple([weapon_id] + vals + [attr_id])
        self.db.execute_non_query(sql, params)

    def _ensure_schema(self) -> None:
        tables = ["basehp", "baseatk", "basedef", "breakthrough_attribute"]
        for table in tables:
            for col in ["95", "100"]:
                check_sql = f"SHOW COLUMNS FROM `{table}` LIKE '{col}'"
                if not self.db.execute_query(check_sql):
                    alter_sql = (
                        f"ALTER TABLE `{table}` ADD COLUMN `{col}` DOUBLE DEFAULT 0"
                    )
                    self.db.execute_non_query(alter_sql)

    def _sync_base_info(self, data: dict[str, Any]) -> None:
        """同步基础信息，使用 INSERT ... ON DUPLICATE KEY UPDATE 以保留自增 ID。"""
        m = data["metadata"]
        # 我们假设 Name 是唯一键
        sql = """
            INSERT INTO `character` (Name, Element, Type, Rarity)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
            Element = VALUES(Element), 
            Type = VALUES(Type), 
            Rarity = VALUES(Rarity)
        """
        params = (m["name"], m["element"], m["weapon_type"], m["rarity"])
        self.db.execute_non_query(sql, params)

    def _get_real_id(self, name: str) -> int | None:
        """从数据库查询角色的真实 ID。"""
        sql = "SELECT ID FROM `character` WHERE Name = %s"
        result = self.db.execute_query(sql, (name,))
        return result[0][0] if result else None

    def _sync_stats_table(
        self, table_name: str, char_id: int, stats_data: dict[int, dict], key_name: str
    ) -> None:
        levels = [1, 20, 40, 50, 60, 70, 80, 90, 95, 100]
        vals = [stats_data.get(lv, {}).get(key_name, 0.0) for lv in levels]

        columns = ", ".join([f"`{lv}`" for lv in levels])
        placeholders = ", ".join(["%s"] * (len(levels) + 1))

        # 使用 REPLACE INTO 或 INSERT ... ON DUPLICATE KEY UPDATE
        sql = f"REPLACE INTO `{table_name}` (ID, {columns}) VALUES ({placeholders})"
        params = tuple([char_id] + vals)
        self.db.execute_non_query(sql, params)

    def _sync_breakthrough(self, data: dict[str, Any], char_id: int) -> None:
        stats_data = data["base_stats"]
        prop_name = data["metadata"].get("breakthrough_prop")
        attr_id = self.ATTR_NAME_TO_ID.get(prop_name, 0)

        levels = [1, 20, 40, 50, 60, 70, 80, 90, 95, 100]
        vals = [stats_data.get(lv, {}).get(prop_name, 0.0) for lv in levels]

        columns = ", ".join([f"`{lv}`" for lv in levels])
        placeholders = ", ".join(["%s"] * 12)
        sql = f"REPLACE INTO `breakthrough_attribute` (ID, {columns}, AttributeId) VALUES ({placeholders})"
        params = tuple([char_id] + vals + [attr_id])
        self.db.execute_non_query(sql, params)
