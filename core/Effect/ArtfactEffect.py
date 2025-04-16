from core.Calculation.DamageCalculation import DamageType
from core.Effect.BaseEffect import CritRateBoostEffect, Effect, ElementalDamageBoostEffect
from core.Event import EventBus, EventHandler, EventType
from core.Logger import get_emulation_logger
from core.Team import Team


class CinderCityEffect(ElementalDamageBoostEffect):
    """烬城勇者绘卷效果"""
    def __init__(self, character,current_character,element_type):
        super().__init__(character, '烬城勇者绘卷', element_type, 12, 12*60)
        self.stacks = {}
        self.nightsoul_stacks = {}
        self.nightsoul_duration = 20*60
        self.nightsoul_bonus = 28
        self.current_character = current_character

    def apply(self,element_type):
        # 防止重复应用
        existing = next((e for e in self.current_character.active_effects 
                    if isinstance(e, CinderCityEffect)), None)
        if existing:
            for i in element_type:
                if i in existing.stacks.keys():
                    existing.stacks[i] = self.duration
                else:
                    existing.apply_element(i)
                if self.character.Nightsoul_Blessing:
                    if i in existing.nightsoul_stacks.keys():
                        existing.nightsoul_stacks[i] = self.nightsoul_bonus
                    else:
                        existing.apply_nightsoul(i)
            return
        for element in self.element_type:
            self.current_character.attributePanel[element+'元素伤害加成'] += self.bonus
            self.stacks[element] = self.duration
            if self.character.Nightsoul_Blessing:
                self.current_character.attributePanel[element+'元素伤害加成'] += self.nightsoul_bonus
                self.nightsoul_stacks[element] = self.nightsoul_duration
        self.current_character.add_effect(self)
        get_emulation_logger().log_effect(f"🌋 {self.current_character.name}获得{element_type}烬城勇者绘卷效果")

    def apply_element(self,element):
        self.current_character.attributePanel[element+'元素伤害加成'] += self.bonus
        self.stacks[element] = self.duration
        get_emulation_logger().log_effect(f"🌋 {self.current_character.name}触发烬城勇者绘卷 效果")

    def apply_nightsoul(self,element):
        self.current_character.attributePanel[element+'元素伤害加成'] += self.nightsoul_bonus
        self.nightsoul_stacks[element] = self.nightsoul_duration
        get_emulation_logger().log_effect(f"🌋 {self.current_character.name}触发烬城勇者绘卷 夜魂效果")
        
    def remove(self):
        for element in self.element_type:
            self.current_character.attributePanel[element+'元素伤害加成'] -= self.bonus
        self.current_character.remove_effect(self)
        get_emulation_logger().log_effect(f"🌋 {self.current_character.name}失去{self.name}效果")

    def remove_element(self,element):
        self.current_character.attributePanel[element+'元素伤害加成'] -= self.bonus
        del self.stacks[element]
        get_emulation_logger().log_effect(f"🌋 {self.current_character.name}失去{element}烬城勇者绘卷 效果")

    def remove_nightsoul(self,element):
        self.current_character.attributePanel[element+'元素伤害加成'] -= self.nightsoul_bonus
        del self.nightsoul_stacks[element]
        get_emulation_logger().log_effect(f"🌋 {self.current_character.name}失去{element}烬城勇者绘卷 夜魂效果")

    def update(self,target):
        keys_to_remove = [elemment for elemment, time in self.stacks.items() if time <= 0]
        for elemment in keys_to_remove:
            self.remove_element(elemment)
        for elemment,time in self.stacks.items():
            self.stacks[elemment] -= 1
        keys_to_remove = [elemment for elemment, time in self.nightsoul_stacks.items() if time <= 0]
        for elemment in keys_to_remove:
            self.remove_nightsoul(elemment)
        for elemment,time in self.nightsoul_stacks.items():
            self.nightsoul_stacks[elemment] -= 1
        if sum(self.nightsoul_stacks.values()) <= 0 and sum(self.stacks.values()) <= 0:
            self.remove()

