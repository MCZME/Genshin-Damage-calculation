from core.Calculation.DamageCalculation import DamageType
from core.Effect.BaseEffect import Effect, HealthBoostEffect
from core.Event import EventBus, EventHandler, EventType
from core.Logger import get_emulation_logger
from core.Tool import GetCurrentTime, summon_energy


class STWHealthBoostEffect(HealthBoostEffect):
    def __init__(self, character):
        super().__init__(character, '静水流涌之辉_生命值', 14, 6*60)
        self.stack = 0
        self.last_trigger = 0
        self.interval = 0.2*60

    def apply(self):
        super().apply()
        healthBoost = next((e for e in self.character.active_effects if isinstance(e, STWHealthBoostEffect)), None)
        if healthBoost:
            if GetCurrentTime() - healthBoost.last_trigger > self.interval:
                if healthBoost.stack < 2:
                    healthBoost.removeEffect()
                    healthBoost.stack += 1
                    healthBoost.setEffect()
                healthBoost.last_trigger = GetCurrentTime()
                healthBoost.duration = self.duration
            return
        self.character.add_effect(self)
        self.stack = 1
        self.setEffect()
        get_emulation_logger().log_effect(f"{self.character.name}获得{self.name}效果")

    def setEffect(self):
        self.character.attributePanel['生命值%'] += self.bonus * self.stack

    def removeEffect(self):
        self.character.attributePanel['生命值%'] -= self.bonus * self.stack

    def remove(self):
        super().remove()
        self.removeEffect()
        get_emulation_logger().log_effect(f"{self.character.name}: {self.name}效果结束")

class STWElementSkillBoostEffect(Effect,EventHandler):
    def __init__(self, character):
        super().__init__(character, 6*60)
        self.name = '静水流涌之辉_元素战技'
        self.bonus = 8
        self.stack = 0
        self.last_trigger = 0
        self.interval = 0.2*60

    def apply(self):
        super().apply()
        existing = next((e for e in self.character.active_effects if isinstance(e, STWElementSkillBoostEffect)), None)
        if existing:
            if GetCurrentTime() - existing.last_trigger > self.interval:
                if existing.stack < 3:
                    existing.stack += 1
                existing.last_trigger = GetCurrentTime()
            existing.duration = self.duration
            return
        self.character.add_effect(self)
        EventBus.subscribe(EventType.BEFORE_DAMAGE_BONUS,self)
        get_emulation_logger().log_effect(f"{self.character.name}获得{self.name}效果")

    def remove(self):
        super().remove()
        EventBus.unsubscribe(EventType.BEFORE_DAMAGE_BONUS,self)
        get_emulation_logger().log_effect(f"{self.character.name}: {self.name}效果结束")

    def handle_event(self, event):
        if event.event_type == EventType.BEFORE_DAMAGE_BONUS:
            if event.data['character'] == self.character and event.data['damage'].damageType.value == '元素战技':
                event.data['damage'].panel['伤害加成'] += self.bonus * self.stack
                event.data['damage'].setDamageData(self.name, self.bonus * self.stack)

class MorningGlowEffect(Effect,EventHandler):
    """初霞之彩效果(28%暴伤)"""
    def __init__(self, character,lv):
        super().__init__(character,duration=900)
        self.bonus = [28,35,42,49,56] 
        self.name = "初霞之彩"
        self.lv = lv
        
    def apply(self):
        super().apply()
        existing = next((e for e in self.character.active_effects 
                      if isinstance(e, MorningGlowEffect)), None)
        if existing:
            existing.duration = self.duration
            return
            
        self.character.add_effect(self)
        print(f"{self.character.name}获得{self.name}效果")
        EventBus.subscribe(EventType.AFTER_PLUNGING_ATTACK, self)
        EventBus.subscribe(EventType.BEFORE_CRITICAL_BRACKET, self)

    def remove(self):
        super().remove()
        print(f"{self.character.name}: {self.name}效果结束")
        EventBus.unsubscribe(EventType.AFTER_PLUNGING_ATTACK, self)
        EventBus.unsubscribe(EventType.BEFORE_CRITICAL_BRACKET, self)

    def handle_event(self, event):
        if event.data['character'] != self.character:
            return
        if event.event_type == EventType.AFTER_PLUNGING_ATTACK and event.data['is_plunging_impact']:
            self.duration = 43
        elif event.event_type == EventType.BEFORE_CRITICAL_BRACKET:
            if event.data['damage'].damageType == DamageType.PLUNGING:
                event.data['damage'].panel['暴击伤害']+= self.bonus[self.lv-1]
                event.data['damage'].setDamageData(self.name, {"暴击伤害": self.bonus[self.lv-1]})

