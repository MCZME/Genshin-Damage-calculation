from core.calculation.DamageCalculation import DamageType
from core.effect.BaseEffect import CritRateBoostEffect, Effect, ElementalDamageBoostEffect
from core.Event import EventBus, EventHandler, EventType
from core.Logger import get_emulation_logger
from core.team import Team


class CinderCityEffect(ElementalDamageBoostEffect):
    """烬城勇者绘卷效果"""
    def __init__(self, character,current_character,element_type):
        super().__init__(character, current_character,'烬城勇者绘卷', element_type, 12, 12*60)
        self.stacks = {}
        self.nightsoul_stacks = {}
        self.nightsoul_duration = 20*60
        self.nightsoul_bonus = 28

    def apply(self,element_type):
        self.is_active = True
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
                        existing.nightsoul_stacks[i] = self.nightsoul_duration
                    else:
                        existing.apply_nightsoul(i)
            return
        for element in self.element_type:
            if element == '冻':
                element = '冰'
            elif element == '激':
                element = '草'
            
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
        self.is_active = False
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
        
        self.msg = f"""<p><span style="color: #faf8f0; font-size: 14pt;">{self.current_character.name} - {self.name}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">获得{" ".join(k for k in self.stacks.keys())}元素伤害加成</span></p>
        <p><span style="color: #faf8f0; font-size: 12pt;">夜魂：获得{" ".join(k for k in self.nightsoul_stacks.keys())}元素伤害加成</span></p>
        """

class ThirstEffect(Effect):
    """渴盼效果 - 记录治疗量"""
    def __init__(self, character):
        super().__init__(character, 6 * 60)  # 6秒持续时间
        self.name = "渴盼效果"
        self.heal_amount = 0
        self.max_amount = 15000
        
    def apply(self):
        super().apply()
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
        self.msg = f"""<p><span style="color: #faf8f0; font-size: 14pt;">{self.character.name} - {self.name}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">记录治疗量</span></p>
        <p><span style="color: #faf8f0; font-size: 12pt;">当前治疗量:{amount:.2f}</span></p>
        """
        
    def remove(self):
        # 渴盼结束时创建浪潮效果
        if self.heal_amount > 0:
            WaveEffect(self.character, self.heal_amount).apply()
        super().remove()
        print(f"{self.character.name}: {self.name}结束")

class WaveEffect(Effect):
    """彼时的浪潮效果 - 基于治疗量提升伤害"""
    def __init__(self, character, heal_amount):
        super().__init__(character, 10 * 60)  # 10秒持续时间
        self.name = "彼时的浪潮"
        self.bonus = heal_amount * 0.08  # 8%治疗量转化为伤害加成
        self.max_hits = 5
        self.hit_count = 0
        self.msg = f"""<p><span style="color: #faf8f0; font-size: 14pt;">{self.character.name} - {self.name}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">基于治疗量提升伤害</span></p>
        """
        
    def apply(self):
        super().apply()
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
        super().remove()
        EventBus.unsubscribe(EventType.BEFORE_FIXED_DAMAGE, self)

class MarechausseeHunterEffect(CritRateBoostEffect):
    def __init__(self, character):
        super().__init__(character, '逐影猎人', 12, 5 * 60)
        self.name = "逐影猎人"
        self.stack = 0
        self.max_stack = 3

    def apply(self):
        self.is_active = True
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
        self.msg = f"""
        <p><span style="color: #faf8f0; font-size: 14pt;">{self.character.name} - {self.name}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">获得{self.stack} * 12 暴击率</span></p>
        """
        self.current_character.attributePanel[self.attribute_name] += self.bonus * self.stack

    def removeEffect(self):
        self.current_character.attributePanel[self.attribute_name] -= self.bonus * self.stack

    def remove(self):
        self.is_active = False
        self.removeEffect()
        get_emulation_logger().log_effect(f"🗡️ {self.current_character.name}失去逐影猎人效果")