class ThirstEffect(Effect):
    """渴盼效果 - 记录治疗量"""
    def __init__(self, character):
        super().__init__(character, 6 * 60)  # 6秒持续时间
        self.name = "渴盼效果"
        self.heal_amount = 0
        self.max_amount = 15000
        
    def apply(self):
        # 防止重复应用
        existing = next((e for e in self.character.active_effects 
                        if isinstance(e, ThirstEffect)), None)
        if existing:
            existing.duration = self.duration  # 刷新持续时间
            return
            
        self.character.add_effect(self)
        print(f"{self.character.name}获得{self.name}")
        
    def add_heal(self, amount):
        """添加治疗量记录"""
        self.heal_amount = min(self.heal_amount + amount, self.max_amount)
        
    def remove(self):
        # 渴盼结束时创建浪潮效果
        if self.heal_amount > 0:
            WaveEffect(self.character, self.heal_amount).apply()
        self.character.remove_effect(self)
        print(f"{self.character.name}: {self.name}结束")

class WaveEffect(Effect):
    """彼时的浪潮效果 - 基于治疗量提升伤害"""
    def __init__(self, character, heal_amount):
        super().__init__(character, 10 * 60)  # 10秒持续时间
        self.name = "彼时的浪潮"
        self.bonus = heal_amount * 0.08  # 8%治疗量转化为伤害加成
        self.max_hits = 5
        self.hit_count = 0
        
    def apply(self):
        # 订阅固定伤害事件来计数和加成
        waveEffect = next((e for e in self.character.active_effects
                          if isinstance(e, WaveEffect)), None)
        if waveEffect:
            waveEffect.duration = self.duration  # 刷新持续时间
            return
        self.character.add_effect(self)
        EventBus.subscribe(EventType.BEFORE_FIXED_DAMAGE, self)
        
    def handle_event(self, event):
        if event.event_type == EventType.BEFORE_FIXED_DAMAGE:
            if (event.data['damage'].source in Team.team and 
                event.data['damage'].damageType in [DamageType.NORMAL, DamageType.CHARGED,
                                                   DamageType.SKILL, DamageType.BURST,
                                                   DamageType.PLUNGING]):
                # 增加固定伤害基础值
                event.data['damage'].panel['固定伤害基础值加成'] += self.bonus
                event.data['damage'].data['浪潮_固定伤害加成'] = self.bonus
                self.hit_count += 1
                if self.hit_count >= self.max_hits:
                    self.remove()
                    
    def remove(self):
        self.character.remove_effect(self)
        EventBus.unsubscribe(EventType.BEFORE_FIXED_DAMAGE, self)

class MarechausseeHunterEffect(CritRateBoostEffect):
    def __init__(self, character):
        super().__init__(character, '逐影猎人', 12, 5 * 60)
        self.name = "逐影猎人"
        self.stack = 0
        self.max_stack = 3

    def apply(self):
        MarechausseeHunter = next((e for e in self.character.active_effects
                                   if isinstance(e, MarechausseeHunterEffect)), None)
        if MarechausseeHunter:
            if MarechausseeHunter.stack < MarechausseeHunter.max_stack:
                MarechausseeHunter.removeEffect()
                MarechausseeHunter.stack += 1
                MarechausseeHunter.setEffect()
            MarechausseeHunter.duration = self.duration  # 刷新持续时间
            return
        self.character.add_effect(self)
        self.stack = 1
        self.setEffect()
        get_emulation_logger().log_effect(f"🗡️ {self.current_character.name}获得逐影猎人效果")

    def setEffect(self):
        self.current_character.attributePanel[self.attribute_name] += self.bonus * self.stack

    def removeEffect(self):
        self.current_character.attributePanel[self.attribute_name] -= self.bonus * self.stack

    def remove(self):
        self.character.remove_effect(self)
        self.removeEffect()
        get_emulation_logger().log_effect(f"🗡️ {self.current_character.name}失去逐影猎人效果")

