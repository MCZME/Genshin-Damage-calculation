from core.context import get_context

from core.event import EventHandler, EventType
from core.effect.stat_modifier import AttackBoostEffect
from weapon.weapon import Weapon
from core.registry import register_weapon

@register_weapon("讨龙英杰谭", "法器")
class ThrillingTalesOfDragonSlayers(Weapon, EventHandler):
    ID = 174
    def __init__(self, character, level=1, lv=1):
        super().__init__(character, ThrillingTalesOfDragonSlayers.ID, level, lv)
        self.last_trigger_time = -1200 
        self.attack_boost = [24,30,36,42,48]
       

    def skill(self):
        get_context().event_engine.subscribe(EventType.AFTER_CHARACTER_SWITCH, self)

    def handle_event(self, event):
        current_time = event.frame
        if current_time - self.last_trigger_time >= 20*60:
            if event.data["old_character"] == self.character:
                effect = AttackBoostEffect(self.character,event.data["new_character"], "讨龙英杰谭", self.attack_boost[self.lv-1], 10*60)
                effect.apply()
                self.last_trigger_time = current_time

