from character.FONTAINE.charlotte.char import CHARLOTTE

# 角色配置表 (用于 UI 和模拟配置)
Charlotte_table = {
    'id': 74,
    'name': '夏洛蒂',
    'type': '法器',
    'element': '冰',
    'rarity': 4,
    'association': '枫丹',
    'normalAttack': {'攻击次数': 3},
    'chargedAttack': {},
    'skill': {'释放时间': ['长按', '点按']},
    'burst': {}
}

__all__ = ['CHARLOTTE', 'Charlotte_table']
