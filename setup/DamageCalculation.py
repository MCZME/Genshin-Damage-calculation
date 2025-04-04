from enum import Enum, auto
from character.character import Character
from setup.BaseEffect import ElementalInfusionEffect, ResistanceDebuffEffect
from setup.ElementalReaction import ElementalReaction, ElementalReactionType
from setup.Event import DamageEvent, ElementalReactionEvent, EventBus, EventHandler, EventType, GameEvent
from setup.Target import Target
from setup.Tool import GetCurrentTime
from setup.Logger import get_emulation_logger

# 定义一个枚举类，表示伤害类型
class DamageType(Enum):
    NORMAL = "普通攻击"
    CHARGED = "重击"
    SKILL = "元素战技"
    BURST = "元素爆发"
    PLUNGING = "下落攻击"
    REACTION = "剧变反应"

class Damage():
    def __init__(self,damageMultipiler,element,damageType:DamageType,name,**kwargs):
        self.damageMultipiler = damageMultipiler
        self.element = element
        self.damageType = damageType
        self.name = name
        self.damage = 0
        self.baseValue = '攻击力'
        self.reaction = None # ElementalReaction class
        self.data = kwargs
        self.panel = {}

    def setSource(self,source):
        self.source = source

    def setTarget(self,target):
        self.target = target

    def setBaseValue(self,baseValue):
        self.baseValue = baseValue

    def setReaction(self,reaction):
        self.reaction = reaction

    def setDamageData(self,key,value):
        self.data[key] = value

    def setPanel(self,key,value):
        self.panel[key] = value

