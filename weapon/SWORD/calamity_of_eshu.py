import random
from core.logger import get_emulation_logger
from core.effect.stat_modifier import DefenseBoostEffect, EnergyRechargeBoostEffect
from core.action.damage import DamageType

from core.event import EventBus, EventHandler, EventType
from core.team import Team
import core.tool as T
from weapon.weapon import Weapon
from core.registry import register_weapon

@register_weapon("厄水之祸", "单手剑")
class CalamityOfEshu(Weapon,EventHandler):
    ID = 39
    def __init__(self, character, level=1, lv=1):
        super().__init__(character, CalamityOfEshu.ID, level, lv)
        self.dmg_bonus = [20,25,30,35,40]
        self.critical_bonus = [8,10,12,14,16]

    def skill(self):
        EventBus.subscribe(EventType.BEFORE_DAMAGE_BONUS, self)
        EventBus.subscribe(EventType.BEFORE_CRITICAL, self)

    def handle_event(self, event):
        if event.data["character"] == self.character:
            s = T.get_shield()
            if not s:
                return
            
            damage = event.data["damage"]
            if event.event_type == EventType.BEFORE_DAMAGE_BONUS and damage.damage_type in [DamageType.NORMAL, DamageType.CHARGED]:
                damage.panel["伤害加成"] += self.dmg_bonus[self.lv - 1]
                damage.setDamageData("厄水之祸_伤害加成", self.dmg_bonus[self.lv - 1])
            elif event.event_type == EventType.BEFORE_CRITICAL:
                damage.panel["暴击率"] += self.critical_bonus[self.lv - 1]
                damage.setDamageData("厄水之祸_暴击率", self.critical_bonus[self.lv - 1])
