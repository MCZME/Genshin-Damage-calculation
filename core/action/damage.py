from enum import Enum
from typing import Any, Dict, Optional, Tuple, Union

class DamageType(Enum):
    NORMAL = "普通攻击"
    CHARGED = "重击"
    SKILL = "元素战技"
    BURST = "元素爆发"
    PLUNGING = "下落攻击"
    REACTION = "剧变反应"

class Damage:
    def __init__(self, damage_multiplier: Any, element: Tuple[str, Any], damage_type: DamageType, name: str, **kwargs):
        self.damage_multiplier = damage_multiplier
        self.element = element
        self.damage_type = damage_type
        self.name = name
        self.damage: float = 0.0
        self.base_value: Union[str, Tuple[str, str]] = '攻击力'
        self.reaction_type: Optional[Tuple[str, Enum]] = None
        self.reaction_data: Optional[Any] = None
        self.data: Dict[str, Any] = kwargs
        self.panel: Dict[str, Any] = {}
        self.hit_type: Optional[Any] = None
        
        # Source/Target 将在事件处理时注入
        self.source = None
        self.target = None

    def set_source(self, source):
        self.source = source

    def set_target(self, target):
        self.target = target

    def set_base_value(self, base_value):
        self.base_value = base_value

    def set_reaction(self, reaction_type, reaction_data):
        self.reaction_type = reaction_type
        self.reaction_data = reaction_data

    def set_damage_data(self, key, value):
        self.data[key] = value

    def set_panel(self, key, value):
        self.panel[key] = value

    def set_hit_type(self, hit_type):
        self.hit_type = hit_type