class Calculation:
    def __init__(self,source:Character,target:Target,damage:Damage):
        self.source = source
        self.target = target
        self.damage = damage

    def attack(self):
        attributePanel = self.source.attributePanel
        atk0 = attributePanel['攻击力']
        atk1 = atk0 * attributePanel['攻击力%']/100 + attributePanel['固定攻击力']
        self.damage.setPanel('攻击力',atk0+atk1)
        return atk0+atk1

    def health(self):
        """获取生命值"""
        attribute = self.source.attributePanel
        hp0 = attribute['生命值']
        hp1 = hp0 * attribute['生命值%'] / 100 + attribute['固定生命值']
        self.damage.setPanel('生命值',hp0+hp1)
        return hp0 + hp1

    def DEF(self):
        """获取防御力"""
        attribute = self.source.attributePanel
        def0 = attribute['防御力']
        def1 = def0 * attribute['防御力%'] / 100 + attribute['固定防御力']
        self.damage.setPanel('防御力',def0+def1)
        return def0 + def1

    def damageMultipiler(self):
        self.damage.setPanel('伤害倍率',self.damage.damageMultipiler)
        return self.damage.damageMultipiler/100

    def damageBonus(self):
        self.damage.setPanel('伤害加成',0)
        event = GameEvent(EventType.BEFORE_DAMAGE_BONUS, 
                          GetCurrentTime(),
                          character = self.source,
                           target = self.target, 
                           damage = self.damage)
        EventBus.publish(event)
        attributePanel = self.source.attributePanel
        self.damage.panel['伤害加成'] += attributePanel['伤害加成']
        self.damage.panel['伤害加成'] += attributePanel[(self.damage.element[0] if self.damage.element[0]=='物理'else self.damage.element[0]+'元素') +'伤害加成']
        event = GameEvent(EventType.AFTER_DAMAGE_BONUS, 
                          GetCurrentTime(),
                          character = self.source,
                           target = self.target, 
                           damage = self.damage)
        EventBus.publish(event)
        return self.damage.panel['伤害加成']/100

    def criticalBracket(self):
        self.damage.setPanel('暴击伤害',0)
        event = GameEvent(EventType.BEFORE_CRITICAL,GetCurrentTime(),
                          character = self.source,
                          target = self.target, 
                          damage = self.damage)
        EventBus.publish(event)
        attributePanel = self.source.attributePanel
        self.damage.panel['暴击伤害'] += attributePanel['暴击伤害']   
        event = GameEvent(EventType.AFTER_CRITICAL,GetCurrentTime(),
                          character = self.source,
                          target = self.target, 
                          damage = self.damage)
        EventBus.publish(event)
        return self.damage.panel['暴击伤害']/100

    def defense(self):
        self.damage.setPanel('防御力减免',(5*self.source.level+500)/(self.target.defense+5*self.source.level+500))
        return (5*self.source.level+500)/(self.target.defense+5*self.source.level+500)

    def resistance(self):
        r = self.target.element_resistance[self.damage.element[0]]
        if r>75:
            self.damage.setPanel('元素抗性',(1/(1+4*r))/100)
            return (1/(1+4*r))/100
        elif r>=0 and r<=75:
            self.damage.setPanel('元素抗性',(100-r)/100)
            return (100-r)/100
        else:
            self.damage.setPanel('元素抗性',(100-r/2)/100)
            return (100-r/2)/100
        
    # 待补充
    # 剧变反应
    def reaction(self):
        attributePanel = self.source.attributePanel
        e = attributePanel['元素精通']
        r = {}
        if '反应系数提高' in list(attributePanel.keys()):
            r = attributePanel['反应系数提高']
        if self.damage.element[0] != '物理':
            target_element = self.target.apply_elemental_aura(self.damage.element)
            if target_element is not None:
                elementalReaction = ElementalReaction(source=self.source,target_element=target_element,damage=self.damage)
                event = ElementalReactionEvent(elementalReaction, GetCurrentTime())
                EventBus.publish(event)
                self.damage.reaction = event.data['elementalReaction']
                if self.damage.reaction.reaction_Type == "剧变反应":
                    self.damage.setPanel('反应系数',1)
                    return 1
                if self.damage.reaction.reaction_type in list(r.keys()):
                    r1 = r[self.damage.reaction.reaction_type]
                else:
                    r1 = 0
                self.damage.setPanel('反应系数',self.damage.reaction.reaction_ratio * (1+(2.78*e)/(e+1400)+r1))
                return self.damage.reaction.reaction_ratio * (1+(2.78*e)/(e+1400)+r1)
        self.damage.setPanel('反应系数',1)
        return 1


              
    def calculation_by_attack(self):
        value = self.attack() * self.damageMultipiler() * (1 + self.damageBonus()) * (1 + self.criticalBracket()) * self.defense() * self.resistance() * self.reaction()
        self.damage.damage = value
    
    def calculation_by_hp(self):
        value = self.health() * self.damageMultipiler() * (1 + self.damageBonus()) * (1 + self.criticalBracket()) * self.defense() * self.resistance() * self.reaction()
        self.damage.damage = value

    def calculation_by_def(self):
        value = self.DEF() * self.damageMultipiler() * (1 + self.damageBonus()) * (1 + self.criticalBracket()) * self.defense() * self.resistance() * self.reaction()
        self.damage.damage = value

    def calculation_by_reaction(self):
        attributePanel = self.source.attributePanel
        r = {}
        if '反应系数提高' in list(attributePanel.keys()):
            r = attributePanel['反应系数提高']
        if self.damage.name in list(r.keys()):
            r1 = r[self.damage.name]
        else:
            r1 = 0
        inc = self.damage.panel['反应系数'] * (1+16*self.source.attributePanel['元素精通']/(self.source.attributePanel['元素精通']+2000))
        value = self.damage.panel['等级系数'] * (inc+r1) * self.resistance()
        self.damage.damage = value

