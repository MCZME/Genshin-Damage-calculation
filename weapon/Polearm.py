from setup.DamageCalculation import DamageType
from setup.Tool import summon_energy
from weapon.weapon import Weapon
from setup.Event import EventBus, EventType, EventHandler
from setup.BaseEffect import AttackBoostEffect

polearm = ['且住亭御咄','渔获','沙中伟贤的对答']

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
        self.critical_bonus = [6,7.5,9,10.5,12]
        
        # 订阅伤害加成计算前事件
        EventBus.subscribe(EventType.BEFORE_DAMAGE_BONUS, self)
        EventBus.subscribe(EventType.BEFORE_CRITICAL, self)

    def handle_event(self, event):
        if event.data['character'] != self.character:
            return
        # 只处理元素爆发类型的伤害
        if event.event_type == EventType.BEFORE_DAMAGE_BONUS and event.data['damage'].damageType == DamageType.BURST:
            event.data['damage'].panel['伤害加成'] += self.burst_bonus[self.lv-1]
            event.data['damage'].setDamageData("渔获_伤害加成", self.burst_bonus[self.lv-1])
        elif event.event_type == EventType.BEFORE_CRITICAL and event.data['damage'].damageType == DamageType.BURST:
            event.data['damage'].panel['暴击率'] += self.critical_bonus[self.lv-1]
            event.data['damage'].setDamageData("渔获_暴击率", self.critical_bonus[self.lv-1])

class DialoguesOfTheDesertSages(Weapon, EventHandler):
    ID = 157
    def __init__(self, character, level=1, lv=1):
        super().__init__(character, DialoguesOfTheDesertSages.ID, level, lv)
        self.energy_restore = [8, 10, 12, 14, 16]
        self.last_trigger_frame = -600  # 初始化为-600确保第一次可以触发
        
        EventBus.subscribe(EventType.AFTER_HEAL, self)

    def handle_event(self, event):
        if event.data['healing'].source != self.character:
            return
            
        current_frame = event.frame
        if current_frame - self.last_trigger_frame < 600:  # 10秒=600帧
            return
            
        # 触发能量恢复
        summon_energy(1,self.character,('无',self.energy_restore[self.lv-1]),True,True)
        
        self.last_trigger_frame = current_frame
