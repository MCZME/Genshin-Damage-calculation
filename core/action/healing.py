from enum import Enum, auto
from typing import Optional, Union, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from core.base_entity import BaseEntity

class HealingType(Enum):
    NORMAL = auto()      # 普通治疗
    SKILL = auto()       # 技能治疗
    BURST = auto()       # 爆发治疗
    PASSIVE = auto()     # 被动治疗

class Healing:
    def __init__(self, base_multiplier: Union[float, Tuple[float, float]], 
                 healing_type: HealingType, name: str, multiplier_provider: str = '来源'):
        self.base_multiplier = base_multiplier   # 基础倍率
        self.healing_type = healing_type         # 治疗类型
        self.final_value: float = 0              # 最终治疗量
        self.base_value: str = '攻击力'
        self.name = name
        self.multiplier_provider = multiplier_provider # '来源' 或 '目标'

        self.source: Optional['BaseEntity'] = None
        self.target: Optional['BaseEntity'] = None

    def set_source(self, source: 'BaseEntity'):
        self.source = source

    def set_target(self, target: 'BaseEntity'):
        self.target = target
