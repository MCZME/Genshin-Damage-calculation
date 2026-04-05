"""武器数据转换器。"""

from typing import Any


class WeaponDataTransformer:
    """
    武器数据转换器。
    将 Project Amber API 原始数据转换为结构化格式。
    """

    WEAPON_TYPE_MAP = {
        "WEAPON_SWORD_ONE_HAND": "单手剑",
        "WEAPON_CLAYMORE": "双手剑",
        "WEAPON_POLE": "长柄武器",
        "WEAPON_BOW": "弓",
        "WEAPON_CATALYST": "法器",
    }

    FIGHT_PROP_MAP = {
        "FIGHT_PROP_ATTACK_PERCENT": "攻击力%",
        "FIGHT_PROP_CRITICAL": "暴击率",
        "FIGHT_PROP_CRITICAL_HURT": "暴击伤害",
        "FIGHT_PROP_ELEMENT_MASTERY": "元素精通",
        "FIGHT_PROP_CHARGE_EFFICIENCY": "元素充能效率",
        "FIGHT_PROP_HP_PERCENT": "生命值%",
        "FIGHT_PROP_DEFENSE_PERCENT": "防御力%",
        "FIGHT_PROP_PHYSICAL_ADD_HURT": "物理伤害加成",
        "FIGHT_PROP_FIRE_ADD_HURT": "火元素伤害加成",
        "FIGHT_PROP_WATER_ADD_HURT": "水元素伤害加成",
        "FIGHT_PROP_ICE_ADD_HURT": "冰元素伤害加成",
        "FIGHT_PROP_ELEC_ADD_HURT": "雷元素伤害加成",
        "FIGHT_PROP_WIND_ADD_HURT": "风元素伤害加成",
        "FIGHT_PROP_ROCK_ADD_HURT": "岩元素伤害加成",
        "FIGHT_PROP_GRASS_ADD_HURT": "草元素伤害加成",
        "FIGHT_PROP_BASE_HP": "生命值",
        "FIGHT_PROP_BASE_ATTACK": "攻击力",
        "FIGHT_PROP_BASE_DEFENSE": "防御力",
    }

    # 突破等级对应的属性索引
    TARGET_LEVELS = {
        1: 0,
        20: 1,
        40: 2,
        50: 3,
        60: 4,
        70: 5,
        80: 6,
        90: 7,
        95: 7,  # 近似
        100: 7,  # 近似
    }

    def transform(
        self, weapon_raw: dict[str, Any], curve_raw: dict[str, Any]
    ) -> dict[str, Any]:
        """
        转换武器原始数据。

        Args:
            weapon_raw: API 返回的武器详情数据
            curve_raw: 武器成长曲线数据

        Returns:
            结构化数据:
            {
                "metadata": { "id", "name", "type", "rarity", "route" },
                "base_atk": { level: value, ... },
                "secondary_attribute": { "name": str, "values": { level: value } }
            }
        """
        metadata = self._extract_metadata(weapon_raw)
        base_atk = self._calculate_base_atk(weapon_raw, curve_raw)
        secondary = self._extract_secondary_attribute(weapon_raw, curve_raw)

        return {
            "metadata": metadata,
            "base_atk": base_atk,
            "secondary_attribute": secondary,
        }

    def _extract_metadata(self, weapon_raw: dict[str, Any]) -> dict[str, Any]:
        """提取武器基础元数据。"""
        # API 可能返回 type 或 weaponType
        weapon_type_api = weapon_raw.get("type") or weapon_raw.get("weaponType", "")
        weapon_type = self.WEAPON_TYPE_MAP.get(weapon_type_api, weapon_type_api)

        return {
            "id": weapon_raw.get("id"),
            "name": weapon_raw.get("name", "Unknown"),
            "type": weapon_type,
            "rarity": weapon_raw.get("rank", 1),
            "route": weapon_raw.get("route", ""),
        }

    def _calculate_base_atk(
        self, weapon_raw: dict[str, Any], curve_raw: dict[str, Any]
    ) -> dict[int, float]:
        """计算各等级基础攻击力。"""
        upgrade = weapon_raw.get("upgrade", {})
        promote_list = upgrade.get("promote", [])

        # 获取基础攻击力配置
        base_atk_config = None
        for prop in upgrade.get("prop", []):
            if prop.get("propType") == "FIGHT_PROP_BASE_ATTACK":
                base_atk_config = prop
                break

        if not base_atk_config:
            return {lv: 0.0 for lv in self.TARGET_LEVELS}

        init_value = base_atk_config.get("initValue", 0)
        curve_type = base_atk_config.get("type", "")

        results = {}
        for level, promote_idx in self.TARGET_LEVELS.items():
            # 获取成长曲线系数
            curve_data = curve_raw.get(str(level), {}).get("curveInfos", {})
            coeff = curve_data.get(curve_type, 1.0)

            # 获取突破加成
            add_atk = 0.0
            if promote_idx < len(promote_list):
                add_props = promote_list[promote_idx].get("addProps", {})
                add_atk = add_props.get("FIGHT_PROP_BASE_ATTACK", 0.0)

            final_atk = init_value * coeff + add_atk
            results[level] = round(final_atk, 2)

        return results

    def _extract_secondary_attribute(
        self, weapon_raw: dict[str, Any], curve_raw: dict[str, Any]
    ) -> dict[str, Any]:
        """提取副属性。"""
        upgrade = weapon_raw.get("upgrade", {})
        promote_list = upgrade.get("promote", [])

        # 查找副属性类型（非基础属性）
        secondary_prop = None
        for prop in upgrade.get("prop", []):
            prop_type = prop.get("propType", "")
            if prop_type not in [
                "FIGHT_PROP_BASE_HP",
                "FIGHT_PROP_BASE_ATTACK",
                "FIGHT_PROP_BASE_DEFENSE",
            ]:
                secondary_prop = prop
                break

        if not secondary_prop:
            return {"name": None, "values": {}}

        prop_type = secondary_prop.get("propType", "")
        prop_name = self.FIGHT_PROP_MAP.get(prop_type, prop_type)
        init_value = secondary_prop.get("initValue", 0)
        curve_type = secondary_prop.get("type", "")

        # 计算各等级副属性值
        values = {}
        for level, promote_idx in self.TARGET_LEVELS.items():
            curve_data = curve_raw.get(str(level), {}).get("curveInfos", {})
            coeff = curve_data.get(curve_type, 1.0)

            # 副属性通常没有突破加成
            final_val = init_value * coeff

            # 百分比属性转换为百分比形式
            if "%" in prop_name or prop_type in [
                "FIGHT_PROP_CRITICAL",
                "FIGHT_PROP_CRITICAL_HURT",
                "FIGHT_PROP_CHARGE_EFFICIENCY",
                "FIGHT_PROP_ATTACK_PERCENT",
                "FIGHT_PROP_HP_PERCENT",
                "FIGHT_PROP_DEFENSE_PERCENT",
            ]:
                final_val *= 100

            values[level] = round(final_val, 2)

        return {"name": prop_name, "values": values}
