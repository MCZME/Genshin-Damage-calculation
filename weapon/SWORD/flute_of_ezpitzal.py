from core.effect.stat_modifier import DefenseBoostEffect

from core.event import EventBus, EventHandler, EventType
from weapon.weapon import Weapon
from core.registry import register_weapon

@register_weapon("息燧之笛", "单手剑")
class FluteOfEzpitzal(Weapon,EventHandler):
    ID = 38
    def __init__(self, character, level=1, lv=1):
        super().__init__(character, FluteOfEzpitzal.ID, level, lv)
        self.defense_boost = [16,20,24,28,32]

    def skill(self):
        EventBus.subscribe(EventType.BEFORE_SKILL, self)

    def handle_event(self, event):
        if event.event_type == EventType.BEFORE_SKILL:
            if event.data["character"] == self.character:
                effect = DefenseBoostEffect(self.character, "息燧之笛", self.defense_boost[self.lv - 1],15*60)
                effect.apply()
