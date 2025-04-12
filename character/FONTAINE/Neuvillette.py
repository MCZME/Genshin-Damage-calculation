from character.FONTAINE.fontaine import Fontaine


class Neuvillette(Fontaine):
    ID = 73

    def __init__(self, level=1, skill_params=..., constellation=0):
        super().__init__(Neuvillette.ID, level, skill_params, constellation)

    def _init_character(self):
        super()._init_character()

Neuvillette_table = {
    'id': Neuvillette.ID,
    'name': '那维莱特',
    'type': '法器',
    'element': '水',
    'rarity': 5,
    'association':'枫丹',
    # 'normalAttack': {'攻击次数': 3},
    # 'chargedAttack': {},
    # 'plungingAttack': {'攻击距离':['高空', '低空']},
    # 'skill': {},
    # 'burst': {}
}