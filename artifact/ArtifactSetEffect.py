from character.character import Character
from core.effect.ArtfactEffect import CinderCityEffect, FlowerOfParadiseLostEffect, LuminescenceEffect, MarechausseeHunterEffect, ThirstEffect
from core.effect.BaseEffect import  AttackBoostEffect, CritRateBoostEffect, ElementalMasteryBoostEffect, ResistanceDebuffEffect
from core.action.damage import DamageType
from core.event import EventBus, EventHandler, EventType, GameEvent
from core.team import Team
from core.tool import GetCurrentTime, summon_energy

class ArtifactEffect(EventHandler):
    def __init__(self,name = ''):
        self.name = name

    def tow_SetEffect(self,character:Character):
        ...

    def four_SetEffect(self,character:Character):
        ...

    def handle_event(self, event):
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
        EventBus.subscribe(EventType.AFTER_NIGHT_SOUL_CHANGE, self)
        self.last_trigger_time = 0  # 记录上次触发时间

    def handle_event(self, event):
        if event.event_type == EventType.BEFORE_NIGHTSOUL_BLESSING:
            attributePanel = event.data['character'].attributePanel
            attributePanel['伤害加成'] += 15
        elif event.event_type == EventType.AFTER_NIGHTSOUL_BLESSING:
            attributePanel = event.data['character'].attributePanel
            attributePanel['伤害加成'] -= 15
        elif event.event_type == EventType.AFTER_NIGHT_SOUL_CHANGE:
            # 检查是否是当前角色且夜魂值减少
            if (event.data['character'] == self.character and 
                event.data['amount'] < 0 and
                GetCurrentTime() - self.last_trigger_time >= 60 and
                event.cancelled == False):  # 1秒冷却
                
                # 使用CritRateBoostEffect应用暴击率提升效果
                effect = CritRateBoostEffect(self.character, '黑曜秘典', 40, 6 * 60)
                effect.apply()
                self.last_trigger_time = GetCurrentTime()

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
            summon_energy(1, self.character, ('无', 6),True,True,0)
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

class Instructor(ArtifactEffect):
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
                    effect = ElementalMasteryBoostEffect(self.character, c, '教官', 120, 8*60)
                    effect.apply()

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
                    effect = AttackBoostEffect(self.character, c, '昔日宗室之仪', 20, 12*60)
                    effect.apply()

class MarechausseeHunter(ArtifactEffect):
    def __init__(self):
        super().__init__('逐影猎人')

    def tow_SetEffect(self, character):
        self.character = character
        EventBus.subscribe(EventType.BEFORE_DAMAGE_BONUS, self)

    def four_SetEffect(self, character):
        EventBus.subscribe(EventType.AFTER_HEALTH_CHANGE, self)

    def handle_event(self, event):
        if event.event_type == EventType.BEFORE_DAMAGE_BONUS:
            if event.data['character'] == self.character and event.data['damage'].damageType in [DamageType.NORMAL, DamageType.CHARGED]:
                event.data['damage'].panel['伤害加成'] += 15
                event.data['damage'].setDamageData('逐影猎人-伤害加成', 15)
        if event.event_type == EventType.AFTER_HEALTH_CHANGE:
            if event.data['character'] == self.character:
                MarechausseeHunterEffect(self.character).apply()

class GoldenTroupe(ArtifactEffect):
    def __init__(self):
        super().__init__('黄金剧团')
        self.fourSet = False

    def tow_SetEffect(self, character):
        self.character = character
        EventBus.subscribe(EventType.BEFORE_DAMAGE_BONUS, self)
    
    def four_SetEffect(self, character):
        self.fourSet = True
        self.last_on_field_time = 999
        EventBus.subscribe(EventType.AFTER_CHARACTER_SWITCH, self)

    def handle_event(self, event):
        if event.event_type == EventType.BEFORE_DAMAGE_BONUS:
            if event.data['character'] == self.character and event.data['damage'].damageType == DamageType.SKILL:
                event.data['damage'].panel['伤害加成'] += 20
                event.data['damage'].setDamageData('黄金剧团-两件套伤害加成', 20)
                if self.fourSet:
                    event.data['damage'].panel['伤害加成'] += 25
                    event.data['damage'].setDamageData('黄金剧团-四件套伤害加成', 25)
                    if (self.character.on_field and event.frame - self.last_on_field_time < 2*60) or not self.character.on_field:
                        event.data['damage'].panel['伤害加成'] += 25
                        event.data['damage'].setDamageData('黄金剧团-四件套伤害加成-后台', 25)
        elif event.event_type == EventType.AFTER_CHARACTER_SWITCH:
            if event.data['new_character'] == self.character:
                self.last_on_field_time = event.frame

class ViridescentVenerer(ArtifactEffect):
    def __init__(self):
        super().__init__('翠绿之影')

    def tow_SetEffect(self, character):
        self.character = character
        self.character.attributePanel['风元素伤害加成'] += 15

    def four_SetEffect(self, character):
        self.character = character
        self.character.attributePanel['反应系数提高'] = {'扩散':60}
        EventBus.subscribe(EventType.BEFORE_SWIRL, self)

    def handle_event(self, event):
        if (event.event_type == EventType.BEFORE_SWIRL and 
            event.data['elementalReaction'].source == self.character and
            self.character.on_field):
            element = event.data['elementalReaction'].target_element
            effect = ResistanceDebuffEffect(self.name+f'-{element}', self.character, event.data['elementalReaction'].target, 
                                            element, 40, 10*60)
            effect.apply()

