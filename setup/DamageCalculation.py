from enum import Enum, auto
from character.character import Character
from setup.BaseEffect import ElementalInfusionEffect
from setup.ElementalReaction import ElementalReaction
from setup.Event import DamageEvent, ElementalReactionEvent, EventBus, EventHandler, EventType
from setup.Target import Target
from setup.Tool import GetCurrentTime

# 定义一个枚举类，表示伤害类型
class DamageType(Enum):
    NORMAL = auto()
    CHARGED = auto()
    SKILL = auto()
    BURST = auto()
    PLUNGING = auto()  # 下落攻击

class Damage():
    def __init__(self,damageMultipiler,element,damageType:DamageType,name,**kwargs):
        self.damageMultipiler = damageMultipiler
        self.element = element
        self.damageType = damageType
        self.name = name
        self.damage = 0
        self.baseValue = '攻击力'

    def setSource(self,source):
        self.source = source

    def setTarget(self,target):
        self.target = target

    def setDamageData(self):
        ...        

class Calculation:
    def __init__(self,source:Character,target:Target,damage:Damage):
        self.source = source
        self.target = target
        self.damage = damage

    def attack(self):
        attributePanel = self.source.attributePanel
        atk0 = attributePanel['攻击力']
        atk1 = atk0 * attributePanel['攻击力%']/100 + attributePanel['固定攻击力']
        return atk0+atk1

    def health(self):
        """获取生命值"""
        attribute = self.source.attributePanel
        hp0 = attribute['生命值']
        hp1 = hp0 * attribute['生命值%'] / 100 + attribute['固定生命值']
        return hp0 + hp1

    def DEF(self):
        """获取防御力"""
        attribute = self.source.attributePanel
        def0 = attribute['防御力']
        def1 = def0 * attribute['防御力%'] / 100 + attribute['固定防御力']
        return def0 + def1

    def damageMultipiler(self):
        return self.damage.damageMultipiler/100

    def damageBonus(self):
        DamageBonus = 0
        attributePanel = self.source.attributePanel
        DamageBonus = attributePanel[(self.damage.element[0] if self.damage.element[0]=='物理'else self.damage.element[0]+'元素') +'伤害加成'] + attributePanel['伤害加成']
        return DamageBonus/100

    def criticalBracket(self):
        attributePanel = self.source.attributePanel
        return attributePanel['暴击伤害']/100

    def defense(self):
        return (5*self.source.level+500)/(self.target.defense+5*self.source.level+500)

    def resistance(self):
        r = self.target.element_resistance[self.damage.element[0]]
        if r>75:
            return (1/(1+4*r))/100
        elif r>=0 and r<=75:
            return (100-r)/100
        else:
            return (100-r/2)/100
        
    # 待补充
    # 剧变反应
    def reaction(self):
        attributePanel = self.source.attributePanel
        e = attributePanel['元素精通']
        r = {'反应类型':[],'反应系数提高值':0}
        if '反应系数提高' in list(attributePanel.keys()):
            r = attributePanel['反应系数提高']
        if self.damage.element[0] == '物理':
            return 1
        else:
            target_element = self.target.apply_elemental_aura(self.damage.element)
            if target_element is not None:
                elementalReaction = ElementalReaction(source=self.source,target_element=target_element,damage=self.damage)
                event = ElementalReactionEvent(elementalReaction, GetCurrentTime())
                EventBus.publish(event)
                if event.data['elementalReaction'].reaction_Type == '增幅反应':
                    if event.data['elementalReaction'].reaction_type in r['反应类型']:
                        r1 = r['反应系数提高值']
                    else:
                        r1 = 0
                    return event.data['elementalReaction'].reaction_ratio * (1+(2.78*e)/(e+1400)+r1)
                elif event.data['elementalReaction'].reaction_Type == '剧变反应':
                    ...
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
            if damage.baseValue == '攻击力':
                calculation.calculation_by_attack()
            elif damage.baseValue == '生命值':
                calculation.calculation_by_hp()
            elif damage.baseValue == '防御力':
                calculation.calculation_by_def()

            element_icons = {
                '物理': '⚔️',
                '水': '🌊',
                '火': '🔥',
                '冰': '❄️',
                '风': '🌪️',
                '雷': '⚡',
                '岩': '⛰️',
                '草': '🌿'
            }
            e = element_icons.get(damage.element[0], '❓')
            print(f'{e} {character.name}使用 {damage.name} 造成{damage.damage:.2f}点 {damage.element[0]+"元素" if damage.element[0] != "物理" else damage.element[0]} 伤害')
                
            damageEvent = DamageEvent(character, event.data['target'], damage, event.frame, before=False)
            EventBus.publish(damageEvent)
    
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