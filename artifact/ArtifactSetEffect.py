from character.character import Character
from setup.BaseEffect import  ElementalDamageBoostEffect
from setup.DamageCalculation import DamageType
from setup.Event import EnergyChargeEvent, EventBus, EventHandler, EventType
from setup.Team import Team
from setup.Tool import GetCurrentTime

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
        ...

    def handle_event(self, event):
        if event.event_type == EventType.BEFORE_NIGHTSOUL_BLESSING:
            attributePanel = event.data['character'].attributePanel
            attributePanel['伤害加成'] += 15
        elif event.event_type == EventType.AFTER_NIGHTSOUL_BLESSING:
            attributePanel = event.data['character'].attributePanel
            attributePanel['伤害加成'] -= 15

class CinderCityEffect(ElementalDamageBoostEffect):
    """烬城勇者绘卷效果"""
    def __init__(self, character,element_type):
        super().__init__(character, '烬城勇者绘卷', element_type, 12, 12*60)
        self.stacks = {}
        self.nightsoul_stacks = {}
        self.nightsoul_duration = 20*60
        self.nightsoul_bonus = 28

    def apply(self,element_type):
        # 防止重复应用
        for character in Team.team:
            existing = next((e for e in character.active_effects 
                        if isinstance(e, CinderCityEffect) and e.name == self.name), None)
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
                character.attributePanel[element+'元素伤害加成'] += self.bonus
                character.add_effect(self)
                self.stacks[element] = self.duration
                if self.character.Nightsoul_Blessing:
                    character.attributePanel[element+'元素伤害加成'] += self.nightsoul_bonus
                    self.nightsoul_stacks[element] = self.nightsoul_bonus
            print(f"{character.name}获得{element_type}烬城勇者绘卷效果")

    def apply_element(self,element):
        for character in Team.team:
            character.attributePanel[element+'元素伤害加成'] += self.bonus
            self.stacks[element] = self.duration

    def apply_nightsoul(self,element):
        for character in Team.team:
            character.attributePanel[element+'元素伤害加成'] += self.nightsoul_bonus
            self.nightsoul_stacks[element] = self.nightsoul_bonus
        
    def remove(self):
        for character in Team.team:
            for element in self.element_type:
                character.attributePanel[element+'元素伤害加成'] -= self.bonus
            character.remove_effect(self)
            print(f"{character.name}: {self.name}效果结束")

    def remove_element(self,element):
        for character in Team.team:
            character.attributePanel[element+'元素伤害加成'] -= self.bonus
        del self.stacks[element]

    def remove_nightsoul(self,element):
        for character in Team.team:
            character.attributePanel[element+'元素伤害加成'] -= self.nightsoul_bonus
        del self.nightsoul_stacks[element]

    def update(self):
        for elemment,time in self.stacks.items():
            self.stacks[elemment] -= 1
            if self.stacks[elemment] <= 0:
                self.remove_element(elemment)
        for elemment,time in self.nightsoul_stacks.items():
            self.nightsoul_stacks[elemment] -= 1
            if self.nightsoul_stacks[elemment] <= 0:
                self.remove_nightsoul(elemment)
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
            energy_event = EnergyChargeEvent(self.character,('无', 6), GetCurrentTime(),
                                             is_alone=True,is_fixed=True)
            EventBus.publish(energy_event)
        elif event.event_type == EventType.AFTER_ELEMENTAL_REACTION:
            reaction = event.data['elementalReaction']
            if reaction.source == self.character:
                CinderCityEffect(self.character,[reaction.target_element, reaction.damage.element[0]]).apply([reaction.target_element, reaction.damage.element[0]])
