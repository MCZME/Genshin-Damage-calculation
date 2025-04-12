from character.INAZUMA.inazuma import Inazuma


class KaedeharaKazuha(Inazuma):
    ID = 33
    def __init__(self, level=1, skill_params=..., constellation=0):
        super().__init__(KaedeharaKazuha.ID, level, skill_params, constellation)

    def _init_character(self):
        super()._init_character()

Kaedehara_Kazuha_table = {
    'id': KaedeharaKazuha.ID,
    'name': '枫原万叶',
    'type': '单手剑',
    'element': '风',
    'rarity': 5,
    'association':'稻妻',
    # 'normalAttack': {'攻击次数': 3},
    # 'chargedAttack': {},
    # 'plungingAttack': {'攻击距离':['高空', '低空']},
    # 'skill': {},
    # 'burst': {}
}
