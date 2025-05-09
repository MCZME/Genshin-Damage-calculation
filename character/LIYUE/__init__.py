__all__ = ['liyue_table', 'XiangLing']

liyue_table = {}

def add(name,character,table):
    __all__.append(character)
    table['skip'] = {'时间':9999}
    liyue_table[name] = table

from .Xiangling import xiangling_table
add('香菱','XiangLing',xiangling_table)
from .Xingqiu import xingqiu_table
add('行秋','Xingqiu',xingqiu_table)
from .Yelan import yelan_table
add('夜兰','Yelan',yelan_table)

