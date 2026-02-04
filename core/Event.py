from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union
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

    # 元素反应 (通用)
    BEFORE_ELEMENTAL_REACTION = auto()
    AFTER_ELEMENTAL_REACTION = auto()
    
    # 具体反应
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

    # 生命与防御
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

    # 动作相关
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

    # 资源与系统
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
# 事件基类
# --------------------------
@dataclass
class GameEvent:
    event_type: EventType
    frame: int
    source: Any = None # 事件产生的实体
    cancelled: bool = False
    propagation_stopped: bool = False
    data: Dict[str, Any] = field(default_factory=dict)

    def stop_propagation(self):
        self.propagation_stopped = True

    def cancel(self):
        self.cancelled = True

# --------------------------
# 核心事件定义 (使用 Dataclass 替代 kwargs)
# --------------------------

@dataclass
class DamageEvent(GameEvent):
    target: Any = None
    damage: Any = None
    # 构造函数微调：兼容旧代码的 source, target, damage 传参
    def __post_init__(self):
        self.data["character"] = self.source
        self.data["target"] = self.target
        self.data["damage"] = self.damage

@dataclass
class HealEvent(GameEvent):
    target: Any = None
    healing: Any = None
    def __post_init__(self):
        self.data["character"] = self.source
        self.data["target"] = self.target
        self.data["healing"] = self.healing

@dataclass
class EnergyChargeEvent(GameEvent):
    amount: Any = None
    is_fixed: bool = False
    is_alone: bool = False
    def __post_init__(self):
        self.data["character"] = self.source
        self.data["amount"] = self.amount
        self.data["is_fixed"] = self.is_fixed
        self.data["is_alone"] = self.is_alone

@dataclass
class CharacterSwitchEvent(GameEvent):
    old_character: Any = None
    new_character: Any = None
    def __post_init__(self):
        self.data["old_character"] = self.old_character
        self.data["new_character"] = self.new_character

@dataclass
class ElementalReactionEvent(GameEvent):
    elemental_reaction: Any = None
    def __post_init__(self):
        self.data["elementalReaction"] = self.elemental_reaction # 暂时保留旧 key 兼容 System

# 为了保持兼容性，后续几十个简单的 Event 类暂时使用 GameEvent 代理
# 新架构下应鼓励直接使用 GameEvent(EventType.XXX, ...)

class FrameEndEvent(GameEvent):
    def __init__(self, frame):
        super().__init__(EventType.FRAME_END, frame)

# --------------------------
# 代理与接口
# --------------------------

class EventHandler(ABC):
    @abstractmethod
    def handle_event(self, event: GameEvent):
        pass

from core.context import get_context

class EventBus:
    """
    [Deprecated] 静态代理类。
    """
    @classmethod
    def subscribe(cls, event_type: EventType, handler: EventHandler):
        get_context().event_engine.subscribe(event_type, handler)

    @classmethod
    def unsubscribe(cls, event_type: EventType, handler: EventHandler):
        get_context().event_engine.unsubscribe(event_type, handler)

    @classmethod
    def publish(cls, event: GameEvent):
        get_context().event_engine.publish(event)

    @classmethod
    def clear(cls):
        get_context().event_engine.clear()
