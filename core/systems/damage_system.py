from typing import List, Optional
import random

from core.systems.utils import AttributeCalculator
from core.systems.base_system import GameSystem
from core.context import EventEngine
from core.event import GameEvent, DamageEvent, EventType
from core.action.damage import Damage, DamageType
from core.config import Config
from core.logger import get_emulation_logger
from core.entities.elemental_entities import DendroCoreObject
from core.effect.elemental import ElementalInfusionEffect
from core.tool import GetCurrentTime

# ---------------------------------------------------------
# Calculation Helper (Logic Container)
# ---------------------------------------------------------
class Calculation:
    def __init__(self, source, target, damage: Damage, engine: EventEngine):
        self.source = source
        self.target = target
        self.damage = damage
        self.engine = engine

        event = GameEvent(EventType.BEFORE_CALCULATE, GetCurrentTime(),
                          character=self.source,
                          target=self.target,
                          damage=self.damage)
        self.engine.publish(event)
        self.damage = event.data['damage']
        self.damage.setPanel('固定伤害基础值加成', 0)

    def attack(self):
        val = AttributeCalculator.get_attack(self.source)
        self.damage.setPanel('攻击力', val)
        return val

    def health(self):
        val = AttributeCalculator.get_hp(self.source)
        self.damage.setPanel('生命值', val)
        return val

    def DEF(self):
        val = AttributeCalculator.get_defense(self.source)
        self.damage.setPanel('防御力', val)
        return val

    def damageMultipiler(self):
        self.damage.setPanel('伤害倍率', self.damage.damageMultipiler)
        event = GameEvent(EventType.BEFORE_DAMAGE_MULTIPLIER, GetCurrentTime(),
                          character=self.source,
                          target=self.target,
                          damage=self.damage)
        self.engine.publish(event)
        event = GameEvent(EventType.AFTER_DAMAGE_MULTIPLIER, GetCurrentTime(),
                          character=self.source,
                          target=self.target,
                          damage=self.damage)
        self.engine.publish(event)
        return event.data['damage'].panel['伤害倍率']

    def damageBonus(self):
        self.damage.setPanel('伤害加成', 0)
        event = GameEvent(EventType.BEFORE_DAMAGE_BONUS, 
                          GetCurrentTime(),
                          character=self.source,
                          target=self.target, 
                          damage=self.damage)
        self.engine.publish(event)
        attributePanel = self.source.attributePanel
        self.damage.panel['伤害加成'] += attributePanel['伤害加成']
        element_key = (self.damage.element[0] if self.damage.element[0] == '物理' else self.damage.element[0] + '元素') + '伤害加成'
        self.damage.panel['伤害加成'] += attributePanel.get(element_key, 0)
        
        event = GameEvent(EventType.AFTER_DAMAGE_BONUS, 
                          GetCurrentTime(),
                          character=self.source,
                          target=self.target, 
                          damage=self.damage)
        self.engine.publish(event)
        return self.damage.panel['伤害加成']/100

    def critical(self):
        self.damage.setPanel('暴击率', 0)
        event = GameEvent(EventType.BEFORE_CRITICAL, GetCurrentTime(),
                          character=self.source,
                          target=self.target,
                          damage=self.damage)
        self.engine.publish(event)
        attributePanel = self.source.attributePanel
        self.damage.panel['暴击率'] += attributePanel['暴击率']
        event = GameEvent(EventType.AFTER_CRITICAL, GetCurrentTime(),
                          character=self.source,
                          target=self.target,
                          damage=self.damage)
        self.engine.publish(event)
        if random.randint(1, 100) <= self.damage.panel['暴击率']:
            self.damage.setDamageData('暴击', True)
            return 1
        else:
            self.damage.setDamageData('暴击', False)
            return 0

    def criticalBracket(self):
        self.damage.setPanel('暴击伤害', 0)
        event = GameEvent(EventType.BEFORE_CRITICAL_BRACKET, GetCurrentTime(),
                          character=self.source,
                          target=self.target, 
                          damage=self.damage)
        self.engine.publish(event)
        attributePanel = self.source.attributePanel
        self.damage.panel['暴击伤害'] += attributePanel['暴击伤害']   
        event = GameEvent(EventType.AFTER_CRITICAL_BRACKET, GetCurrentTime(),
                          character=self.source,
                          target=self.target, 
                          damage=self.damage)
        self.engine.publish(event)
        
        if Config.get('emulation.open_critical'):
            if self.critical():
                return self.damage.panel['暴击伤害']/100
            else:
                return 0
        else:
            return self.damage.panel['暴击伤害']/100

    def defense(self):
        self.damage.setPanel('防御力减免', (5*self.source.level+500)/(self.target.defense+5*self.source.level+500))
        return (5*self.source.level+500)/(self.target.defense+5*self.source.level+500)

    def resistance(self):
        r = self.target.current_resistance[self.damage.element[0]]
        if r > 75:
            res = (1/(1+4*r))/100
        elif r >= 0 and r <= 75:
            res = (100-r)/100
        else:
            res = (100-r/2)/100
        self.damage.setPanel('元素抗性', res)
        return res
        
    def reaction(self):
        if self.damage.element[0] == '物理':
            return 1
        attributePanel = self.source.attributePanel
        e = attributePanel['元素精通']
        r = attributePanel.get('反应系数提高', {})

        reaction_multiplier = self.target.apply_elemental_aura(self.damage)
        if reaction_multiplier:
            if self.damage.reaction_type and self.damage.reaction_type[0] != '激化反应':
                r1 = r.get(self.damage.reaction_type[1].value, 0) / 100
                self.damage.setPanel('反应系数', reaction_multiplier * (1+(2.78*e)/(e+1400)+r1))
                return reaction_multiplier * (1+(2.78*e)/(e+1400)+r1)
            elif self.damage.reaction_type and self.damage.reaction_type[0] == '激化反应':
                self.damage.panel['固定伤害基础值加成'] += self.damage.panel['等级系数'] * reaction_multiplier * (1 + 5 * e /(e + 1200))
                self.damage.setDamageData('激化提升', self.damage.panel['等级系数'] * reaction_multiplier * (1 + 5 * e /(e + 1200)))
        return 1

    def independent_damage_multiplier(self):
        self.damage.setPanel('独立伤害加成', 0)
        event = GameEvent(EventType.BEFORE_INDEPENDENT_DAMAGE, GetCurrentTime(),
                          character=self.source,
                          target=self.target, 
                          damage=self.damage)
        self.engine.publish(event)
        event = GameEvent(EventType.AFTER_INDEPENDENT_DAMAGE, GetCurrentTime(),
                          character=self.source,
                          target=self.target, 
                          damage=self.damage)
        self.engine.publish(event)
        if self.damage.panel['独立伤害加成'] > 0:
            return self.damage.panel['独立伤害加成']/100
        else:
            self.damage.panel.pop('独立伤害加成', None)
            return 1
              
    def calculation_by_reaction(self):
        attributePanel = self.source.attributePanel
        r = attributePanel.get('反应系数提高', {})
        r1 = r.get(self.damage.reaction_type[1].value, 0) / 100
        
        if r1 != 0:
            self.damage.setDamageData('反应伤害提高', r1)
            
        inc = self.damage.panel['反应系数'] * (1+16*self.source.attributePanel['元素精通']/(self.source.attributePanel['元素精通']+2000))
        value = self.damage.panel['等级系数'] * (inc+r1) * self.resistance()
        
        if '暴击伤害' in self.damage.panel:
            if not Config.get('emulation.open_critical') or random.randint(1, 100) <= self.damage.panel['暴击率']:
                value = value * (1 + self.damage.panel['暴击伤害']/100)
                self.damage.setDamageData('暴击', True)
                
        self.damage.damage = value

    def calculate(self):
        if self.damage.damageType == DamageType.REACTION:
            self.calculation_by_reaction()
        else:
            event = GameEvent(EventType.BEFORE_FIXED_DAMAGE, GetCurrentTime(),
                    character=self.source,
                    target=self.target, 
                    damage=self.damage)
            self.engine.publish(event)
            
            if isinstance(self.damage.baseValue, tuple):
                val1 = self.get_base_value(self.damage.baseValue[0]) * self.damageMultipiler()[0]/100
                val2 = self.get_base_value(self.damage.baseValue[1]) * self.damageMultipiler()[1]/100
                value = val1 + val2
                self.damage.setPanel(self.damage.baseValue[1], self.get_base_value(self.damage.baseValue[1]))
                self.damage.panel['伤害倍率'] = f'{self.damageMultipiler()[0]:.2f}% + {self.damageMultipiler()[1]:.2f}% {self.damage.baseValue[1]}'
            else:
                value = self.get_base_value(self.damage.baseValue) * self.damageMultipiler()/100
            
            value += self.damage.panel.get('固定伤害基础值加成', 0)
            
            event = GameEvent(EventType.AFTER_FIXED_DAMAGE, GetCurrentTime(),
                          character=self.source,
                          target=self.target, 
                          damage=self.damage)
            self.engine.publish(event)
            
            value = value * (1 + self.damageBonus()) * (1 + self.criticalBracket()) * self.defense() * self.resistance() * self.reaction()
            self.damage.damage = value * self.independent_damage_multiplier()

    def get_base_value(self, baseValue):
        if baseValue == '攻击力':
            return self.attack()
        elif baseValue == '生命值':
            return self.health()
        elif baseValue == '防御力':
            return self.DEF()
        elif baseValue == '元素精通':
            return self.source.attributePanel['元素精通']

