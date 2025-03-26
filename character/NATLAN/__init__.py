__all__ = ['natlan_character']

natlan_character = {}

def add(name,character,table):
    __all__.append(character)
    natlan_character[name] = table

from character.NATLAN.VARESA import Varesa_table
add('瓦雷莎','Varesa',Varesa_table)
from character.NATLAN.MAVUIKA import mavuika_table
add('玛维卡','MAVUIKA',mavuika_table)
