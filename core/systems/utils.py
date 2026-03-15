from __future__ import annotations
from typing import Any
from core.mechanics.aura import Element

class AttributeCalculator:
    """
    [V2.4] 统一属性合算工具。
    负责从 Base + Modifiers 聚合出最终战斗数值。
    """
    
    @staticmethod
    def get_val_by_name(entity: Any, stat_name: str) -> float:
        """[V2.5] 根据属性名动态获取合算值"""
        mapping = {
            "攻击力": AttributeCalculator.get_final_atk,
            "生命值": AttributeCalculator.get_final_hp,
            "防御力": AttributeCalculator.get_final_def,
            "元素精通": AttributeCalculator.get_final_em,
            "暴击率": AttributeCalculator.get_final_crit_rate,
            "暴击伤害": AttributeCalculator.get_final_crit_dmg,
            "元素充能效率": AttributeCalculator.get_final_er,
            "治疗加成": AttributeCalculator.get_final_healing_bonus,
            "受治疗加成": AttributeCalculator.get_final_incoming_healing_bonus,
            "护盾强效": AttributeCalculator.get_final_shield_strength,
        }
        if stat_name in mapping:
            return mapping[stat_name](entity)
        
        # 针对抗性类属性的动态路由
        if "抗性" in stat_name:
            return AttributeCalculator.get_final_res(entity, stat_name)
            
        return float(entity.attribute_data.get(stat_name, 0.0))

    @staticmethod
    def get_final_atk(entity: Any) -> float:
        """合算最终攻击力"""
        base = float(entity.attribute_data.get('攻击力', 0.0))
        percent = float(entity.attribute_data.get('攻击力%', 0.0))
        flat = float(entity.attribute_data.get('固定攻击力', 0.0))
        
        for m in getattr(entity, 'dynamic_modifiers', []):
            if m.stat == '攻击力%':
                percent += m.value
            if m.stat == '固定攻击力':
                flat += m.value
        
        return base * (1 + percent / 100) + flat

    @staticmethod
    def get_final_hp(entity: Any) -> float:
        """合算最终生命值"""
        base = float(entity.attribute_data.get('生命值', 0.0))
        percent = float(entity.attribute_data.get('生命值%', 0.0))
        flat = float(entity.attribute_data.get('固定生命值', 0.0))
        
        for m in getattr(entity, 'dynamic_modifiers', []):
            if m.stat == '生命值%':
                percent += m.value
            if m.stat == '固定生命值':
                flat += m.value
        
        return base * (1 + percent / 100) + flat

    @staticmethod
    def get_final_def(entity: Any) -> float:
        """合算最终防御力"""
        base = float(entity.attribute_data.get('防御力', 0.0))
        percent = float(entity.attribute_data.get('防御力%', 0.0))
        flat = float(entity.attribute_data.get('固定防御力', 0.0))
        
        for m in getattr(entity, 'dynamic_modifiers', []):
            if m.stat == '防御力%':
                percent += m.value
            if m.stat == '固定防御力':
                flat += m.value
        
        return base * (1 + percent / 100) + flat

    @staticmethod
    def get_final_em(entity: Any) -> float:
        """合算最终元素精通"""
        val = float(entity.attribute_data.get('元素精通', 0.0))
        for m in getattr(entity, 'dynamic_modifiers', []):
            if m.stat == '元素精通':
                val += m.value
        return val

    @staticmethod
    def get_final_crit_rate(entity: Any) -> float:
        """合算最终暴击率 (%)"""
        val = float(entity.attribute_data.get('暴击率', 5.0))
        for m in getattr(entity, 'dynamic_modifiers', []):
            if m.stat == '暴击率':
                val += m.value
        return val

    @staticmethod
    def get_final_crit_dmg(entity: Any) -> float:
        """合算最终暴击伤害 (%)"""
        val = float(entity.attribute_data.get('暴击伤害', 50.0))
        for m in getattr(entity, 'dynamic_modifiers', []):
            if m.stat == '暴击伤害':
                val += m.value
        return val

    @staticmethod
    def get_final_er(entity: Any) -> float:
        """合算最终元素充能效率 (%)"""
        val = float(entity.attribute_data.get('元素充能效率', 100.0))
        for m in getattr(entity, 'dynamic_modifiers', []):
            if m.stat == '元素充能效率':
                val += m.value
        return val

    @staticmethod
    def get_final_healing_bonus(entity: Any) -> float:
        """合算最终治疗加成 (%)"""
        val = float(entity.attribute_data.get('治疗加成', 0.0))
        for m in getattr(entity, 'dynamic_modifiers', []):
            if m.stat == '治疗加成':
                val += m.value
        return val

    @staticmethod
    def get_final_incoming_healing_bonus(entity: Any) -> float:
        """合算最终受治疗加成 (%)"""
        val = float(entity.attribute_data.get('受治疗加成', 0.0))
        for m in getattr(entity, 'dynamic_modifiers', []):
            if m.stat == '受治疗加成':
                val += m.value
        return val

    @staticmethod
    def get_final_shield_strength(entity: Any) -> float:
        """合算最终护盾强效 (%)"""
        val = float(entity.attribute_data.get('护盾强效', 0.0))
        for m in getattr(entity, 'dynamic_modifiers', []):
            if m.stat == '护盾强效':
                val += m.value
        return val

    @staticmethod
    def get_final_res(entity: Any, stat_name: str) -> float:
        """合算最终抗性 (%)"""
        val = float(entity.attribute_data.get(stat_name, 10.0))
        for m in getattr(entity, 'dynamic_modifiers', []):
            if m.stat == stat_name:
                val += m.value
        return val

    @staticmethod
    def get_final_damage_bonus(entity: Any, element_name: str | None = None) -> float:
        """
        合算最终伤害加成 (%)。
        """
        bonus = float(entity.attribute_data.get('伤害加成', 0.0))
        for m in getattr(entity, 'dynamic_modifiers', []):
            if m.stat == '伤害加成':
                bonus += m.value

        if element_name and element_name not in ("无", "物理"):
            key = f"{element_name}元素伤害加成"
            bonus += float(entity.attribute_data.get(key, 0.0))
            for m in getattr(entity, 'dynamic_modifiers', []):
                if m.stat == key:
                    bonus += m.value
        elif element_name == "物理":
            key = "物理伤害加成"
            bonus += float(entity.attribute_data.get(key, 0.0))
            for m in getattr(entity, 'dynamic_modifiers', []):
                if m.stat == key:
                    bonus += m.value

        return bonus
