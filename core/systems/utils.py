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
