from enum import Enum
import random
from character.character import Character
from core.BaseObject import DendroCoreObject
from core.Team import Team
from core.effect.BaseEffect import ElementalInfusionEffect
from core.Config import Config
import core.Constants as Constants
from core.Event import DamageEvent, EventBus, EventHandler, EventType, GameEvent
from core.Tool import GetCurrentTime
from core.Logger import get_emulation_logger
from typing import Dict, List, Tuple, Optional, Any, Union, TYPE_CHECKING, cast

if TYPE_CHECKING:
    from character.character import Character
    from core.effect.BaseEffect import ElementalInfusionEffect

# 定义一个枚举类，表示伤害类型
class DamageType(Enum):
    NORMAL = Constants.SKILL_NAME_NORMAL
    CHARGED = Constants.SKILL_NAME_CHARGED
    SKILL = Constants.SKILL_NAME_ELEMENTAL_SKILL
    BURST = Constants.SKILL_NAME_ELEMENTAL_BURST
    PLUNGING = Constants.SKILL_NAME_PLUNGING
    REACTION = Constants.DAMAGE_TYPE_REACTION

class Damage:
    def __init__(self, damageMultiplier: Union[float, List[float]], element: Tuple[str, int], damageType: DamageType, name: str, **kwargs: Any) -> None:
        self.damageMultiplier: Union[float, List[float]] = damageMultiplier
        self.element: Tuple[str, int] = element
        self.damageType: DamageType = damageType
        self.name: str = name
        self.damage: float = 0
        self.baseValue: Union[str, Tuple[str, str]] = Constants.ATTR_ATK
        self.reaction_type: Optional[Tuple[str, Enum]] = None
        self.reaction_data: Optional[Any] = None
        self.data: Dict[str, Any] = kwargs
        self.panel: Dict[str, Any] = {}
        self.hit_type: Optional[str] = None

    def setSource(self, source: 'Character') -> None:
        self.source: 'Character' = source

    def setTarget(self, target: Any) -> None:
        self.target: Any = target

    def setBaseValue(self, baseValue: Union[str, Tuple[str, str]]) -> None:
        self.baseValue = baseValue

    def setReaction(self, reaction_type: Tuple[str, Enum], reaction_data: Any) -> None:
        self.reaction_type = reaction_type
        self.reaction_data = reaction_data

    def setDamageData(self, key: str, value: Any) -> None:
        self.data[key] = value

    def setPanel(self, key: str, value: Any) -> None:
        self.panel[key] = value

    def setHitType(self, hit_type: str) -> None:
        self.hit_type = hit_type