# ---------------------------------------------------------
# Damage System
# ---------------------------------------------------------
class DamageSystem(GameSystem):
    def register_events(self, engine: EventEngine):
        engine.subscribe(EventType.BEFORE_DAMAGE, self)

    def handle_event(self, event: GameEvent):
        # 仅处理 BEFORE_DAMAGE
        if event.event_type == EventType.BEFORE_DAMAGE:
            self._process_damage(event)
            
    def _process_damage(self, event: GameEvent):
        character = event.data['character']
        damage = event.data['damage']
        
        # 元素附魔逻辑
        if damage.damageType in [DamageType.NORMAL, DamageType.CHARGED, DamageType.PLUNGING]:
            self.handle_elemental_infusion(character, damage)
        
        # 执行计算
        calculation = Calculation(character, event.data['target'], damage, self.engine)
        calculation.calculate()

        # 记录日志
        get_emulation_logger().log_damage(character, event.data['target'], damage)
            
        # 发布计算后事件 (标记 before=False)
        damageEvent = DamageEvent(character, event.data['target'], damage, event.frame, before=False)
        self.engine.publish(damageEvent)

        # 触发草原核反应 (延迟导入以避免循环依赖)
        try:
            ctx = self.context
            if ctx and ctx.team:
                dendroCore = [d for d in ctx.team.active_objects if isinstance(d, DendroCoreObject)]
                for d in dendroCore:
                    d.apply_element(damage)
        except Exception:
            pass

    def handle_elemental_infusion(self, character, damage: Damage):
        # 获取所有元素附魔效果
        infusion_effects = [e for e in character.active_effects 
                          if isinstance(e, ElementalInfusionEffect)]
        
        if damage.data.get('不可覆盖', False):
            return
            
        unoverridable = next((e for e in infusion_effects if e.is_unoverridable), None)
        if unoverridable:
            damage.element = (unoverridable.element_type, unoverridable.should_apply_infusion(damage.damageType))
            return
        
        elements = [e.element_type for e in infusion_effects]
        if len(elements) > 1:
            dominant_element = self.get_dominant_element(character, elements)
            damage.element = (dominant_element, max(e.should_apply_infusion(damage.damageType) for e in infusion_effects))
        elif len(elements) == 1:
            damage.element = (elements[0], infusion_effects[0].should_apply_infusion(damage.damageType))
        
    def get_dominant_element(self, character, elements):
        element_order = ['水', '火', '冰']
        infusion_effects = [e for e in character.active_effects 
                          if isinstance(e, ElementalInfusionEffect)]
        for element in element_order:
            if element in elements:
                return element
        
        # 默认取最早的一个
        return min(elements, key=lambda x: next(e.apply_time for e in infusion_effects if e.element_type == x))
