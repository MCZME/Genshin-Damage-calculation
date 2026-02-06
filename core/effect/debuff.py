from typing import Any, List
from core.effect.base import BaseEffect

class DefenseDebuffEffect(BaseEffect):
    """防御力降低效果"""
    def __init__(self, owner: Any, name: str, debuff_rate: float, duration: float):
        super().__init__(owner, name, duration)
        self.debuff_rate = debuff_rate

    def on_apply(self):
        # 假设 Target 拥有 defense 属性
        if hasattr(self.owner, 'defense'):
            self.owner.defense *= (1 - self.debuff_rate / 100)

    def on_remove(self):
        if hasattr(self.owner, 'defense'):
            self.owner.defense /= (1 - self.debuff_rate / 100)

class ResistanceDebuffEffect(BaseEffect):
    """元素抗性降低效果"""
    def __init__(self, owner: Any, name: str, elements: List[str], debuff_rate: float, duration: float):
        super().__init__(owner, name, duration)
        self.elements = elements
        self.debuff_rate = debuff_rate

    def on_apply(self):
        if hasattr(self.owner, 'current_resistance'):
            for element in self.elements:
                self.owner.current_resistance[element] -= self.debuff_rate

    def on_remove(self):
        if hasattr(self.owner, 'current_resistance'):
            for element in self.elements:
                self.owner.current_resistance[element] += self.debuff_rate
