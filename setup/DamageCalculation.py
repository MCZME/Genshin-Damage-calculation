from enum import Enum, auto
from character.character import Character
from setup.BaseClass import SkillBase
from setup.Event import EventBus, EventHandler, EventType, GameEvent
from setup.Target import Target

# 定义一个枚举类，表示伤害类型
class DamageType(Enum):
    NORMAL = auto()
    HEAVY = auto()
    SKILL = auto()
    BURST = auto()

class Calculation:
    def __init__(self,source:Character,target:Target,damageType:DamageType,skill:SkillBase):
        self.source = source
        self.target = target
        self.damageType = damageType
        self.skill = skill

    def attack(self):
        attributePanel = self.source.attributePanel
        atk0 = attributePanel['攻击力']
        atk1 = atk0 * attributePanel['攻击力%']/100 + attributePanel['固定攻击力']
        return atk0+atk1

    def damageMultipiler(self):
        return self.skill.getDamageMultipiler()/100

    def damageBonus(self):
        DamageBonus = 0
        bonus_event = GameEvent(
            event_type=EventType.BEFORE_DAMAGE_BONUS,
            source=self.source,
            target=self.target,
            damageType=self.damageType,
            damageBonus=DamageBonus
        )
        EventBus.publish(bonus_event)

        attributePanel = self.source.attributePanel
        DamageBonus = bonus_event.data['damageBonus'] + attributePanel[self.skill.element[0]+'伤害加成'] + attributePanel['伤害加成']
        return DamageBonus/100

    def criticalBracket(self):
        attributePanel = self.source.attributePanel
        return attributePanel['暴击伤害']/100

    def defense(self):
        t_level = self.target.level
        c_level = self.source.level
        return (100+c_level)/(190+(t_level+100))

    def resistance(self):
        r = self.target.element_resistance[self.skill.element[0]]
        if r>75:
            return (1/(1+4*r))/100
        elif r>=0 and r<=75:
            return (100-r)/100
        else:
            return (100-r/2)/100
        
    # 待补充
    # 剧变反应
    def reaction(self):
        e = self.source.attributePanel['元素精通']
        e_skill = self.skill.element
        e_target = self.target.elementalAura
        if e_target[0] == "物理":
            return 1
        elif e_skill[0] == e_target[0]:
            return 1
        elif e_skill[0] == "火" and e_target[0] == "水":
            return 1.5*(1+(2.78*e/(e+1400)))
        elif e_skill[0] == "水" and e_target[0] == "火":
            return 2*(1+(2.78*e/(e+1400)))
        elif e_skill[0] == "火" and e_target[0] == "冰":
            return 2*(1+(2.78*e/(e+1400)))
        elif e_skill[0] == "冰" and e_target[0] == "火":
            return 1.5*(1+(2.78*e/(e+1400)))
        

    def calculation(self):
        damage = self.attack() * self.damageMultipiler() * (1 + self.damageBonus()) * (1 + self.criticalBracket()) * self.defense() * (self.resistance()) * self.reaction()
        return damage

class DamageCalculateEventHandler(EventHandler):
    def handle_event(self, event):
        if event.event_type == EventType.BEFORE_DAMAGE:
            calculation = Calculation(event.source, event.target, event.data['damageType'],event.data['skill'])
            event.data['damage'] = calculation.calculation()

class Damage():
    def __init__(self,damageMultipiler,element,damageType:DamageType,damge=0):
        self.damageMultipiler = damageMultipiler
        self.element = element
        self.damageType = damageType

    def setSource(self,source):
        self.source = source

    def setTarget(self,target):
        self.target = target

    def setDamageData(self):
        ...        