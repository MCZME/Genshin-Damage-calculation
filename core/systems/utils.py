from typing import Any, Optional

class AttributeCalculator:
    """
    属性合算工具类 (V2.4 审计集成版)。
    负责从实体的基础属性与动态审计链中合算出最终战斗数值。
    """

    @staticmethod
    def get_attack(entity: Any) -> float:
        base = entity.attribute_data.get('攻击力', 0.0)
        percent = 0.0
        flat = 0.0
        
        # 动态加成
        for m in getattr(entity, 'dynamic_modifiers', []):
            if m.stat == '攻击力%': percent += m.value
            if m.stat == '固定攻击力': flat += m.value
            
        return base * (1 + percent / 100) + flat

    @staticmethod
    def get_hp(entity: Any) -> float:
        base = entity.attribute_data.get('生命值', 0.0)
        percent = 0.0
        flat = 0.0
        
        for m in getattr(entity, 'dynamic_modifiers', []):
            if m.stat == '生命值%': percent += m.value
            if m.stat == '固定生命值': flat += m.value
            
        return base * (1 + percent / 100) + flat

    @staticmethod
    def get_defense(entity: Any) -> float:
        base = entity.attribute_data.get('防御力', 0.0)
        percent = 0.0
        flat = 0.0
        
        for m in getattr(entity, 'dynamic_modifiers', []):
            if m.stat == '防御力%': percent += m.value
            if m.stat == '固定防御力': flat += m.value
            
        return base * (1 + percent / 100) + flat

    @staticmethod
    def get_mastery(entity: Any) -> float:
        val = entity.attribute_data.get('元素精通', 0.0)
        for m in getattr(entity, 'dynamic_modifiers', []):
            if m.stat == '元素精通': val += m.value
        return val

    @staticmethod
    def get_shield_strength(entity: Any) -> float:
        val = entity.attribute_data.get('护盾强效', 0.0)
        for m in getattr(entity, 'dynamic_modifiers', []):
            if m.stat == '护盾强效': val += m.value
        return val / 100

    @staticmethod
    def get_energy_recharge(entity: Any) -> float:
        val = entity.attribute_data.get('元素充能效率', 100.0)
        for m in getattr(entity, 'dynamic_modifiers', []):
            if m.stat == '元素充能效率': val += m.value
        return val / 100

    @staticmethod
    def get_healing_bonus(entity: Any) -> float:
        val = entity.attribute_data.get('治疗加成', 0.0)
        for m in getattr(entity, 'dynamic_modifiers', []):
            if m.stat == '治疗加成': val += m.value
        return val / 100

    @staticmethod
    def get_incoming_healing_bonus(entity: Any) -> float:
        val = entity.attribute_data.get('受治疗加成', 0.0)
        for m in getattr(entity, 'dynamic_modifiers', []):
            if m.stat == '受治疗加成': val += m.value
        return val / 100

    @staticmethod
    def get_damage_bonus(entity: Any, element_type: Optional[str] = None) -> float:
        """获取总增伤。若指定元素，则包含对应元素的加成。"""
        bonus = entity.attribute_data.get('伤害加成', 0.0)
        
        # 动态基础伤害加成
        for m in getattr(entity, 'dynamic_modifiers', []):
            if m.stat == '伤害加成': bonus += m.value
            
        if element_type:
            key = f"{element_type}元素伤害加成" if element_type != "物理" else "物理伤害加成"
            bonus += entity.attribute_data.get(key, 0.0)
            # 动态元素加成
            for m in getattr(entity, 'dynamic_modifiers', []):
                if m.stat == key: bonus += m.value
                
        return bonus / 100

    @staticmethod
    def get_crit_rate(entity: Any) -> float:
        val = entity.attribute_data.get('暴击率', 5.0)
        for m in getattr(entity, 'dynamic_modifiers', []):
            if m.stat == '暴击率': val += m.value
        return val / 100

    @staticmethod
    def get_crit_damage(entity: Any) -> float:
        val = entity.attribute_data.get('暴击伤害', 50.0)
        for m in getattr(entity, 'dynamic_modifiers', []):
            if m.stat == '暴击伤害': val += m.value
        return val / 100
