from core.calculation.DamageCalculation import DamageType
from core.Tool import summon_energy
from weapon.weapon import Weapon
from core.Event import EventBus, EventType, EventHandler
from core.effect.BaseEffect import AttackBoostEffect


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
                current_character=self.character,
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
        summon_energy(1,self.character,('无',self.energy_restore[self.lv-1]),True,True,0)
        
        self.last_trigger_frame = current_frame

class SymphonistOfScents(Weapon, EventHandler):
    ID = 217
    def __init__(self, character, level=1, lv=1):
        super().__init__(character, SymphonistOfScents.ID, level, lv)
        self.atk_boost_1 = [12,15,18,21,24]
        self.atk_boost_2 = [32,40,48,56,64]
        self.is_applied = False

    def skill(self):
        self.character.attributePanel['攻击力%'] += self.atk_boost_1[self.lv-1]

        EventBus.subscribe(EventType.AFTER_HEAL, self)

    def handle_event(self, event):
        if event.data['healing'].source is not self.character:
            return
        
        AttackBoostEffect(
            character=self.character,
            current_character=event.data['healing'].source,
            name="香韵奏者",
            bonus=self.atk_boost_2[self.lv-1],
            duration=3*60
        ).apply()
        AttackBoostEffect(
            character=self.character,
            current_character=event.data['healing'].target,
            name="香韵奏者",
            bonus=self.atk_boost_2[self.lv-1],
            duration=3*60
        ).apply()

    def update(self, target):
        if not self.is_applied and not self.character.on_field:
            self.character.attributePanel['攻击力%'] += self.atk_boost_1[self.lv-1]
            self.is_applied = True
        elif self.is_applied and self.character.on_field:
            self.character.attributePanel['攻击力%'] -= self.atk_boost_1[self.lv-1]
            self.is_applied = False

polearm = {
    '香韵奏者':SymphonistOfScents,
    '且住亭御咄':TamayurateinoOhanashi,
    '「渔获」':TheCatch,
    '沙中伟贤的对答':DialoguesOfTheDesertSages,
}
