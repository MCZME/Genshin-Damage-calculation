from character import *
from weapon.Catalyst import catalyst
from weapon.Claymore import claymore
from weapon.Polearm import polearm
from weapon.Sword import sword
from weapon.Bow import bow


CharacterClassMap = {
    cls.ID: cls
    for name, cls in globals().items()
    if isinstance(cls, type) and hasattr(cls, 'ID') and cls.__module__[:9] == 'character'
}

WeaponClassMap = {}
WeaponClassMap.update(catalyst)
WeaponClassMap.update(claymore)
WeaponClassMap.update(polearm)
WeaponClassMap.update(sword)
WeaponClassMap.update(bow)
