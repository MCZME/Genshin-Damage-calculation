from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from core.entities.base_entity import BaseEntity

class Shield:
    def __init__(self, base_multiplier: float):
        self.base_multiplier = base_multiplier
        self.shield_value: float = 0
        self.scaling_stat: Optional[str] = None # '生命值', '防御力' 等
        
        self.source: Optional['BaseEntity'] = None

    def set_source(self, source: 'BaseEntity'):
        self.source = source

    def set_scaling_stat(self, scaling_stat: str):
        self.scaling_stat = scaling_stat
