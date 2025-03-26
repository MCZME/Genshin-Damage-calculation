__all__ = []

weapon_table = []

from weapon.Polearm import polearm
from weapon.Claymore import claymore
from weapon.Catalyst import catalyst

weapon_table.extend(polearm)
weapon_table.extend(claymore)
weapon_table.extend(catalyst)
