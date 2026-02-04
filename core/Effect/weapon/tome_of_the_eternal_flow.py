from typing import Any
from core.effect.base import BaseEffect
from core.event import EventHandler, EventType, GameEvent
from core.tool import GetCurrentTime, summon_energy

class TEFChargedBoostEffect(BaseEffect, EventHandler):
    """万世流涌大典 - 重击提升"""
    def __init__(self, owner: Any):
        super().__init__(owner, "万世流涌大典_重击提升", duration=4*60)
        self.bonus = 14
        self.stack = 0
        self.last_trigger = 0
        self.last_energy_trigger = 0
        self.interval = 0.3*60
        self.energy_interval = 12*60

    def on_apply(self):
        self.stack = 1
        self.owner.event_engine.subscribe(EventType.BEFORE_DAMAGE_BONUS, self)

    def on_remove(self):
        self.owner.event_engine.unsubscribe(EventType.BEFORE_DAMAGE_BONUS, self)

    def on_stack_added(self, other: 'TEFChargedBoostEffect'):
        now = GetCurrentTime()
        if now - self.last_trigger > self.interval:
            if self.stack < 3:
                self.stack += 1
            self.last_trigger = now
            if self.stack == 3 and now - self.last_energy_trigger > self.energy_interval:
                summon_energy(8, self.owner, ('无', 0)) # 产能逻辑
                self.last_energy_trigger = now
            self.duration = self.max_duration

    def handle_event(self, event: GameEvent):
        if event.source == self.owner:
            damage = event.data['damage']
            if damage.damage_type.value == '重击':
                damage.panel['伤害加成'] += self.bonus * self.stack
