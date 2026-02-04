from core.base_entity import BaseEntity
from core.entities.arkhe import ArkheObject
from core.entities.energy import EnergyDropsObject
from core.entities.elemental_entities import LightningBladeObject, DendroCoreObject
from core.entities.combat_entities import ShatteredIceObject, ShieldObject

# ---------------------------------------------------------
# 兼容性导出
# ---------------------------------------------------------
BaseObject = BaseEntity
baseObject = BaseEntity

__all__ = [
    'BaseEntity', 'BaseObject', 'baseObject',
    'ArkheObject', 'EnergyDropsObject', 'LightningBladeObject',
    'DendroCoreObject', 'ShatteredIceObject', 'ShieldObject'
]
