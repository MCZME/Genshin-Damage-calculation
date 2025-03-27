__all__ = ['fontaine_table']

fontaine_table = {}

def _add(name,character,table):
    __all__.append(character)
    table['skip'] = {'时间':9999}
    fontaine_table[name] = table

from character.FONTAINE.CHEVREUSE import chevreuse_table
_add('夏沃蕾','CHEVREUSE',chevreuse_table)
