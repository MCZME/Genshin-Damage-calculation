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
        self.damageMultipiler = damage_multiplier  # 兼容旧代码命名，未来应改为 snake_case
        self.element = element
        self.damageType = damage_type
        self.name = name
        self.damage: float = 0.0
        self.baseValue: Union[str, Tuple[str, str]] = '攻击力'
        self.reaction_type: Optional[Tuple[str, Enum]] = None
        self.reaction_data: Optional[Any] = None
        self.data: Dict[str, Any] = kwargs
        self.panel: Dict[str, Any] = {}
        self.hit_type: Optional[Any] = None
        
        # Source/Target 将在事件处理时注入
        self.source = None
        self.target = None

    def setSource(self, source):
        self.source = source

    def setTarget(self, target):
        self.target = target

    def setBaseValue(self, base_value):
        self.baseValue = base_value

    def setReaction(self, reaction_type, reaction_data):
        self.reaction_type = reaction_type
        self.reaction_data = reaction_data

    def setDamageData(self, key, value):
        self.data[key] = value

    def setPanel(self, key, value):
        self.panel[key] = value

    def setHitType(self, hit_type):
        self.hit_type = hit_type
