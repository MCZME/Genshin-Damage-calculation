import random
from core.action.damage import DamageType
from core.event import EventBus, EventHandler, EventType
from core.logger import get_emulation_logger
import core.tool as T
from weapon.weapon import Weapon
from core.registry import register_weapon

@register_weapon("螭骨剑", "双手剑")
class SerpentSpine(Weapon):
    ID = 1
    def __init__(self,character,level,lv):
        super().__init__(character,SerpentSpine.ID,level,lv)
        self.skill_param = [6,7,8,9,10]

    def skill(self):
        attribute_panel = self.character.attribute_panel
        attribute_panel["伤害加成"] += 5*self.skill_param[self.lv-1]

# 焚曜千阳
