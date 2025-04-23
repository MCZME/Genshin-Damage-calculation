import random
from core.Logger import get_emulation_logger
from core.Team import Team
from core.effect.WeaponEffect import DuskGlowEffect, MorningGlowEffect, TEFchargedBoostEffect
from core.Event import EventBus, EventHandler, EventType
from core.effect.BaseEffect import AttackBoostEffect
import core.Tool as T
from weapon.weapon import Weapon

catalyst = ['溢彩心念','讨龙英杰谭','万世流涌大典','祭礼残章','千夜浮梦']

class VividNotions(Weapon, EventHandler):
    ID = 215
    def __init__(self, character, level=1, lv=1):
        super().__init__(character, VividNotions.ID, level, lv)
        self.character.attributePanel['攻击力%'] += [28,35,42,49,56][lv-1]
        
        # 效果状态
        self.morning_effect = MorningGlowEffect(self.character,lv)  # 初霞之彩
        self.dusk_effect = DuskGlowEffect(self.character,lv)       # 苍暮之辉
        self.remove_timer = 0       # 效果移除计时器
        
        # 订阅事件
        EventBus.subscribe(EventType.BEFORE_SKILL, self)
        EventBus.subscribe(EventType.BEFORE_BURST, self)
        EventBus.subscribe(EventType.BEFORE_PLUNGING_ATTACK, self)

    def handle_event(self, event):
        if event.data['character'] != self.character:
            return
            
        # 元素战技/爆发触发苍暮之辉
        if event.event_type in (EventType.BEFORE_SKILL, EventType.BEFORE_BURST):
            self.dusk_effect.duration = 900  # 重置持续时间
            self.dusk_effect.apply()  
        # 下落攻击触发初霞之彩
        elif event.event_type == EventType.BEFORE_PLUNGING_ATTACK:
            self.morning_effect.duration = 900  # 重置持续时间
            self.morning_effect.apply() 

class ThrillingTalesOfDragonSlayers(Weapon, EventHandler):
    ID = 174
    def __init__(self, character, level=1, lv=1):
        super().__init__(character, ThrillingTalesOfDragonSlayers.ID, level, lv)
        self.last_trigger_time = -1200 
        self.attack_boost = [24,30,36,42,48]
       

    def skill(self):
        EventBus.subscribe(EventType.AFTER_CHARACTER_SWITCH, self)

    def handle_event(self, event):
        current_time = event.frame
        if current_time - self.last_trigger_time >= 20*60:
            if event.data['old_character'] == self.character:
                effect = AttackBoostEffect(self.character,event.data['new_character'], "讨龙英杰谭", self.attack_boost[self.lv-1], 10*60)
                effect.apply()
                self.last_trigger_time = current_time

class TomeOfTheEternalFlow(Weapon,EventHandler):
    ID = 210
    def __init__(self, character, level=1, lv=1):
        super().__init__(character, TomeOfTheEternalFlow.ID, level, lv)

    def skill(self):
        self.character.attributePanel['生命值%'] += 16
        EventBus.subscribe(EventType.AFTER_HEALTH_CHANGE, self)

    def handle_event(self, event):
        if event.data['character'] != self.character:
            return
        if event.event_type == EventType.AFTER_HEALTH_CHANGE and event.data['amount'] != 0:
            TEFchargedBoostEffect(self.character).apply()

class SacrificialFragments(Weapon,EventHandler):
    ID = 181
    def __init__(self, character, level=1, lv=1):
        super().__init__(character, SacrificialFragments.ID, level, lv)
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

class AThousandFloatingDreams(Weapon):
    ID =207
    def __init__(self, character, level=1, lv=1):
        super().__init__(character, AThousandFloatingDreams.ID, level, lv)
        self.same = 0
        self.different = 0
        self.damage_bonus = [10,14,18,22,26]
        self.em_bonus_0 = [32,40,48,56,64]
        self.em_bonus_1 = [40,42,44,46,48]
    
    def getElementNum(self):
        self.same = 0
        self.different = 0
        for c in Team.team:
            if c.element != self.character.element:
                self.different += 1
            else:
                self.same += 1

    def applyEffect(self):
        if self.same != 0:
            self.character.attributePanel['元素精通'] += self.em_bonus_0[self.lv-1] * self.same
        if self.different != 0:
            self.character.attributePanel[self.character.element + '元素伤害加成'] += self.damage_bonus[self.lv-1] * self.different

    def removeEffect(self):
        if self.same != 0:
            self.character.attributePanel['元素精通'] -= self.em_bonus_0[self.lv-1] * self.same
        if self.different != 0:
            self.character.attributePanel[self.character.element + '伤害加成'] -= self.damage_bonus[self.lv-1] * self.different

    def update(self, target):
        if T.GetCurrentTime() % 60 == 1:
            self.removeEffect
            self.getElementNum()
            self.applyEffect()
