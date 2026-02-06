from typing import Any

class AttributeCalculator:
    """
    统一的属性计算工具类，用于从实体的 attributePanel 中提取最终属性值。
    """
    @staticmethod
    def get_attack(entity: Any) -> float:
        attr = entity.attributePanel
        base = attr.get('攻击力', 0)
        percent = attr.get('攻击力%', 0)
        flat = attr.get('固定攻击力', 0)
        return base * (1 + percent / 100) + flat

    @staticmethod
    def get_hp(entity: Any) -> float:
        attr = entity.attributePanel
        base = attr.get('生命值', 0)
        percent = attr.get('生命值%', 0)
        flat = attr.get('固定生命值', 0)
        return base * (1 + percent / 100) + flat

    @staticmethod
    def get_defense(entity: Any) -> float:
        attr = entity.attributePanel
        base = attr.get('防御力', 0)
        percent = attr.get('防御力%', 0)
        flat = attr.get('固定防御力', 0)
        return base * (1 + percent / 100) + flat

    @staticmethod
    def get_mastery(entity: Any) -> float:
        return entity.attributePanel.get('元素精通', 0)

    @staticmethod
    def get_shield_strength_bonus(entity: Any) -> float:
        """获取护盾强效加成 (百分比/100)"""
        return entity.attributePanel.get('护盾强效', 0) / 100

    @staticmethod
    def get_energy_recharge(entity: Any) -> float:
        """获取元素充能效率 (百分比/100)"""
        return entity.attributePanel.get('元素充能效率', 100) / 100

    @staticmethod
    def get_healing_bonus(entity: Any) -> float:
        """获取治疗加成 (百分比/100)"""
        return entity.attributePanel.get('治疗加成', 0) / 100

    @staticmethod
    def get_healed_bonus(entity: Any) -> float:
        """获取受治疗加成 (百分比/100)"""
        return entity.attributePanel.get('受治疗加成', 0) / 100
