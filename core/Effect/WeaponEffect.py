from core.calculation.DamageCalculation import DamageType
from core.effect.BaseEffect import Effect, HealthBoostEffect
from core.Event import EventBus, EventHandler, EventType
from core.Logger import get_emulation_logger
from core.Tool import GetCurrentTime, summon_energy
from core.team import Team


class STWHealthBoostEffect(HealthBoostEffect):
    def __init__(self, character):
        super().__init__(character, character, '静水流涌之辉_生命值', 14, 6*60)
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
        self.msg = f"""
        <p><span style="color: #faf8f0; font-size: 14pt;">{self.character.name} - {self.name}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">获得{self.stack}*{self.bonus}%生命值</span></p>
        """

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
                    summon_energy(1, self.character,('无',8),True,True,0)
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

class RongHuaZhiGeEffect(Effect):
    """荣花之歌效果"""
    def __init__(self, character, lv):
        super().__init__(character, 6*60)
        self.name = "荣花之歌"
        self.lv = lv
        self.defense_bonus = [8,10,12,14,16]
        self.damage_bonus = [10,12.5,15,17.5,20]
        self.stack = 0
        self.last_trigger = 0
        self.interval = 0.1*60  # 0.1秒冷却

    def apply(self):
        super().apply()
        existing = next((e for e in self.character.active_effects 
                      if isinstance(e, RongHuaZhiGeEffect)), None)
        if existing:
            if GetCurrentTime() - existing.last_trigger > self.interval:
                if existing.stack < 2:
                    existing.removeEffect()
                    existing.stack += 1
                    existing.setEffect()
                existing.last_trigger = GetCurrentTime()
                existing.duration = self.duration
                
                # 检查是否达到2层并触发队伍效果
                if existing.stack == 2:
                    for c in Team.team:
                        RongHuaZhiGeTeamEffect(self.character, c, self.lv).apply()
            return
            
        self.character.add_effect(self)
        self.stack = 1
        self.setEffect()
        self.last_trigger = GetCurrentTime()
        get_emulation_logger().log_effect(f"{self.character.name}获得{self.name}效果(层数:{self.stack})")

    def setEffect(self):
        self.character.attributePanel['防御力%'] += self.defense_bonus[self.lv -1] * self.stack
        for element in ['水', '火', '风', '雷', '冰', '岩']:
            self.character.attributePanel[f'{element}元素伤害加成'] += self.damage_bonus[self.lv -1] * self.stack

    def removeEffect(self):
        self.character.attributePanel['防御力%'] -= self.defense_bonus[self.lv -1] * self.stack
        for element in ['水', '火', '风', '雷', '冰', '岩']:
            self.character.attributePanel[f'{element}元素伤害加成'] -= self.damage_bonus[self.lv -1] * self.stack

    def remove(self):
        super().remove()
        self.removeEffect()
        get_emulation_logger().log_effect(f"{self.character.name}: {self.name}效果结束")

class RongHuaZhiGeTeamEffect(Effect):
    """荣花之歌队伍效果"""
    def __init__(self, character, current_character, lv):
        super().__init__(character, 15*60)
        self.name = "荣花之歌-队伍"
        self.lv = lv
        self.bonus_per_1000 = [8,10,12,14,16]
        self.max_bonus = [25.6,32,38.4,44.8,51.2]
        self.current_character = current_character
        self.defense = (self.character.attributePanel['防御力'] * 
                   (1 + self.character.attributePanel['防御力%'] / 100) + 
                   self.character.attributePanel['固定防御力'])

    def apply(self):
        super().apply()
        existing = next((e for e in self.current_character.active_effects 
                      if isinstance(e, RongHuaZhiGeTeamEffect)), None)
        if existing:
            existing.duration = self.duration
            return

        self.current_character.add_effect(self)
        for element in ['水', '火', '风', '雷', '冰', '岩']:
            self.current_character.attributePanel[f'{element}元素伤害加成'] += min((self.defense/1000)*self.bonus_per_1000[self.lv -1], 
                                                                             self.max_bonus[self.lv -1])
        get_emulation_logger().log_effect(f"{self.current_character.name}获得{self.name}效果")

    def remove(self):
        super().remove()
        for element in ['水', '火', '风', '雷', '冰', '岩']:
            self.current_character.attributePanel[f'{element}元素伤害加成'] -= min((self.defense/1000)*self.bonus_per_1000[self.lv -1], 
                                                                             self.max_bonus[self.lv -1])
        get_emulation_logger().log_effect(f"{self.current_character.name}: {self.name}效果结束")

class AzurelightEffect(Effect):
    def __init__(self, character, lv):
        super().__init__(character, 12*60)
        self.name = "苍耀"
        self.is_apply_energy = False
        self.lv = lv
        self.atk_bomus = [24,30,36,42,48]
        self.cick_bonus = [40,50,60,70,80]
        self.msg = f"""施放元素战技后的12秒内，攻击力提升{self.atk_bomus[self.lv -1]}%。持续期间，装备者的元素能量为0时，
        攻击力还会提升{self.atk_bomus[self.lv -1]}%，且暴击伤害提升{self.cick_bonus[self.lv -1]}%"""

    def apply(self):
        existing = next((e for e in self.character.active_effects if e.name == self.name),None)
        if existing:
            existing.duration = self.duration
            return
        
        super().apply()
        self.character.add_effect(self)
        self.character.attributePanel['攻击力%'] += self.atk_bomus[self.lv -1]
        if self.character.elemental_energy.elemental_energy[1] == 0:
            self.character.attributePanel['攻击力%'] += self.atk_bomus[self.lv -1]
            self.character.attributePanel['暴击伤害'] += self.cick_bonus[self.lv -1]
            self.is_apply_energy = True
        get_emulation_logger().log_effect(f"{self.character.name}获得{self.name}效果")

    def remove(self):
        super().remove()
        self.character.attributePanel['攻击力%'] -= self.atk_bomus[self.lv -1]
        if self.is_apply_energy:
            self.character.attributePanel['攻击力%'] -= self.atk_bomus[self.lv -1]
            self.character.attributePanel['暴击伤害'] -= self.cick_bonus[self.lv -1]
