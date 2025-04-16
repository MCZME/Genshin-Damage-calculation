from character.character import Character
from core.BaseClass import ChargedAttackSkill, ConstellationEffect, ElementalEnergy, EnergySkill, NormalAttackSkill, PlungingAttackSkill, SkillBase, TalentEffect

class NormalAttack(NormalAttackSkill):
    ...

class ChargedAttack(ChargedAttackSkill):
    ...

class PlungingAttack(PlungingAttackSkill):
    ...

class ElementalSkill(SkillBase):
    ...

class ElementalBurst(EnergySkill):
    ...

class PassiveSkillEffect_1(TalentEffect):
    ...

class PassiveSkillEffect_2(TalentEffect):
    ...

class ConstellationEffect_1(ConstellationEffect):
    ...

class ConstellationEffect_2(ConstellationEffect):
    ...

class ConstellationEffect_3(ConstellationEffect):
    ...

class ConstellationEffect_4(ConstellationEffect):
    ...

class ConstellationEffect_5(ConstellationEffect):
    ...

class ConstellationEffect_6(ConstellationEffect):
    ...

class CharacterName(Character):
    # 数据库ID
    ID = 0
    def __init__(self, level=1, skill_params=..., constellation=0):
        super().__init__(CharacterName.ID, level, skill_params, constellation)

    def _init_character(self):
        super()._init_character()
        self.elemental_energy = ElementalEnergy(self,('水',70)) # ('元素',能量上限)
        self.NormalAttack = NormalAttack(self.skill_params[0])
        self.ChargedAttack = ChargedAttack(self.skill_params[0])
        self.Skill = ElementalSkill(self.skill_params[1])
        self.Burst = ElementalBurst(self.skill_params[2])
        self.talent1 = PassiveSkillEffect_1()
        self.talent2 = PassiveSkillEffect_2()
        self.constellation_effects[0] = ConstellationEffect_1()
        self.constellation_effects[1] = ConstellationEffect_2()
        self.constellation_effects[2] = ConstellationEffect_3()
        self.constellation_effects[3] = ConstellationEffect_4()
        self.constellation_effects[4] = ConstellationEffect_5()
        self.constellation_effects[5] = ConstellationEffect_6()

characterName_table = {
    'id': CharacterName.ID,
    'name': '角色名',
    'type': '武器类型',
    'element': '元素',
    'rarity': '星级',
    'association':'所属地区',
    'normalAttack': {'攻击次数': 3},
    'chargedAttack': {},
    'plungingAttack': {'攻击距离':['高空', '低空']},
    'skill': {},
    'burst': {}
}