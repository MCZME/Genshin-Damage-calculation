from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Dict, List

# --------------------------
# 事件类型枚举
# --------------------------
class EventType(Enum):
    BEFORE_DAMAGE = 1   # 伤害计算前
    AFTER_DAMAGE = 2    # 伤害施加后

# --------------------------
# 事件基类
# --------------------------
class GameEvent:
    def __init__(self, event_type: EventType, source, target, **kwargs):
        self.event_type = event_type
        self.source = source      # 事件来源（角色/技能）
        self.target = target      # 事件目标
        self.data = kwargs        # 扩展数据
        self.cancelled = False    # 是否取消事件

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
