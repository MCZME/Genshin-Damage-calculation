from enum import Enum, auto
from character.character import Character
from setup.BaseClass import SkillBase
from setup.Target import Target

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
        atk1 = atk0 * attributePanel['攻击力%'] + attributePanel['固定攻击力']
        return atk0+atk1

    def damageMultipiler(self):
        return self.skill.getDamageMultipiler()

    def damageBonus(self):
        attributePanel = self.source.attributePanel
        DamageBonus = attributePanel[self.skill.element[0]+'伤害加成']
        return DamageBonus

    def criticalBracket(self):
        attributePanel = self.source.attributePanel
        return attributePanel['暴击伤害']

    def defense(self):
        t_level = self.target.level
        c_level = self.source.level
        return (100+c_level)/(190+(t_level+100))

    def resistance(self):
        r = self.target.element_resistance[self.skill.element[0]]
        if r>75:
            return 1/(1+4*r)
        elif r>=0 and r<=75:
            return 100-r
        else:
            return 100-r/2
        
    # 待补充
    # 剧变反应
    def reaction(self):
        e = self.source.attributePanel['元素精通']
        e_skill = self.skill.element
        e_target = self.target.elementalAura
        if e_target[0] == "无":
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
        damage = self.attack() * self.damageMultipiler() * (1 + self.damageBonus()/100) * (1 + self.criticalBracket()/100) * self.defense() * (self.resistance()/100) * self.reaction()
        return damage

