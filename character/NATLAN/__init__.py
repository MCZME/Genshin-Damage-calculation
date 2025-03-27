__all__ = ['natlan_character']

natlan_character = {}

def add(name,character,table):
    __all__.append(character)
    natlan_character[name] = table

from character.NATLAN.VARESA import Varesa_table
add('瓦雷莎','Varesa',Varesa_table)
from character.NATLAN.MAVUIKA import mavuika_table
add('玛维卡','MAVUIKA',mavuika_table)
from character.NATLAN.IANSAN import iansan_table
add('伊安珊','IANSAN',iansan_table)
from character.NATLAN.CITLALI import citlali_table
add('茜特菈莉','CITLALI',citlali_table)
