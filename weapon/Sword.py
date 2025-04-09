from setup.BaseEffect import DefenseBoostEffect
from setup.Event import EventBus, EventHandler, EventType
import setup.Tool as T
from weapon.weapon import Weapon


sword = ['息燧之笛','风鹰剑']

class FluteOfEzpitzal(Weapon,EventHandler):
    ID = 38
    def __init__(self, character, level=1, lv=1):
        super().__init__(character, FluteOfEzpitzal.ID, level, lv)
        self.defense_boost = [16,20,24,28,32]

    def skill(self):
        EventBus.subscribe(EventType.BEFORE_SKILL, self)

    def handle_event(self, event):
        if event.event_type == EventType.BEFORE_SKILL:
            if event.data['character'] == self.character:
                effect = DefenseBoostEffect(self.character, '息燧之笛', self.defense_boost[self.lv - 1],15*60)
                effect.apply()

class AquilaFavonia(Weapon):
    ID = 40
    def __init__(self, character, level=1, lv=1):
        super().__init__(character, AquilaFavonia.ID, level, lv)

    def get_data(self, level):
        l = T.level(level)
        self.attributeData["攻击力"] = self.stats[4+l]
        self.attributeData['物理伤害加成'] = self.stats[12+l]
    
    def skill(self):
        self.character.attributePanel['攻击力%'] += 20
