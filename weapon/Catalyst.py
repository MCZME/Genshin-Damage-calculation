from core.effect.WeaponEffect import DuskGlowEffect, MorningGlowEffect, TEFchargedBoostEffect
from core.Event import EventBus, EventHandler, EventType
from core.effect.BaseEffect import AttackBoostEffect
from weapon.weapon import Weapon

catalyst = ['溢彩心念','讨龙英杰谭','万世流涌大典']

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