# todo
# 元素反应：燃烧，绽放，超绽放，烈绽放，激化，超激化，蔓激化，感电，扩散，碎冰，冻结
class DamageCalculateEventHandler(EventHandler):
    def handle_event(self, event):
        if event.event_type == EventType.BEFORE_DAMAGE:
            character = event.data['character']
            damage = event.data['damage']
            
            if damage.damageType in [DamageType.NORMAL, DamageType.CHARGED]:
                # 处理元素附魔
                self.handle_elemental_infusion(character, damage)
            
            # 原有伤害计算逻辑
            calculation = Calculation(character, event.data['target'], damage)
            if damage.damageType == DamageType.REACTION:
                calculation.calculation_by_reaction()
            elif damage.baseValue == '攻击力':
                calculation.calculation_by_attack()
            elif damage.baseValue == '生命值':
                calculation.calculation_by_hp()
            elif damage.baseValue == '防御力':
                calculation.calculation_by_def()

            get_emulation_logger().log_damage(character, event.data['target'], damage)
                
            damageEvent = DamageEvent(character, event.data['target'], damage, event.frame, before=False)
            EventBus.publish(damageEvent)

            if damage.reaction is not None and damage.reaction.reaction_Type == '剧变反应':
                self.extra_damage(character, event.data['target'], damage)
    
    def handle_elemental_infusion(self, character, damage):
        # 获取所有元素附魔效果
        infusion_effects = [e for e in character.active_effects 
                          if isinstance(e, ElementalInfusionEffect)]
        
        # 检查是否有不可覆盖的效果
        unoverridable = next((e for e in infusion_effects if e.is_unoverridable), None)
        if unoverridable:
            damage.element = (unoverridable.element_type, unoverridable.should_apply_infusion())
            return
        
        # 收集所有元素类型并处理克制关系（仅通过冷却检查的）
        elements = [e.element_type for e in infusion_effects]
        if len(elements) > 1:
            # 实现元素克制逻辑
            dominant_element = self.get_dominant_element(elements)
            damage.element = (dominant_element, max(e.should_apply_infusion() for e in infusion_effects))
        elif len(elements) == 1:
            damage.element = (elements[0], infusion_effects[0].should_apply_infusion())
        
    def get_dominant_element(self, elements):
        # 元素克制关系：水 > 火 > 冰
        element_order = ['水', '火', '冰']
        infusion_effects = [e for e in self.character.active_effects 
                          if isinstance(e, ElementalInfusionEffect)]
        for element in element_order:
            if element in elements:
                return element
        # 没有克制关系则返回最早应用的元素
        return min(elements, key=lambda x: next(e.apply_time for e in infusion_effects if e.element_type == x))
    
    def extra_damage(self, character, target, damage):
        if damage.reaction.reaction_type == ElementalReactionType.OVERLOAD:
            EventBus.publish(GameEvent(EventType.BEFORE_OVERLOAD, GetCurrentTime(),
                                       character = character, 
                                       target = target))
            e_damage = Damage(0,('火',0),DamageType.REACTION, '超载')
            e_damage.setPanel("等级系数", damage.reaction.lv_ratio)
            e_damage.setPanel("反应系数", damage.reaction.reaction_ratio)
            EventBus.publish(DamageEvent(character, target, e_damage, GetCurrentTime()))
            EventBus.publish(GameEvent(EventType.AFTER_OVERLOAD, GetCurrentTime(), 
                                        character = character, 
                                        target = target))
        elif damage.reaction.reaction_type == ElementalReactionType.SUPERCONDUCT:
            EventBus.publish(GameEvent(EventType.BEFORE_SUPERCONDUCT, GetCurrentTime(),
                                        character = character, 
                                        target = target))
            e_damage = Damage(0,('冰',0),DamageType.REACTION, '超导')
            EventBus.publish(DamageEvent(character, target, e_damage, GetCurrentTime()))
            ResistanceDebuffEffect('超导',character,target,'物理',40,12*60).apply()
            EventBus.publish(GameEvent(EventType.AFTER_SUPERCONDUCT, GetCurrentTime(), 
                                        character = character, 
                                        target = target))
