__all__ = []

weapon_table = {}

from weapon.Polearm import polearm
from weapon.Claymore import claymore
from weapon.Catalyst import catalyst
from weapon.Bow import bow
from weapon.Sword import sword

weapon_table['长柄武器'] = list(polearm.keys())
weapon_table['双手剑'] = list(claymore.keys())
weapon_table['单手剑'] = list(sword.keys())
weapon_table['弓'] = list(bow.keys())
weapon_table['法器'] = list(catalyst.keys())
