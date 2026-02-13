from core.context import get_context
from core.effect.stat_modifier import EnergyRechargeBoostEffect
from core.systems.contract.damage import DamageType

from core.event import EventHandler, EventType
from weapon.weapon import Weapon
from core.registry import register_weapon

@register_weapon("灰河渡手", "单手剑")
class FleuveCendreFerryman(Weapon,EventHandler):
    ID = 33
    def __init__(self, character, level=1, lv=1):
        super().__init__(character, FleuveCendreFerryman.ID, level, lv)
        self.critical_rate = [8,10,12,14,16]
        self.engergy_recharge = [16,20,24,28,32]

    def skill(self):
        get_context().event_engine.subscribe(EventType.AFTER_SKILL, self)
        get_context().event_engine.subscribe(EventType.BEFORE_CRITICAL, self)

    def handle_event(self, event):
        if event.event_type == EventType.AFTER_SKILL:
            if event.data["character"] == self.character:
                EnergyRechargeBoostEffect(self.character, "灰河渡手", self.engergy_recharge[self.lv - 1], 5*60).apply()
        if event.event_type == EventType.BEFORE_CRITICAL:
            if event.data["character"] == self.character and event.data["damage"].damage_type == DamageType.SKILL:
                event.data["damage"].panel["暴击率"] += self.critical_rate[self.lv - 1]
                event.data["damage"].setDamageData(self.name,self.critical_rate[self.lv - 1])

