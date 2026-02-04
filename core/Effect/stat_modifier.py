from typing import Any, Dict
from core.effect.base import BaseEffect, StackingRule

class StatModifierEffect(BaseEffect):
    """
    通用面板属性加成效果。
    能够一次性修改多个面板数值（如攻击力、暴击率、伤害加成等）。
    """
    def __init__(self, owner: Any, name: str, stats: Dict[str, float], duration: float, 
                 stacking_rule: StackingRule = StackingRule.REFRESH):
        super().__init__(owner, name, duration, stacking_rule)
        self.stats = stats # 例如 {'攻击力%': 20, '暴击率': 10}

    def on_apply(self):
        """修改面板"""
        panel = self.owner.attribute_panel
        for attr, value in self.stats.items():
            if attr in panel:
                panel[attr] += value
            else:
                # 如果是特定元素伤害加成，支持动态拼接 (例如 '火' + '元素伤害加成')
                panel[attr] = panel.get(attr, 0.0) + value

    def on_remove(self):
        """还原面板"""
        panel = self.owner.attribute_panel
        for attr, value in self.stats.items():
            if attr in panel:
                panel[attr] -= value

    def on_stack_added(self, other: 'StatModifierEffect'):
        """如果支持堆叠，可在此处实现层数逻辑"""
        pass

# -----------------------------------------------------
# 为了保持旧代码兼容性，提供一些工厂方法或别名
# -----------------------------------------------------
def AttackBoostEffect(source, owner, name, bonus, duration):
    return StatModifierEffect(owner, name, {"攻击力%": bonus}, duration)

def DamageBoostEffect(source, owner, name, bonus, duration):
    return StatModifierEffect(owner, name, {"伤害加成": bonus}, duration)

def CritRateBoostEffect(owner, name, bonus, duration):
    return StatModifierEffect(owner, name, {"暴击率": bonus}, duration)
