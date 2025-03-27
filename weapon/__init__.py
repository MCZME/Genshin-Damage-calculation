__all__ = []

weapon_table = {}

from weapon.Polearm import polearm
from weapon.Claymore import claymore
from weapon.Catalyst import catalyst
from weapon.Bow import bow
from weapon.Sword import sword

weapon_table['长柄武器'] = polearm
weapon_table['双手剑'] = claymore
weapon_table['法器'] = catalyst
weapon_table['弓'] = bow
weapon_table['单手剑'] = sword
