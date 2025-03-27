__all__ = ['Varesa','MAVUIKA','Iansan','CITLALI']

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