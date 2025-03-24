from setup.DamageCalculation import DamageType
from weapon.weapon import Weapon
from setup.Event import EventBus, EventType, EventHandler
from setup.BaseEffect import AttackBoostEffect


class TamayurateinoOhanashi(Weapon, EventHandler):
    ID = 161
    def __init__(self, character, level=1, lv=1):
        super().__init__(character, TamayurateinoOhanashi.ID, level, lv)
        self.attack_boost = [20,25,30,35,40]

        EventBus.subscribe(EventType.BEFORE_SKILL, self)

    def handle_event(self, event):
        if event.data['character'] == self.character:
            effect = AttackBoostEffect(
                character=self.character,
                name="且住亭御咄", 
                bonus=self.attack_boost[self.lv-1],
                duration=10*60
            )
            effect.apply()

class TheCatch(Weapon, EventHandler):
    ID = 151
    def __init__(self, character, level=1, lv=1):
        super().__init__(character, TheCatch.ID, level, lv)
        self.burst_bonus = [16,20,24,28,32]
        
        # 订阅伤害加成计算前事件
        EventBus.subscribe(EventType.BEFORE_DAMAGE_BONUS, self)

    def handle_event(self, event):
        if event.data['character'] != self.character:
            return
        # 只处理元素爆发类型的伤害
        if event.data['damage'].damageType == DamageType.BURST:
            event.data['damage'].panel['伤害加成'] += self.burst_bonus[self.lv-1]
            event.data['damage'].setDamageData('渔获',{'伤害加成': self.burst_bonus[self.lv-1]})
