from typing import Any
from core.effect.base import BaseEffect
from core.event import EventHandler, EventType, GameEvent
from core.action.damage import DamageType
from core.team import Team

class ThirstEffect(BaseEffect):
    """渴盼效果 - 记录治疗量"""
    def __init__(self, owner: Any):
        super().__init__(owner, "渴盼效果", duration=6*60)
        self.heal_amount = 0
        self.max_amount = 15000

    def add_heal(self, amount: float):
        self.heal_amount = min(self.heal_amount + amount, self.max_amount)

    def on_remove(self):
        if self.heal_amount > 0:
            WaveEffect(self.owner, self.heal_amount).apply()

class WaveEffect(BaseEffect, EventHandler):
    """彼时的浪潮 - 基础伤害提升"""
    def __init__(self, owner: Any, heal_total: float):
        super().__init__(owner, "彼时的浪潮", duration=10*60)
        self.bonus = heal_total * 0.08
        self.max_hits = 5
        self.hit_count = 0

    def on_apply(self):
        self.owner.event_engine.subscribe(EventType.BEFORE_FIXED_DAMAGE, self)

    def on_remove(self):
        self.owner.event_engine.unsubscribe(EventType.BEFORE_FIXED_DAMAGE, self)

    def handle_event(self, event: GameEvent):
        damage = event.data['damage']
        if (damage.source in Team.team and 
            damage.damage_type in [DamageType.NORMAL, DamageType.CHARGED, DamageType.SKILL, DamageType.BURST, DamageType.PLUNGING]):
            damage.panel['固定伤害基础值加成'] += self.bonus
            self.hit_count += 1
            if self.hit_count >= self.max_hits:
                self.remove()