class Calculation:
    def __init__(self, source: 'Character', target: Any, damage: Damage) -> None:
        self.source: 'Character' = source
        self.target: Any = target
        self.damage: Damage = damage

        event = GameEvent(EventType.BEFORE_CALCULATE,GetCurrentTime(),
                          character = self.source,
                          target = self.target,
                          damage = self.damage)
        EventBus.publish(event)
        self.damage = event.data['damage']
        self.damage.setPanel(Constants.ATTR_FIXED_DMG_BONUS,0)

    def attack(self) -> float:
        attributePanel = self.source.attributePanel
        atk0 = attributePanel[Constants.ATTR_ATK]
        atk1 = atk0 * attributePanel[Constants.ATTR_ATK_PERCENT]/100 + attributePanel[Constants.ATTR_FIXED_ATK]
        self.damage.setPanel(Constants.ATTR_ATK,atk0+atk1)
        return atk0+atk1

    def health(self) -> float:
        """获取生命值"""
        attribute = self.source.attributePanel
        hp0 = attribute[Constants.ATTR_HP]
        hp1 = hp0 * attribute[Constants.ATTR_HP_PERCENT] / 100 + attribute[Constants.ATTR_FIXED_HP]
        self.damage.setPanel(Constants.ATTR_HP,hp0+hp1)
        return hp0 + hp1

    def DEF(self) -> float:
        """获取防御力"""
        attribute = self.source.attributePanel
        def0 = attribute[Constants.ATTR_DEF]
        def1 = def0 * attribute[Constants.ATTR_DEF_PERCENT] / 100 + attribute[Constants.ATTR_FIXED_DEF]
        self.damage.setPanel(Constants.ATTR_DEF,def0+def1)
        return def0 + def1

    def damageMultiplier(self) -> Union[float, List[float]]:
        self.damage.setPanel(Constants.ATTR_DMG_MULTIPLIER,self.damage.damageMultiplier)
        event = GameEvent(EventType.BEFORE_DAMAGE_MULTIPLIER,GetCurrentTime(),
                          character = self.source,
                          target = self.target,
                          damage = self.damage)
        EventBus.publish(event)
        event = GameEvent(EventType.AFTER_DAMAGE_MULTIPLIER,GetCurrentTime(),
                          character = self.source,
                          target = self.target,
                          damage = self.damage)
        EventBus.publish(event)
        EventBus.publish(event)
        return event.data['damage'].panel[Constants.ATTR_DMG_MULTIPLIER]

    def damageBonus(self) -> float:
        self.damage.setPanel(Constants.ATTR_DMG_BONUS,0)
        event = GameEvent(EventType.BEFORE_DAMAGE_BONUS, 
                          GetCurrentTime(),
                          character = self.source,
                           target = self.target, 
                           damage = self.damage)
        EventBus.publish(event)
        attributePanel = self.source.attributePanel
        self.damage.panel[Constants.ATTR_DMG_BONUS] = self.damage.panel.get(Constants.ATTR_DMG_BONUS, 0) + attributePanel[Constants.ATTR_DMG_BONUS]
        element_key = (self.damage.element[0] if self.damage.element[0]==Constants.ELEMENT_PHYSICAL else self.damage.element[0]+Constants.SUFFIX_ELEMENT) + Constants.ATTR_DMG_BONUS
        self.damage.panel[Constants.ATTR_DMG_BONUS] += attributePanel.get(element_key, 0)
        event = GameEvent(EventType.AFTER_DAMAGE_BONUS, 
                          GetCurrentTime(),
                          character = self.source,
                           target = self.target, 
                           damage = self.damage)
        EventBus.publish(event)
        return self.damage.panel[Constants.ATTR_DMG_BONUS]/100

    def critical(self) -> int:
        self.damage.setPanel(Constants.ATTR_CRIT_RATE,0)
        event = GameEvent(EventType.BEFORE_CRITICAL,GetCurrentTime(),
                          character = self.source,
                          target = self.target,
                          damage = self.damage)
        EventBus.publish(event)
        attributePanel = self.source.attributePanel
        self.damage.panel[Constants.ATTR_CRIT_RATE] += attributePanel[Constants.ATTR_CRIT_RATE]
        event = GameEvent(EventType.AFTER_CRITICAL,GetCurrentTime(),
                          character = self.source,
                          target = self.target,
                          damage = self.damage)
        EventBus.publish(event)
        if random.randint(1,100) <= self.damage.panel[Constants.ATTR_CRIT_RATE]:
            self.damage.setDamageData('暴击',True)
            return 1
        else:
            self.damage.setDamageData('暴击',False)
            return 0

    def criticalBracket(self) -> float:
        self.damage.setPanel(Constants.ATTR_CRIT_DMG,0)
        event = GameEvent(EventType.BEFORE_CRITICAL_BRACKET,GetCurrentTime(),
                          character = self.source,
                          target = self.target, 
                          damage = self.damage)
        EventBus.publish(event)
        attributePanel = self.source.attributePanel
        self.damage.panel[Constants.ATTR_CRIT_DMG] += attributePanel[Constants.ATTR_CRIT_DMG]   
        event = GameEvent(EventType.AFTER_CRITICAL_BRACKET,GetCurrentTime(),
                          character = self.source,
                          target = self.target, 
                          damage = self.damage)
        EventBus.publish(event)
        if Config.get('emulation.open_critical'):
            if self.critical():
                return self.damage.panel[Constants.ATTR_CRIT_DMG]/100
            else:
                return 0
        else:
            return self.damage.panel[Constants.ATTR_CRIT_DMG]/100

    def defense(self) -> float:
        self.damage.setPanel(Constants.ATTR_DEF_REDUCTION,(5*self.source.level+500)/(self.target.defense+5*self.source.level+500))
        return (5*self.source.level+500)/(self.target.defense+5*self.source.level+500)

    def resistance(self) -> float:
        r = self.target.current_resistance[self.damage.element[0]]
        if r>75:
            self.damage.setPanel(Constants.ATTR_ELEMENT_RES,(1/(1+4*r))/100)
            return (1/(1+4*r))/100
        elif r>=0 and r<=75:
            self.damage.setPanel(Constants.ATTR_ELEMENT_RES,(100-r)/100)
            return (100-r)/100
        else:
            self.damage.setPanel(Constants.ATTR_ELEMENT_RES,(100-r/2)/100)
            return (100-r/2)/100
        
    def reaction(self) -> float:
        if self.damage.element[0] == Constants.ELEMENT_PHYSICAL:
            return 1
        attributePanel = self.source.attributePanel
        e = attributePanel[Constants.ATTR_EM]
        r = attributePanel.get(Constants.ATTR_REACTION_BONUS, {})
        
        reaction_multiplier = self.target.apply_elemental_aura(self.damage)
        if reaction_multiplier:
            if self.damage.reaction_type and self.damage.reaction_type[0] != '激化反应': # Check if reaction_type is not None
                # 获取反应系数提高
                # Check if reaction_type[1] (Enum) value in keys
                if self.damage.reaction_type[1].value in r:
                    r1 = r[self.damage.reaction_type[1].value]/100
                else:
                    r1 = 0
                self.damage.setPanel('反应系数',reaction_multiplier * (1+(2.78*e)/(e+1400)+r1))
                return reaction_multiplier * (1+(2.78*e)/(e+1400)+r1)
            else:
                self.damage.panel['固定伤害基础值加成'] += self.damage.panel.get('等级系数', 0) * reaction_multiplier * (1 + 5 * e /(e + 1200))
                self.damage.setDamageData('激化提升',self.damage.panel.get('等级系数', 0) * reaction_multiplier * (1 + 5 * e /(e + 1200)))
        return 1

    def independent_damage_multiplier(self) -> float:
        self.damage.setPanel(Constants.ATTR_INDEPENDENT_DMG_BONUS,0)
        event = GameEvent(EventType.BEFORE_INDEPENDENT_DAMAGE,GetCurrentTime(),
                          character = self.source,
                          target = self.target, 
                          damage = self.damage)
        EventBus.publish(event)
        event = GameEvent(EventType.AFTER_INDEPENDENT_DAMAGE,GetCurrentTime(),
                          character = self.source,
                          target = self.target, 
                          damage = self.damage)
        EventBus.publish(event)
        if self.damage.panel[Constants.ATTR_INDEPENDENT_DMG_BONUS] > 0:
            return self.damage.panel[Constants.ATTR_INDEPENDENT_DMG_BONUS]/100
        else:
            self.damage.panel.pop(Constants.ATTR_INDEPENDENT_DMG_BONUS)
            return 1
              
    def calculation_by_reaction(self) -> None:
        attributePanel = self.source.attributePanel
        r = attributePanel.get(Constants.ATTR_REACTION_BONUS, {})

        if self.damage.reaction_type and self.damage.reaction_type[1].value in r:
            r1 = r[self.damage.reaction_type[1].value]/100
        else:
            r1 = 0
        if r1 != 0:
            self.damage.setDamageData(Constants.DAMAGE_BOOST_REACTION,r1)
        inc = self.damage.panel.get(Constants.ATTR_REACTION_MULTIPLIER, 0) * (1+16*self.source.attributePanel[Constants.ATTR_EM]/(self.source.attributePanel[Constants.ATTR_EM]+2000))
        value = self.damage.panel.get(Constants.ATTR_LEVEL_MULTIPLIER, 0) * (inc+r1) * self.resistance()
        if Constants.ATTR_CRIT_DMG in list(self.damage.panel.keys()):
            if not Config.get('emulation.open_critical') or random.randint(1,100) <= self.damage.panel[Constants.ATTR_CRIT_RATE]:
                value = value * (1 + self.damage.panel[Constants.ATTR_CRIT_DMG]/100)
                self.damage.setDamageData('暴击',True)
        self.damage.damage = value

    def calculate(self) -> None:
        if self.damage.damageType == DamageType.REACTION:
            self.calculation_by_reaction()
        else:
            event = GameEvent(EventType.BEFORE_FIXED_DAMAGE,GetCurrentTime(),
                    character = self.source,
                    target = self.target, 
                    damage = self.damage)
            EventBus.publish(event)
            if isinstance(self.damage.baseValue, tuple):
                # split scaling, damageMultiplier return a list?
                # Assume damageMultiplier() returns List[float] here
                multipliers = cast(List[float], self.damageMultiplier())
                value = self.get_base_value(self.damage.baseValue[0]) * multipliers[0]/100 + self.get_base_value(self.damage.baseValue[1]) * multipliers[1]/100
                self.damage.setPanel(self.damage.baseValue[1],self.get_base_value(self.damage.baseValue[1]))
                self.damage.panel[Constants.ATTR_DMG_MULTIPLIER] = f'{multipliers[0]:.2f}% + {multipliers[1]:.2f}% {self.damage.baseValue[1]}'
            else:
                # Assume damageMultiplier() returns float here
                value = self.get_base_value(self.damage.baseValue) * cast(float, self.damageMultiplier())/100
            value += self.damage.panel[Constants.ATTR_FIXED_DMG_BONUS]
            event = GameEvent(EventType.AFTER_FIXED_DAMAGE,GetCurrentTime(),
                          character = self.source,
                          target = self.target, 
                          damage = self.damage)
            EventBus.publish(event)
            value = value * (1 + self.damageBonus()) * (1 + self.criticalBracket()) * self.defense() * self.resistance() * self.reaction()
            self.damage.damage = value * self.independent_damage_multiplier()

    def get_base_value(self, baseValue: str) -> float:
        if baseValue == Constants.ATTR_ATK:
            return self.attack()
        elif baseValue == Constants.ATTR_HP:
            return self.health()
        elif baseValue == Constants.ATTR_DEF:
            return self.DEF()
        elif baseValue == Constants.ATTR_EM:
            return self.source.attributePanel[Constants.ATTR_EM]