class DeepwoodMemories(ArtifactEffect):
    def __init__(self):
        super().__init__('深林的记忆')

    def tow_SetEffect(self, character):
        self.character = character
        self.character.attributePanel['草元素伤害加成'] += 15

    def four_SetEffect(self, character):
        self.character = character
        EventBus.subscribe(EventType.AFTER_DAMAGE, self)

    def handle_event(self, event):
        if event.event_type == EventType.AFTER_DAMAGE:
            if event.data['character'] == self.character and event.data['damage'].damageType in [DamageType.SKILL, DamageType.BURST]:
                ResistanceDebuffEffect('深林的记忆', self.character, event.data['damage'].target, ['草'], 30, 8*60).apply()

class FlowerOfParadiseLost(ArtifactEffect):
    def __init__(self):
        super().__init__('乐园遗落之花')
        self.last_tigger_time = 0
        self.inveral = 60

    def tow_SetEffect(self, character):
        self.character = character
        self.character.attributePanel['元素精通'] += 80

    def four_SetEffect(self, character):
        self.character = character
        self.character.attributePanel['反应系数提高'] = {'绽放':40, '超绽放':40, '烈绽放':40}
        EventBus.subscribe(EventType.AFTER_BLOOM, self)
        EventBus.subscribe(EventType.AFTER_HYPERBLOOM, self)
        EventBus.subscribe(EventType.AFTER_BURGEON, self)

    def handle_event(self, event):
        if event.event_type in [EventType.AFTER_BLOOM, EventType.AFTER_HYPERBLOOM, EventType.AFTER_BURGEON]:
            e = event.data['elementalReaction']
            if e.source == self.character and GetCurrentTime() - self.last_tigger_time > self.inveral:
                self.last_tigger_time = GetCurrentTime()
                FlowerOfParadiseLostEffect(self.character).apply()

class LongNightsOath(ArtifactEffect):
    def __init__(self):
        super().__init__('长夜之誓')
        self.last_tigger_time = -60

    def tow_SetEffect(self, character):
        self.character = character
        # 下落攻击伤害提升25%
        EventBus.subscribe(EventType.BEFORE_DAMAGE_BONUS, self)

    def four_SetEffect(self, character):
        self.character = character
        EventBus.subscribe(EventType.AFTER_DAMAGE, self)

    def handle_event(self, event):
        if event.event_type == EventType.BEFORE_DAMAGE_BONUS and event.data['character'] == self.character:
            if event.data['damage'].damageType == DamageType.PLUNGING:
                event.data['damage'].panel['伤害加成'] += 25
                event.data['damage'].setDamageData('长夜之誓-两件套伤害加成', 25)
        
        elif event.event_type == EventType.AFTER_DAMAGE:
            if event.data['character'] == self.character:
                damage_type = event.data['damage'].damageType
                if damage_type in [DamageType.PLUNGING, DamageType.CHARGED, DamageType.SKILL]:
                    current_time = event.frame
                    if current_time - self.last_tigger_time >= 60:
                        # 根据攻击类型获得不同层数
                        if damage_type == DamageType.PLUNGING:
                            effect = LuminescenceEffect(self.character, damage_type, 1)
                            effect.apply()
                        else: # CHARGED or SKILL
                            effect = LuminescenceEffect(self.character, damage_type, 2)
                            effect.apply()

class FinaleOftheDeepGalleries(ArtifactEffect):
    def __init__(self):
        super().__init__('深廊终曲')
        self.last_normal_damage_time = -6*60
        self.last_burst_damage_time = -6*60

    def tow_SetEffect(self, character):
        self.character = character
        self.character.attributePanel['冰元素伤害加成'] += 15

    def four_SetEffect(self, character):
        EventBus.subscribe(EventType.BEFORE_DAMAGE_BONUS, self)

    def handle_event(self, event:GameEvent):
        if event.data['character'] is not self.character:
            return
        
        damage = event.data['damage']
        if damage.damageType == DamageType.NORMAL and event.frame - self.last_normal_damage_time >= 6 *60:
            self.last_burst_damage_time = event.frame
            damage.panel['伤害加成'] += 60
            damage.setDamageData('深廊终曲-四件套伤害加成', 60)
        elif damage.damageType == DamageType.BURST and event.frame - self.last_burst_damage_time >= 6 *60:
            self.last_normal_damage_time = event.frame
            damage.panel['伤害加成'] += 60
            damage.setDamageData('深廊终曲-四件套伤害加成', 60)

__all__ = [
    "FinaleOftheDeepGalleries",
    "ArtifactEffect",
    "GladiatorFinale",
    "ObsidianCodex",
    "ScrolloftheHeroOfCinderCity",
    "EmblemOfSeveredFate",
    "SongOfDaysPast",
    "Instructor",
    "NoblesseOblige",
    "MarechausseeHunter",
    "GoldenTroupe",
    "ViridescentVenerer",
    "DeepwoodMemories",
    "FlowerOfParadiseLost",
    "LongNightsOath"
]
