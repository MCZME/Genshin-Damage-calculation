from typing import Any
from core.effect.base import BaseEffect

class MarechausseeHunterEffect(BaseEffect):
    """逐影猎人套装效果"""
    def __init__(self, owner: Any):
        super().__init__(owner, "逐影猎人", duration=5*60)
        self.stack = 0
        self.bonus_per_stack = 12

    def on_apply(self):
        self.stack = 1
        self.owner.attribute_panel['暴击率'] += self.bonus_per_stack

    def on_stack_added(self, other: 'MarechausseeHunterEffect'):
        if self.stack < 3:
            self.owner.attribute_panel['暴击率'] += self.bonus_per_stack
            self.stack += 1
        self.duration = self.max_duration

    def on_remove(self):
        self.owner.attribute_panel['暴击率'] -= self.stack * self.bonus_per_stack