class DamageCalculateEventHandler(EventHandler):
    def handle_event(self, event: GameEvent) -> None:
        if event.event_type == EventType.BEFORE_DAMAGE:
            character = event.data['character']
            damage = event.data['damage']
            
            if damage.damageType in [DamageType.NORMAL, DamageType.CHARGED, DamageType.PLUNGING]:
                # 处理元素附魔
                self.handle_elemental_infusion(character, damage)
            
            # 原有伤害计算逻辑
            calculation = Calculation(character, event.data['target'], damage)
            calculation.calculate()

            get_emulation_logger().log_damage(character, event.data['target'], damage)
                
            damageEvent = DamageEvent(character, event.data['target'], damage, event.frame, before=False)
            EventBus.publish(damageEvent)

            dendroCore = [d for d in Team.active_objects if isinstance(d, DendroCoreObject)]
            for d in dendroCore:
                d.apply_element(damage)
    
    def handle_elemental_infusion(self, character: 'Character', damage: Damage) -> None:
        # 获取所有元素附魔效果
        infusion_effects = [e for e in character.active_effects 
                          if isinstance(e, ElementalInfusionEffect)]
        
        # 检查是否有不可覆盖的效果
        if damage.data.get('不可覆盖', False):
            return
        unoverridable = next((e for e in infusion_effects if e.is_unoverridable), None)
        if unoverridable:
            damage.element = (unoverridable.element_type, unoverridable.should_apply_infusion(damage.damageType))
            return
        
        # 收集所有元素类型并处理克制关系（仅通过冷却检查的）
        elements = [e.element_type for e in infusion_effects]
        if len(elements) > 1:
            # 实现元素克制逻辑
            dominant_element = self.get_dominant_element(character, elements)
            damage.element = (dominant_element, max(e.should_apply_infusion(damage.damageType) for e in infusion_effects))
        elif len(elements) == 1:
            damage.element = (elements[0], infusion_effects[0].should_apply_infusion(damage.damageType))
        
    def get_dominant_element(self, character: 'Character', elements: List[str]) -> str:
        # 元素克制关系：水 > 火 > 冰
        element_order = Constants.ELEMENT_ORDER
        infusion_effects = [e for e in character.active_effects 
                          if isinstance(e, ElementalInfusionEffect)]
        for element in element_order:
            if element in elements:
                return element
        # 没有克制关系则返回最早应用的元素
        return min(elements, key=lambda x: next(e.apply_time for e in infusion_effects if e.element_type == x))