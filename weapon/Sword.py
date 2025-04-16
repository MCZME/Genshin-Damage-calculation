from core.Effect.BaseEffect import DefenseBoostEffect, EnergyRechargeBoostEffect
from core.Calculation.DamageCalculation import DamageType
from core.Effect.WeaponEffect import FreedomSwornEffect, STWElementSkillBoostEffect, STWHealthBoostEffect
from core.Event import EventBus, EventHandler, EventType
from core.Team import Team
import core.Tool as T
from weapon.weapon import Weapon


sword = ['息燧之笛','风鹰剑','灰河渡手','静水流涌之辉','苍古自由之誓']

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

class FleuveCendreFerryman(Weapon,EventHandler):
    ID = 33
    def __init__(self, character, level=1, lv=1):
        super().__init__(character, FleuveCendreFerryman.ID, level, lv)
        self.critical_rate = [8,10,12,14,16]
        self.engergy_recharge = [16,20,24,28,32]

    def skill(self):
        EventBus.subscribe(EventType.AFTER_SKILL, self)
        EventBus.subscribe(EventType.BEFORE_CRITICAL, self)

    def handle_event(self, event):
        if event.event_type == EventType.AFTER_SKILL:
            if event.data['character'] == self.character:
                EnergyRechargeBoostEffect(self.character, '灰河渡手', self.engergy_recharge[self.lv - 1], 5*60).apply()
        if event.event_type == EventType.BEFORE_CRITICAL:
            if event.data['character'] == self.character and event.data['damage'].damageType == DamageType.SKILL:
                event.data['damage'].panel['暴击率'] += self.critical_rate[self.lv - 1]
                event.data['damage'].setDamageData(self.name,self.critical_rate[self.lv - 1])

class SplendorOfTranquilWaters(Weapon, EventHandler):
    ID = 49
    def __init__(self, character, level=1, lv=1):
        super().__init__(character, SplendorOfTranquilWaters.ID, level, lv)
        self.skill_dmg_stacks = 0
        self.hp_stacks = 0
        self.last_skill_trigger = 0
        self.last_hp_trigger = 0

    def skill(self):
        EventBus.subscribe(EventType.AFTER_HEALTH_CHANGE, self)

    def handle_event(self, event):
        if event.event_type == EventType.AFTER_HEALTH_CHANGE and event.data['amount'] != 0:
            if event.data['character'] == self.character:
                STWElementSkillBoostEffect(self.character).apply()
            else:
                STWHealthBoostEffect(self.character).apply()
        
class FreedomSworn(Weapon):
    ID = 42
    def __init__(self, character, level=1, lv=1):
        super().__init__(character, FreedomSworn.ID, level, lv)
        self.last_tigger_time = 0
        self.stacks = 0
        self.lasr_effect_time = -20*60

    def skill(self):
        self.character.attributePanel['伤害加成'] += 10
        EventBus.subscribe(EventType.AFTER_ELEMENTAL_REACTION, self)

    def handle_event(self, event):
        if event.event_type == EventType.AFTER_ELEMENTAL_REACTION:
            if event.data['elementalReaction'].source == self.character:
                if T.GetCurrentTime() - self.last_tigger_time > 0.5*60 and T.GetCurrentTime() - self.lasr_effect_time > 20*60:
                    self.stacks += 1
                    self.last_tigger_time = T.GetCurrentTime()
                    if self.stacks == 2:
                        for c in Team.team:
                            FreedomSwornEffect(self.character,c,self.lv).apply()
                        self.stacks = 0
                        self.lasr_effect_time = T.GetCurrentTime()