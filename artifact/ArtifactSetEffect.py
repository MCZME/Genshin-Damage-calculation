from character.character import Character
from setup.BaseEffect import  AttackBoostEffect, CritRateBoostEffect, Effect, ElementalDamageBoostEffect, ElementalMasteryBoostEffect
from setup.DamageCalculation import DamageType
from setup.Event import EventBus, EventHandler, EventType
from setup.Team import Team
from setup.Tool import GetCurrentTime, summon_energy
from setup.Logger import get_emulation_logger

class ArtifactEffect(EventHandler):
    def __init__(self,name):
        self.name = name

    def tow_SetEffect(self,character:Character):
        ...

    def four_SetEffect(self,character:Character):
        ...

class GladiatorFinale(ArtifactEffect):
    def __init__(self):
        super().__init__('角斗士的终幕礼')

    def tow_SetEffect(self,character):
        # 攻击力提升18%
        attributePanel = character.attributePanel
        attributePanel['攻击力%'] += 18

    def four_SetEffect(self,character):
        EventBus.subscribe(EventType.BEFORE_DAMAGE_BONUS, self)
    
    def handle_event(self, event):
        if event.event_type == EventType.BEFORE_DAMAGE_BONUS:
            if event.data['damageType'] == DamageType.NORMAL and event.source.type in ['单手剑', '双手剑','长柄武器']:
                event.data['damageBonus'] += 35

class ObsidianCodex(ArtifactEffect):
    def __init__(self):
        super().__init__('黑曜秘典')

    def tow_SetEffect(self,character):
        # 装备者处于夜魂加持状态，并且在场上时，造成的伤害提高15%。
        EventBus.subscribe(EventType.AFTER_NIGHTSOUL_BLESSING, self)
        EventBus.subscribe(EventType.BEFORE_NIGHTSOUL_BLESSING, self)

    def four_SetEffect(self,character):
        self.character = character
        EventBus.subscribe(EventType.BEFORE_NIGHT_SOUL_CHANGE, self)
        self.last_trigger_time = 0  # 记录上次触发时间

    def handle_event(self, event):
        if event.event_type == EventType.BEFORE_NIGHTSOUL_BLESSING:
            attributePanel = event.data['character'].attributePanel
            attributePanel['伤害加成'] += 15
        elif event.event_type == EventType.AFTER_NIGHTSOUL_BLESSING:
            attributePanel = event.data['character'].attributePanel
            attributePanel['伤害加成'] -= 15
        elif event.event_type == EventType.BEFORE_NIGHT_SOUL_CHANGE:
            # 检查是否是当前角色且夜魂值减少
            if (event.data['character'] == self.character and 
                event.data['amount'] < 0 and
                GetCurrentTime() - self.last_trigger_time >= 60):  # 1秒冷却
                
                # 使用CritRateBoostEffect应用暴击率提升效果
                effect = CritRateBoostEffect(self.character, '黑曜秘典', 40, 6 * 60)
                effect.apply()
                self.last_trigger_time = GetCurrentTime()

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

class ScrolloftheHeroOfCinderCity(ArtifactEffect):
    def __init__(self):
        super().__init__('烬城勇者绘卷')

    def tow_SetEffect(self,character):
        self.character = character
        EventBus.subscribe(EventType.NightsoulBurst, self)

    def four_SetEffect(self,character):
        EventBus.subscribe(EventType.AFTER_ELEMENTAL_REACTION, self)

    def handle_event(self, event):
        if event.event_type == EventType.NightsoulBurst:
            summon_energy(5, self.character, ('无', 6),True,True)
        elif event.event_type == EventType.AFTER_ELEMENTAL_REACTION:
            reaction = event.data['elementalReaction']
            if reaction.source == self.character:
                for character in Team.team:
                    effect = CinderCityEffect(self.character,character,[reaction.target_element, reaction.damage.element[0]])
                    effect.apply([reaction.target_element, reaction.damage.element[0]])

class EmblemOfSeveredFate(ArtifactEffect):
    def __init__(self):
        super().__init__('绝缘之旗印')

    def tow_SetEffect(self, character):
        # 元素充能效率提高20%
        character.attributePanel['元素充能效率'] += 20

    def four_SetEffect(self, character):
        self.character = character
        EventBus.subscribe(EventType.BEFORE_DAMAGE_BONUS, self)
    
    def handle_event(self, event):
        if event.event_type == EventType.BEFORE_DAMAGE_BONUS:
            if event.data['damage'].damageType == DamageType.BURST and event.data['damage'].source == self.character:
                # 基于元素充能效率的25%提升伤害，最多75%
                er = self.character.attributePanel['元素充能效率']
                bonus = min(er * 0.25, 75)
                event.data['damage'].panel['伤害加成'] += bonus
                event.data['damage'].data['绝缘之旗印_伤害加成'] = bonus

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

class SongOfDaysPast(ArtifactEffect):
    def __init__(self):
        super().__init__('昔时之歌')

    def tow_SetEffect(self, character):
        # 治疗加成提高15%
        character.attributePanel['治疗加成'] += 15

    def four_SetEffect(self, character):
        self.character = character
        EventBus.subscribe(EventType.AFTER_HEAL, self)
    
    def handle_event(self, event):
        if event.event_type == EventType.AFTER_HEAL and event.data['character'] == self.character:
            # 查找或创建渴盼效果
            thirst = next((e for e in self.character.active_effects 
                          if isinstance(e, ThirstEffect)), None)
            if not thirst:
                thirst = ThirstEffect(self.character)
                thirst.apply()
            # 记录治疗量
            thirst.add_heal(event.data['healing'].final_value)

class Instructor(ArtifactEffect,EventHandler):
    def __init__(self):
        super().__init__('教官')

    def tow_SetEffect(self, character):
        attributrPanel = character.attributePanel
        attributrPanel['元素精通'] += 80
    
    def four_SetEffect(self, character):
        self.character = character
        EventBus.subscribe(EventType.AFTER_ELEMENTAL_REACTION, self)

    def handle_event(self, event):
        if event.event_type == EventType.AFTER_ELEMENTAL_REACTION:
            if event.data['elementalReaction'].source == self.character:
                for c in Team.team:
                    effect = ElementalMasteryBoostEffect(self.character, '教官', 120, 8*60)
                    effect.apply(c)

class NoblesseOblige(ArtifactEffect):
    def __init__(self):
        super().__init__('昔日宗室之仪')
    
    def tow_SetEffect(self, character):
        self.character = character
        EventBus.subscribe(EventType.BEFORE_DAMAGE_BONUS, self)

    def four_SetEffect(self, character):
        EventBus.subscribe(EventType.AFTER_BURST, self)

    def handle_event(self, event):
        if event.event_type == EventType.BEFORE_DAMAGE_BONUS:
            if event.data['character'] == self.character and event.data['damage'].damageType == DamageType.BURST:
                event.data['damage'].panel['伤害加成'] += 20
                event.data['damage'].setDamageData('昔日宗室之仪-伤害加成', 20)
        if event.event_type == EventType.AFTER_BURST:
            if event.data['character'] == self.character:
                for c in Team.team:
                    effect = AttackBoostEffect(c, '昔日宗室之仪', 20, 12*60)
                    effect.apply()
                