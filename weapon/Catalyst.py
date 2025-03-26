from setup.DamageCalculation import DamageType
from setup.Event import EventBus, EventHandler, EventType
from setup.BaseEffect import Effect
from weapon.weapon import Weapon

catalyst = ['溢彩心念']

class MorningGlowEffect(Effect,EventHandler):
    """初霞之彩效果(28%暴伤)"""
    def __init__(self, character,lv):
        super().__init__(character)
        self.bonus = [28,35,42,49,56] 
        self.duration = 900
        self.name = "初霞之彩"
        self.lv = lv
        
    def apply(self):
        # 防止重复应用
        existing = next((e for e in self.character.active_effects 
                      if isinstance(e, MorningGlowEffect)), None)
        if existing:
            existing.duration = self.duration
            return
            
        self.character.add_effect(self)
        print(f"{self.character.name}获得{self.name}效果")
        EventBus.subscribe(EventType.AFTER_PLUNGING_ATTACK, self)
        EventBus.subscribe(EventType.BEFORE_CRITICAL, self)

    def remove(self):
        self.character.remove_effect(self)
        print(f"{self.character.name}: {self.name}效果结束")
        EventBus.unsubscribe(EventType.AFTER_PLUNGING_ATTACK, self)
        EventBus.unsubscribe(EventType.BEFORE_CRITICAL, self)

    def handle_event(self, event):
        if event.data['character'] != self.character:
            return
        if event.event_type == EventType.AFTER_PLUNGING_ATTACK and event.data['is_plunging_impact']:
            self.duration = 6
        elif event.event_type == EventType.BEFORE_CRITICAL:
            if event.data['damage'].damageType == DamageType.PLUNGING:
                event.data['damage'].panel['暴击伤害']+= self.bonus[self.lv-1]
                event.data['damage'].setDamageData(self.name, {"暴击伤害": self.bonus[self.lv-1]})

class DuskGlowEffect(Effect,EventHandler):
    """苍暮之辉效果(40%暴伤)"""
    def __init__(self, character,lv):
        super().__init__(character)
        self.bonus = [40,50,60,70,80] 
        self.duration = 900 
        self.name = "苍暮之辉"
        self.lv = lv
        
    def apply(self):
        # 防止重复应用
        existing = next((e for e in self.character.active_effects 
                      if isinstance(e, DuskGlowEffect)), None)
        if existing:
            existing.duration = self.duration
            return
            
        self.character.add_effect(self)
        print(f"{self.character.name}获得{self.name}效果")
        EventBus.subscribe(EventType.AFTER_PLUNGING_ATTACK, self)
        EventBus.subscribe(EventType.BEFORE_CRITICAL, self)

    def remove(self):
        self.character.remove_effect(self)
        print(f"{self.character.name}: {self.name}效果结束")
        EventBus.unsubscribe(EventType.AFTER_PLUNGING_ATTACK, self)
        EventBus.unsubscribe(EventType.BEFORE_CRITICAL, self)

    def handle_event(self, event):
        if event.data['character'] != self.character:
            return
        if event.event_type == EventType.AFTER_PLUNGING_ATTACK and event.data['is_plunging_impact']:
            self.duration = 6
        elif event.event_type == EventType.BEFORE_CRITICAL:
            if event.data['damage'].damageType == DamageType.PLUNGING:
                event.data['damage'].panel['暴击伤害']+= self.bonus[self.lv-1]
                event.data['damage'].setDamageData(self.name, {"暴击伤害": self.bonus[self.lv-1]})

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