from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Dict, List

# --------------------------
# 事件类型枚举
# --------------------------
class EventType(Enum):
    BEFORE_DAMAGE = auto()       # 伤害计算前
    AFTER_DAMAGE = auto()        # 伤害计算后
    BEFORE_ATTACK = auto()        # 攻击力计算前
    AFTER_ATTACK = auto()         # 攻击力计算后
    BEFORE_DAMAGE_MULTIPLIER = auto()  # 伤害倍率计算前
    AFTER_DAMAGE_MULTIPLIER = auto()   # 伤害倍率计算后
    BEFORE_DAMAGE_BONUS = auto()  # 伤害加成计算前
    AFTER_DAMAGE_BONUS = auto()   # 伤害加成计算后
    BEFORE_CRITICAL = auto()      # 暴击伤害计算前
    AFTER_CRITICAL = auto()       # 暴击伤害计算后
    BEFORE_DEFENSE = auto()       # 防御力计算前
    AFTER_DEFENSE = auto()       # 防御力计算后
    BEFORE_RESISTANCE = auto()   # 抗性计算前
    AFTER_RESISTANCE = auto()    # 抗性计算后
    BEFORE_REACTION = auto()     # 反应加成计算前
    AFTER_REACTION = auto()      # 反应加成计算后

    CHARACTER_SWITCH = auto()   # 角色切换

# --------------------------
# 事件类
# --------------------------
class GameEvent:
    def __init__(self, event_type: EventType, **kwargs):
        self.event_type = event_type
        self.data = kwargs        # 扩展数据
        self.cancelled = False    # 是否取消事件

class DamageEvent(GameEvent):
    def __init__(self, source, target, damage, **kwargs):
        super().__init__(EventType.AFTER_DAMAGE, source=source, target=target, damage=damage, **kwargs)

class CharacterSwitchEvent(GameEvent):
    def __init__(self, old_character, new_character, **kwargs):
        super().__init__(EventType.CHARACTER_SWITCH, old_character=old_character, new_character=new_character, **kwargs)

# --------------------------
# 事件处理器接口
# --------------------------
class EventHandler(ABC):
    @abstractmethod
    def handle_event(self, event: GameEvent):
        pass

# --------------------------
# 事件总线（单例）
# --------------------------
class EventBus:
    _instance = None
    _handlers: Dict[EventType, List[EventHandler]] = {}

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def subscribe(cls, event_type: EventType, handler: EventHandler):
        if event_type not in cls._handlers:
            cls._handlers[event_type] = []
        cls._handlers[event_type].append(handler)

    @classmethod
    def publish(cls, event: GameEvent):
        if event.event_type in cls._handlers:
            for handler in cls._handlers[event.event_type]:
                if event.cancelled:
                    break
                handler.handle_event(event)
