__all__ = ['Varesa','MAVUIKA','Iansan','CITLALI','XiangLing','CHEVREUSE','BENNETT']

character_table = {}

def _add(table):
    for k, v in table.items():
        character_table[k] = v

from character.NATLAN import natlan_character
from character.NATLAN.VARESA import Varesa
from character.NATLAN.MAVUIKA import MAVUIKA
from character.NATLAN.IANSAN import Iansan
from character.NATLAN.CITLALI import CITLALI
_add(natlan_character)
from character.LIYUE import liyue_table
from character.LIYUE.Xiangling import XiangLing
_add(liyue_table)
from character.FONTAINE import fontaine_table
from character.FONTAINE.CHEVREUSE import CHEVREUSE
_add(fontaine_table)
from character.MONDSTADT import mondstadt_table
from character.MONDSTADT.BENNETT import BENNETT
_add(mondstadt_table)