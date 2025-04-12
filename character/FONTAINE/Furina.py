from character.FONTAINE.fontaine import Fontaine


class Furina(Fontaine):
    ID = 75
    def __init__(self, level=1, skill_params=..., constellation=0):
        super().__init__(Furina.ID, level, skill_params, constellation)

    def _init_character(self):
        super()._init_character()

Furina_table = {
    'id': Furina.ID,
    'name': '芙宁娜',
    'type': '单手剑',
    'element': '水',
    'rarity': 5,
    'association':'枫丹',
    # 'normalAttack': {'攻击次数': 3},
    # 'chargedAttack': {},
    # 'plungingAttack': {'攻击距离':['高空', '低空']},
    # 'skill': {},
    # 'burst': {}
}
