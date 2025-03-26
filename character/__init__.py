__all__ = ['Varesa','MAVUIKA','Iansan']

character = {}

def _add(table):
    for k, v in table.items():
        character[k] = v

from NATLAN import natlan_character
from NATLAN.VARESA import Varesa
from NATLAN.MAVUIKA import MAVUIKA
from NATLAN.IANSAN import Iansan
_add(natlan_character)