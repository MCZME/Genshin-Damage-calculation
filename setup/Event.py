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

    BEFORE_HEAL = auto()         # 治疗计算前
    AFTER_HEAL = auto()          # 治疗后

    BEFORE_NORMAL_ATTACK = auto()  # 普通攻击前
    AFTER_NORMAL_ATTACK = auto()   # 普通攻击后
    BEFORE_HEAVY_ATTACK = auto()  # 重击前
    AFTER_HEAVY_ATTACK = auto()   # 重击后
    BEFORE_SKILL = auto()        # 技能使用前
    AFTER_SKILL = auto()         # 技能使用后
    BEFORE_BURST = auto()        # 爆发使用前
    AFTER_BURST = auto()         # 爆发使用后

    CHARACTER_SWITCH = auto()   # 角色切换
    BEFORE_NIGHTSOUL_BLESSING = auto()  # 夜魂加持之前
    AFTER_NIGHTSOUL_BLESSING = auto()  # 夜魂加持结束后
    BEFORE_NIGHT_SOUL_CONSUMPTION = auto()  # 夜魂消耗之前
    AFTER_NIGHT_SOUL_CONSUMPTION = auto()  # 夜魂消耗之后
    NightsoulBurst = auto()  # 夜魂迸发

# --------------------------
# 事件类
# --------------------------
class GameEvent:
    def __init__(self, event_type: EventType, frame, **kwargs):
        self.event_type = event_type
        self.frame = frame
        self.data = kwargs        # 扩展数据
        self.cancelled = False    # 是否取消事件

class DamageEvent(GameEvent):
    def __init__(self, source, target, damage, frame, before=True, **kwargs):
        if before:
            super().__init__(EventType.BEFORE_DAMAGE, frame=frame, character=source, target=target, damage=damage, **kwargs)
        else:
            super().__init__(EventType.AFTER_DAMAGE, frame=frame, character=source, target=target, damage=damage, **kwargs)

class CharacterSwitchEvent(GameEvent):
    def __init__(self, old_character, new_character, frame, **kwargs):
        super().__init__(EventType.CHARACTER_SWITCH, frame=frame, old_character=old_character, new_character=new_character, **kwargs)

class NightSoulBlessingEvent(GameEvent):
    def __init__(self, character, frame, before=True, **kwargs):
        super().__init__(EventType.BEFORE_NIGHTSOUL_BLESSING if before else EventType.AFTER_NIGHTSOUL_BLESSING, frame=frame, character=character, **kwargs)

class NormalAttackEvent(GameEvent):
    def __init__(self, character, frame, before=True, **kwargs):
        if before:
            super().__init__(EventType.BEFORE_NORMAL_ATTACK, frame=frame, character=character, **kwargs)
        else:
            super().__init__(EventType.AFTER_NORMAL_ATTACK, frame=frame, character=character, **kwargs)

class HeavyAttackEvent(GameEvent):
    def __init__(self, character, frame, before=True, **kwargs):
        if before:
            super().__init__(EventType.BEFORE_HEAVY_ATTACK, frame=frame, character=character, **kwargs)
        else:
            super().__init__(EventType.AFTER_HEAVY_ATTACK, frame=frame, character=character, **kwargs)

class NightSoulConsumptionEvent(GameEvent):
    def __init__(self, character, amount, frame, before=True, **kwargs):
        super().__init__(EventType.BEFORE_NIGHT_SOUL_CONSUMPTION if before else EventType.AFTER_NIGHT_SOUL_CONSUMPTION,
                        frame=frame, character=character, amount=amount, **kwargs)

class ElementalBurstEvent(GameEvent):
    def __init__(self, character, frame, before=True, **kwargs):
        if before:
            super().__init__(EventType.BEFORE_BURST, frame=frame, character=character, **kwargs)
        else:
            super().__init__(EventType.AFTER_BURST, frame=frame, character=character, **kwargs)

class ElementalSkillEvent(GameEvent):
    def __init__(self, character, frame, before=True, **kwargs):
        if before:
            super().__init__(EventType.BEFORE_SKILL, frame=frame, character=character, **kwargs)
        else:
            super().__init__(EventType.AFTER_SKILL, frame=frame, character=character, **kwargs)

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
    def unsubscribe(cls, event_type: EventType, handler: EventHandler):
        if event_type in cls._handlers:
            cls._handlers[event_type].remove(handler)
            if not cls._handlers[event_type]:
                del cls._handlers[event_type]

    @classmethod
    def publish(cls, event: GameEvent):
        if event.event_type in cls._handlers:
            for handler in cls._handlers[event.event_type]:
                if event.cancelled:
                    break
                handler.handle_event(event)
