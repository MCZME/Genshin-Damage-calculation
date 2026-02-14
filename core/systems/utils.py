from typing import Any, List
from core.systems.contract.modifier import ModifierRecord


class AttributeCalculator:
    """
    属性计算工具类 (V2.4 审计增强版)。

    采用 [基础属性] + [动态修饰符] 的实时计算模式，支持审计追踪。
    """

    @staticmethod
    def get_final_stat(entity: Any, stat_name: str) -> float:
        """
        计算特定属性的最终值。

        逻辑优先级:
        1. 获取基础值 (attribute_data)
        2. 应用 SET 操作 (最后一个 SET 覆盖之前的)
        3. 应用 ADD 操作 (累加)
        4. 应用 MULT 操作 (连乘)
        """
        base_val = entity.attribute_data.get(stat_name, 0.0)

        # 兼容性处理：如果属性名带 %，比如 "生命值%"，它通常是作为加成系数存在的
        # 我们这里主要处理核心主属性：攻击力、生命值、防御力、元素精通等

        modifiers = [
            m for m in getattr(entity, "dynamic_modifiers", []) if m.stat == stat_name
        ]

        final_val = base_val

        # 处理 SET
        set_mods = [m for m in modifiers if m.op == "SET"]
        if set_mods:
            final_val = set_mods[-1].value

        # 处理 ADD
        for m in modifiers:
            if m.op == "ADD":
                final_val += m.value

        # 处理 MULT
        for m in modifiers:
            if m.op == "MULT":
                final_val *= m.value

        return final_val

    @staticmethod
    def get_attack(entity: Any) -> float:
        base = entity.attribute_data.get("攻击力", 0.0)

        # 汇总加成
        percent = entity.attribute_data.get("攻击力%", 0.0)
        flat = entity.attribute_data.get("固定攻击力", 0.0)

        # 动态加成
        for m in getattr(entity, "dynamic_modifiers", []):
            if m.stat == "攻击力%":
                percent += m.value
            if m.stat == "固定攻击力":
                flat += m.value

        return base * (1 + percent / 100) + flat

    @staticmethod
    def get_hp(entity: Any) -> float:
        base = entity.attribute_data.get("生命值", 0.0)
        percent = entity.attribute_data.get("生命值%", 0.0)
        flat = entity.attribute_data.get("固定生命值", 0.0)

        for m in getattr(entity, "dynamic_modifiers", []):
            if m.stat == "生命值%":
                percent += m.value
            if m.stat == "固定生命值":
                flat += m.value

        return base * (1 + percent / 100) + flat

    @staticmethod
    def get_defense(entity: Any) -> float:
        base = entity.attribute_data.get("防御力", 0.0)
        percent = entity.attribute_data.get("防御力%", 0.0)
        flat = entity.attribute_data.get("固定防御力", 0.0)

        for m in getattr(entity, "dynamic_modifiers", []):
            if m.stat == "防御力%":
                percent += m.value
            if m.stat == "固定防御力":
                flat += m.value

        return base * (1 + percent / 100) + flat

    @staticmethod
    def get_mastery(entity: Any) -> float:
        val = entity.attribute_data.get("元素精通", 0.0)
        for m in getattr(entity, "dynamic_modifiers", []):
            if m.stat == "元素精通":
                val += m.value
        return val

    @staticmethod
    def get_shield_strength_bonus(entity: Any) -> float:
        val = entity.attribute_data.get("护盾强效", 0.0)
        for m in getattr(entity, "dynamic_modifiers", []):
            if m.stat == "护盾强效":
                val += m.value
        return val / 100

    @staticmethod
    def get_energy_recharge(entity: Any) -> float:
        val = entity.attribute_data.get("元素充能效率", 100.0)
        for m in getattr(entity, "dynamic_modifiers", []):
            if m.stat == "元素充能效率":
                val += m.value
        return val / 100

    @staticmethod
    def get_healing_bonus(entity: Any) -> float:
        val = entity.attribute_data.get("治疗加成", 0.0)
        for m in getattr(entity, "dynamic_modifiers", []):
            if m.stat == "治疗加成":
                val += m.value
        return val / 100

    @staticmethod
    def get_healed_bonus(entity: Any) -> float:
        val = entity.attribute_data.get("受治疗加成", 0.0)
        for m in getattr(entity, "dynamic_modifiers", []):
            if m.stat == "受治疗加成":
                val += m.value
        return val / 100

    @staticmethod
    def get_damage_bonus(entity: Any, element_type: str = None) -> float:
        attr = entity.attribute_data
        bonus = attr.get("伤害加成", 0.0)

        # 动态基础伤害加成
        for m in getattr(entity, "dynamic_modifiers", []):
            if m.stat == "伤害加成":
                bonus += m.value

        if element_type:
            key = (
                element_type if element_type == "物理" else element_type + "元素"
            ) + "伤害加成"
            bonus += attr.get(key, 0.0)
            # 动态元素加成
            for m in getattr(entity, "dynamic_modifiers", []):
                if m.stat == key:
                    bonus += m.value

        return bonus / 100

    @staticmethod
    def get_crit_rate(entity: Any) -> float:
        val = entity.attribute_data.get("暴击率", 5.0)
        for m in getattr(entity, "dynamic_modifiers", []):
            if m.stat == "暴击率":
                val += m.value
        return val / 100

    @staticmethod
    def get_crit_damage(entity: Any) -> float:
        val = entity.attribute_data.get("暴击伤害", 50.0)
        for m in getattr(entity, "dynamic_modifiers", []):
            if m.stat == "暴击伤害":
                val += m.value
        return val / 100

    @staticmethod
    def get_audit_trail(entity: Any, stat_names: List[str]) -> List[ModifierRecord]:
        """获取指定属性的完整审计链。"""
        return [
            m for m in getattr(entity, "dynamic_modifiers", []) if m.stat in stat_names
        ]