class FlowerOfParadiseLostEffect(Effect):
    def __init__(self, character):
        super().__init__(character, 10 * 60)
        self.name = '乐园遗落之花'
        self.stack = 0
        self.msg = f"""<p><span style="color: #faf8f0; font-size: 14pt;">{self.character.name} - {self.name}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">装备者绽放、超绽放、烈绽放反应造成的伤害提升{self.stack * 15}%</span></p>
        """

    def apply(self):
        super().apply()
        FlowerOfParadiseLost = next((e for e in self.character.active_effects
                                     if isinstance(e, FlowerOfParadiseLostEffect)), None)
        if FlowerOfParadiseLost:
            FlowerOfParadiseLost.removeEffect()
            FlowerOfParadiseLost.stack = min(4, FlowerOfParadiseLost.stack + 1)
            FlowerOfParadiseLost.setEffect()
            FlowerOfParadiseLost.duration = self.duration
            return
        self.character.add_effect(self)
        self.stack = 1
        self.setEffect()
        get_emulation_logger().log_effect(f"🌹 {self.current_character.name}获得乐园遗落之花效果")

    def setEffect(self):
        self.msg = f"""<p><span style="color: #faf8f0; font-size: 14pt;">{self.character.name} - {self.name}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">装备者绽放、超绽放、烈绽放反应造成的伤害提升{self.stack * 25}%</span></p>
        """
        self.current_character.attributePanel['反应系数提高']['绽放'] += self.stack * 25
        self.current_character.attributePanel['反应系数提高']['超绽放'] += self.stack * 25
        self.current_character.attributePanel['反应系数提高']['烈绽放'] += self.stack * 25

    def removeEffect(self):
        self.current_character.attributePanel['反应系数提高']['绽放'] -= self.stack * 25
        self.current_character.attributePanel['反应系数提高']['超绽放'] -= self.stack * 25
        self.current_character.attributePanel['反应系数提高']['烈绽放'] -= self.stack * 25

    def remove(self):
        super().remove()
        self.removeEffect()

class LuminescenceEffect(Effect, EventHandler):
    def __init__(self, character, damage_type,stack):
        super().__init__(character, 6*60)
        self.name = '永照的流辉'
        self.stack = stack
        self.stack_time = {damage_type:6*60}
        self.msg = f"""<p><span style="color: #faf8f0; font-size: 14pt;">{self.character.name} - {self.name}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">{self.stack}层永照的流辉，下落攻击造成的伤害提升{self.stack * 15}%</span></p>
        """

    def apply(self):
        super().apply()
        Luminescence = next((e for e in self.character.active_effects
                             if isinstance(e, LuminescenceEffect)), None)
        if Luminescence:
            Luminescence.stack = min(5,self.stack + Luminescence.stack)
            Luminescence.stack_time.update(self.stack_time)
            Luminescence.msg = f"""<p><span style="color: #faf8f0; font-size: 14pt;">{Luminescence.character.name} - {Luminescence.name}</span></p>
            <p><span style="color: #c0e4e6; font-size: 12pt;">{Luminescence.stack}层永照的流辉，下落攻击造成的伤害提升{Luminescence.stack * 15}%</span></p>
            """
            return
        
        EventBus.subscribe(EventType.BEFORE_DAMAGE_BONUS,self)
        self.character.add_effect(self)
        get_emulation_logger().log_effect(f"🌟 {self.character.name}获得永照的流辉效果")

    def remove(self):
        super().remove()
        EventBus.unsubscribe(EventType.BEFORE_DAMAGE_BONUS,self)
        get_emulation_logger().log_effect(f"🌟 {self.character.name}失去永照的流辉效果")

    def update(self, target):
        romove = []
        for i in self.stack_time.keys():
            if self.stack_time[i] > 0:
                self.stack_time[i] -= 1
                if self.stack_time[i] == 0:
                    romove.append(i)
        for i in romove:
            if i == DamageType.PLUNGING:
                self.stack -= 1
            else:
                self.stack -= 2
            self.msg = f"""<p><span style="color: #faf8f0; font-size: 14pt;">{self.character.name} - {self.name}</span></p>
            <p><span style="color: #c0e4e6; font-size: 12pt;">{self.stack}层永照的流辉，下落攻击造成的伤害提升{self.stack * 15}%</span></p>
            """
            self.stack_time.pop(i)

        if len(self.stack_time) == 0:
            self.remove()

    def handle_event(self, event):
        if event.event_type == EventType.BEFORE_DAMAGE_BONUS and event.data['character'] == self.character:
            if event.data['damage'].damageType == DamageType.PLUNGING:
                event.data['damage'].panel['伤害加成'] += 15 * self.stack
                event.data['damage'].setDamageData('永照的流辉-下落攻击伤害加成', 15 * self.stack)
