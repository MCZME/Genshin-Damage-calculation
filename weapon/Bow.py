import random
from core.Event import EventBus, EventHandler, EventType
from core.Logger import get_emulation_logger
import core.Tool as T
from weapon.weapon import Weapon


class SacrificialBow(Weapon,EventHandler):
    ID = 103
    def __init__(self, character, level=1, lv=1):
        super().__init__(character, SacrificialBow.ID, level, lv)
        self.last_tigger_time = -30*60
        self.interval = 30 * 60
        self.chance = [0.4,0.5,0.6,0.7,0.8]

    def skill(self):
        EventBus.subscribe(EventType.AFTER_SKILL, self)

    def handle_event(self, event):
        if event.event_type == EventType.AFTER_SKILL:
            if event.data['character'] == self.character:
                if T.GetCurrentTime() - self.last_tigger_time > self.interval:
                    if random.random() < self.chance[self.lv - 1]:
                        self.last_tigger_time = T.GetCurrentTime()
                        self.character.Skill.cd_timer = self.character.Skill.cd
                        get_emulation_logger().log_skill_use("⌚" + self.character.name + f' 触发{self.name}')

class AquaSimulacra(Weapon):
    ID = 103
    def __init__(self, character, level=1, lv=1):
        super().__init__(character, AquaSimulacra.ID, level, lv)
        self.hp_bonus = [16,20,24,28,32]
        self.dmg_bonus = [20,25,30,35,40]

    def skill(self):
        # 默认周围存在敌人
        self.character.attributePanel['生命值%'] += self.hp_bonus[self.lv - 1]
        self.character.attributePanel['伤害加成'] += self.dmg_bonus[self.lv - 1]

bow = {
    '若水':AquaSimulacra,
    '祭礼弓':SacrificialBow,
}