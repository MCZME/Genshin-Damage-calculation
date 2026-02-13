from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Any, Dict
from dataclasses import dataclass, field

# --------------------------
# 事件类型枚举
# --------------------------
class EventType(Enum):
    # 核心循环
    FRAME_END = auto()
    
    # 伤害相关
    BEFORE_DAMAGE = auto()
    AFTER_DAMAGE = auto()
    BEFORE_CALCULATE = auto()
    AFTER_CALCULATE = auto()
    BEFORE_ATTACK = auto()
    AFTER_ATTACK = auto()
    BEFORE_DAMAGE_MULTIPLIER = auto()
    AFTER_DAMAGE_MULTIPLIER = auto()
    BEFORE_DAMAGE_BONUS = auto()
    AFTER_DAMAGE_BONUS = auto()
    BEFORE_CRITICAL = auto()
    AFTER_CRITICAL = auto()
    BEFORE_CRITICAL_BRACKET = auto()
    AFTER_CRITICAL_BRACKET = auto()
    BEFORE_DEFENSE = auto()
    AFTER_DEFENSE = auto()
    BEFORE_RESISTANCE = auto()
    AFTER_RESISTANCE = auto()
    BEFORE_INDEPENDENT_DAMAGE = auto()
    AFTER_INDEPENDENT_DAMAGE = auto()
    BEFORE_FIXED_DAMAGE = auto()
    AFTER_FIXED_DAMAGE = auto()

    # 元素反应
    BEFORE_ELEMENTAL_REACTION = auto()
    AFTER_ELEMENTAL_REACTION = auto()
    BEFORE_FREEZE = auto()
    AFTER_FREEZE = auto()
    BEFORE_QUICKEN = auto()
    AFTER_QUICKEN = auto()
    BEFORE_AGGRAVATE = auto()
    AFTER_AGGRAVATE = auto()
    BEFORE_SPREAD = auto()
    AFTER_SPREAD = auto()
    BEFORE_VAPORIZE = auto()
    AFTER_VAPORIZE = auto()
    BEFORE_MELT = auto()
    AFTER_MELT = auto()
    BEFORE_OVERLOAD = auto()
    AFTER_OVERLOAD = auto()
    BEFORE_SWIRL = auto()
    AFTER_SWIRL = auto()
    BEFORE_SHATTER = auto()
    AFTER_SHATTER = auto()
    BEFORE_BURNING = auto()
    AFTER_BURNING = auto()
    BEFORE_CRYSTALLIZE = auto()
    AFTER_CRYSTALLIZE = auto()
    BEFORE_SUPERCONDUCT = auto()
    AFTER_SUPERCONDUCT = auto()
    BEFORE_ELECTRO_CHARGED = auto()
    AFTER_ELECTRO_CHARGED = auto()
    BEFORE_BLOOM = auto()
    AFTER_BLOOM = auto()
    BEFORE_HYPERBLOOM = auto()
    AFTER_HYPERBLOOM = auto()
    BEFORE_BURGEON = auto()
    AFTER_BURGEON = auto()
    
    # 周期性反应 Tick
    ELECTRO_CHARGED_TICK = auto()
    BURNING_TICK = auto()

    # 生命、防御与状态
    BEFORE_HEALTH_CHANGE = auto()
    AFTER_HEALTH_CHANGE = auto()
    BEFORE_HEAL = auto()
    AFTER_HEAL = auto()
    BEFORE_HURT = auto()
    AFTER_HURT = auto()
    BEFORE_SHIELD_CREATION = auto()
    AFTER_SHIELD_CREATION = auto()

    # 对象生命周期
    OBJECT_CREATE = auto()
    OBJECT_DESTROY = auto()

    # 动作与状态
    BEFORE_NORMAL_ATTACK = auto()
    AFTER_NORMAL_ATTACK = auto()
    BEFORE_CHARGED_ATTACK = auto()
    AFTER_CHARGED_ATTACK = auto()
    BEFORE_PLUNGING_ATTACK = auto()
    AFTER_PLUNGING_ATTACK = auto()
    BEFORE_SKILL = auto()
    AFTER_SKILL = auto()
    BEFORE_BURST = auto()
    AFTER_BURST = auto()
    BEFORE_DASH = auto()
    AFTER_DASH = auto()
    BEFORE_JUMP = auto()
    AFTER_JUMP = auto()
    BEFORE_FALLING = auto()
    AFTER_FALLING = auto()

    # 资源与纳塔机制
    BEFORE_ENERGY_CHANGE = auto()
    AFTER_ENERGY_CHANGE = auto()
    BEFORE_CHARACTER_SWITCH = auto()
    AFTER_CHARACTER_SWITCH = auto()
    BEFORE_NIGHTSOUL_BLESSING = auto()
    AFTER_NIGHTSOUL_BLESSING = auto()
    BEFORE_NIGHT_SOUL_CHANGE = auto()
    AFTER_NIGHT_SOUL_CHANGE = auto()
    NIGHTSOUL_BURST = auto()

# --------------------------
# 核心事件类
# --------------------------
@dataclass
class GameEvent:
    """
    通用游戏事件。
    V2.4 架构中统一使用此基类，不再使用特定子类。
    """
    event_type: EventType
    frame: int
    source: Any = None
    cancelled: bool = False
    propagation_stopped: bool = False
    data: Dict[str, Any] = field(default_factory=dict)

    def stop_propagation(self):
        self.propagation_stopped = True

    def cancel(self):
        self.cancelled = True

# --------------------------
# 代理与接口
# --------------------------

class EventHandler(ABC):
    @abstractmethod
    def handle_event(self, event: GameEvent):
        pass