class DuskGlowEffect(Effect,EventHandler):
    """苍暮之辉效果(40%暴伤)"""
    def __init__(self, character,lv):
        super().__init__(character,duration=900)
        self.bonus = [40,50,60,70,80] 
        self.name = "苍暮之辉"
        self.lv = lv
        
    def apply(self):
        super().apply()
        existing = next((e for e in self.character.active_effects 
                      if isinstance(e, DuskGlowEffect)), None)
        if existing:
            existing.duration = self.duration
            return
            
        self.character.add_effect(self)
        print(f"{self.character.name}获得{self.name}效果")
        EventBus.subscribe(EventType.AFTER_PLUNGING_ATTACK, self)
        EventBus.subscribe(EventType.BEFORE_CRITICAL_BRACKET, self)

    def remove(self):
        super().remove()
        print(f"{self.character.name}: {self.name}效果结束")
        EventBus.unsubscribe(EventType.AFTER_PLUNGING_ATTACK, self)
        EventBus.unsubscribe(EventType.BEFORE_CRITICAL_BRACKET, self)

    def handle_event(self, event):
        if event.data['character'] != self.character:
            return
        if event.event_type == EventType.AFTER_PLUNGING_ATTACK and event.data['is_plunging_impact']:
            self.duration = 6
        elif event.event_type == EventType.BEFORE_CRITICAL_BRACKET:
            if event.data['damage'].damageType == DamageType.PLUNGING:
                event.data['damage'].panel['暴击伤害']+= self.bonus[self.lv-1]
                event.data['damage'].setDamageData(self.name, {"暴击伤害": self.bonus[self.lv-1]})

class TEFchargedBoostEffect(Effect,EventHandler):
    def __init__(self, character):
        super().__init__(character, 4*60)
        self.name = "万世流涌大典_重击提升"
        self.bonus = 14
        self.stack = 0
        self.last_tigger = 0
        self.last_erengy_trigger = 0
        self.interval = 0.3*60
        self.erengy_interval = 12*60

    def apply(self):
        super().apply()
        existing = next((e for e in self.character.active_effects 
                      if isinstance(e, TEFchargedBoostEffect)), None)
        if existing:
            if GetCurrentTime() - existing.last_tigger > existing.interval:
                if existing.stack < 3:
                    existing.stack += 1
                existing.last_tigger = GetCurrentTime()
                if existing.stack == 3 and GetCurrentTime() - existing.last_erengy_trigger > self.erengy_interval:
                    summon_energy(1, self.character,('无',8),True,True)
                    existing.last_erengy_trigger = GetCurrentTime()
            existing.duration = self.duration
            return
        self.character.add_effect(self)
        EventBus.subscribe(EventType.BEFORE_DAMAGE_BONUS,self)

    def remove(self):
        super().remove()
        EventBus.unsubscribe(EventType.BEFORE_DAMAGE_BONUS,self)

    def handle_event(self, event):
        if event.data['character'] != self.character:
            return
        if event.event_type == EventType.BEFORE_DAMAGE_BONUS:
            if event.data['damage'].damageType.value == '重击':
                event.data['damage'].panel['伤害加成']+= self.bonus*self.stack
                event.data['damage'].setDamageData(self.name, self.bonus*self.stack)

class FreedomSwornEffect(Effect,EventHandler):
    def __init__(self, character, current_character, lv):
        super().__init__(character,duration=12*60)
        self.bonus = [16,20,24,28,32]
        self.attack_bonus = [20,25,30,35,40]
        self.name = "苍古自由之誓"
        self.lv = lv
        self.current_character = current_character

    def apply(self):
        super().apply()
        existing = next((e for e in self.current_character.active_effects 
                      if isinstance(e, FreedomSwornEffect)), None)
        if existing:
            return
        self.current_character.add_effect(self)
        self.current_character.attributePanel['攻击力%'] += self.attack_bonus[self.lv-1]
        get_emulation_logger().log_effect(f'{self.current_character.name}获得{self.name}效果')
        EventBus.subscribe(EventType.BEFORE_DAMAGE_BONUS,self)

    def remove(self):
        super().remove()
        self.current_character.attributePanel['攻击力%'] -= self.attack_bonus[self.lv-1]
        get_emulation_logger().log_effect(f'{self.current_character.name}: {self.name}效果结束')

    def handle_event(self, event):
        if event.data['character'] != self.current_character:
            return
        if (event.event_type == EventType.BEFORE_DAMAGE_BONUS and
            event.data['damage'].damageType in [DamageType.NORMAL,DamageType.CHARGED,DamageType.PLUNGING]):
            event.data['damage'].panel['伤害加成']+= self.bonus[self.lv-1]
            event.data['damage'].setDamageData(self.name, self.bonus[self.lv-1])
