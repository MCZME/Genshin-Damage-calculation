from typing import Any
from core.effect.base import BaseEffect
from core.event import EventHandler, EventType, GameEvent
from core.action.damage import DamageType

class FreedomSwornEffect(BaseEffect, EventHandler):
    """苍古自由之誓效果"""
    def __init__(self, owner: Any, lv: int):
        super().__init__(owner, "苍古自由之誓", duration=12*60)
        self.lv = lv
        self.dmg_bonus = [16, 20, 24, 28, 32]
        self.atk_bonus = [20, 25, 30, 35, 40]

    def on_apply(self):
        self.owner.attribute_panel['攻击力%'] += self.atk_bonus[self.lv-1]
        self.owner.event_engine.subscribe(EventType.BEFORE_DAMAGE_BONUS, self)

    def on_remove(self):
        self.owner.attribute_panel['攻击力%'] -= self.atk_bonus[self.lv-1]
        self.owner.event_engine.unsubscribe(EventType.BEFORE_DAMAGE_BONUS, self)

    def handle_event(self, event: GameEvent):
        if event.source == self.owner:
            damage = event.data['damage']
            if damage.damage_type in [DamageType.NORMAL, DamageType.CHARGED, DamageType.PLUNGING]:
                damage.panel['伤害加成'] += self.dmg_bonus[self.lv-1]
