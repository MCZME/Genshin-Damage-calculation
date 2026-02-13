from typing import Any
from core.effect.base import BaseEffect
from core.event import EventHandler, EventType, GameEvent
import core.tool as T
from weapon.weapon import Weapon
from core.registry import register_weapon

class TEFChargedBoostEffect(BaseEffect, EventHandler):
    """万世流涌大典 - 重击提升"""
    def __init__(self, owner: Any):
        super().__init__(owner, "万世流涌大典_重击提升", duration=4*60)
        self.bonus = 14
        self.stack = 0
        self.last_trigger = 0
        self.last_energy_trigger = -12*60
        self.interval = 0.3*60
        self.energy_interval = 12*60

    def on_apply(self):
        self.stack = 1
        self.owner.event_engine.subscribe(EventType.BEFORE_DAMAGE_BONUS, self)

    def on_remove(self):
        self.owner.event_engine.unsubscribe(EventType.BEFORE_DAMAGE_BONUS, self)

    def on_stack_added(self, other: "TEFChargedBoostEffect"):
        now = T.get_current_time()
        if now - self.last_trigger > self.interval:
            if self.stack < 3:
                self.stack += 1
            self.last_trigger = now
            if self.stack == 3 and now - self.last_energy_trigger > self.energy_interval:
                T.summon_energy(8, self.owner, ("无", 0))
                self.last_energy_trigger = now
            self.duration = self.max_duration

    def handle_event(self, event: GameEvent):
        if event.data["character"] == self.owner:
            damage = event.data["damage"]
            from core.systems.contract.damage import DamageType
            d_type = getattr(damage, "damage_type", getattr(damage, "damage_type", None))
            if d_type == DamageType.CHARGED:
                damage.panel["伤害加成"] += self.bonus * self.stack
                damage.setDamageData(self.name, self.bonus * self.stack)

@register_weapon("万世流涌大典", "法器")
class TomeOfTheEternalFlow(Weapon, EventHandler):
    ID = 148
    def __init__(self, character, level=1, lv=1):
        super().__init__(character, TomeOfTheEternalFlow.ID, level, lv)

    def skill(self):
        self.character.attribute_data["生命值%"] += 16
        self.event_engine.subscribe(EventType.AFTER_HEALTH_CHANGE, self)

    def handle_event(self, event: GameEvent):
        if event.event_type == EventType.AFTER_HEALTH_CHANGE and event.data["amount"] != 0:
            if event.data["character"] == self.character:
                TEFChargedBoostEffect(self.character).apply()
