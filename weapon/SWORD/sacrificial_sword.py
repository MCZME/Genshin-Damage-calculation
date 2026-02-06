import random
from core.logger import get_emulation_logger
from core.effect.stat_modifier import DefenseBoostEffect, EnergyRechargeBoostEffect
from core.action.damage import DamageType

from core.event import EventBus, EventHandler, EventType
from core.team import Team
import core.tool as T
from weapon.weapon import Weapon
from core.registry import register_weapon

@register_weapon("祭礼剑", "单手剑")
class SacrificialSword(Weapon,EventHandler):
    ID = 12
    def __init__(self, character, level=1, lv=1):
        super().__init__(character, SacrificialSword.ID, level, lv)
        self.last_tigger_time = -30*60
        self.interval = 30 * 60
        self.chance = [0.4,0.5,0.6,0.7,0.8]

    def skill(self):
        EventBus.subscribe(EventType.AFTER_SKILL, self)

    def handle_event(self, event):
        if event.event_type == EventType.AFTER_SKILL:
            if event.data["character"] == self.character:
                if T.get_current_time() - self.last_tigger_time > self.interval:
                    if random.random() < self.chance[self.lv - 1]:
                        self.last_tigger_time = T.get_current_time()
                        self.character.Skill.last_use_time = -9999
                        get_emulation_logger().log_skill_use("⌚" + self.character.name + f" 触发{self.name}")
