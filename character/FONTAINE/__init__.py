__all__ = ['fontaine_table']

fontaine_table = {}

def _add(name,character,table):
    __all__.append(character)
    table['skip'] = {'时间':9999}
    fontaine_table[name] = table

from character.FONTAINE.Chevreuse import chevreuse_table
_add('夏沃蕾','CHEVREUSE',chevreuse_table)
from character.FONTAINE.Furina import Furina_table
_add('芙宁娜','Furina',Furina_table)
from character.FONTAINE.Neuvillette import Neuvillette_table
_add('那维莱特','Neuvillette',Neuvillette_table)
from character.FONTAINE.Escoffier import Escoffier_table
_add('爱可菲','Escoffier',Escoffier_table)
from character.FONTAINE.Charlotte import Charlotte_table
_add('夏洛蒂','CHARLOTTE',Charlotte_table)
