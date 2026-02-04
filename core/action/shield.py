from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from core.base_entity import BaseEntity

class Shield:
    def __init__(self, base_multiplier: float):
        self.base_multiplier = base_multiplier
        self.shield_value: float = 0
        self.base_value: Optional[str] = None # '生命值', '防御力' 等
        
        self.source: Optional['BaseEntity'] = None

    def set_source(self, source: 'BaseEntity'):
        self.source = source

    def set_base_value(self, base_value: str):
        self.base_value = base_value
