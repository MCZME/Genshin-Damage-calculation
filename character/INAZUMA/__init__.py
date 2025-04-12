__all__ = ['inazuma_character']

def add(name,character,table):
    __all__.append(character)
    table['skip'] = {'时间':9999}
    inazuma_character[name] = table

inazuma_character = {}

from .KaedeharaKazuha import Kaedehara_Kazuha_table
add('枫原万叶','',Kaedehara_Kazuha_table)
