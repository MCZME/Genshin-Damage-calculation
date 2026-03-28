from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Any
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

    # 元素反应
    AFTER_ELEMENTAL_REACTION = auto()

    # 周期性反应 Tick
    ELECTRO_CHARGED_TICK = auto()
    BURNING_TICK = auto()

    # 月曜反应事件
    AFTER_LUNAR_BLOOM = auto()
    AFTER_LUNAR_CHARGED = auto()
    AFTER_LUNAR_CRYSTALLIZE = auto()

    # 月曜特殊事件
    LUNAR_CHARGED_TICK = auto()  # 雷暴云攻击
    LUNAR_CRYSTALLIZE_ATTACK = auto()  # 月笼谐奏攻击

    # 月曜资源事件
    GRASS_DEW_GAIN = auto()  # 草露获取
    GRASS_DEW_CONSUME = auto()  # 草露消耗

    # 哥伦比娅核心机制事件
    GRAVITY_INTERFERENCE = auto()  # 引力干涉触发
    LUNAR_DAMAGE_DEALT = auto()  # 月曜伤害造成

    # 生命与状态
    AFTER_HEALTH_CHANGE = auto()
    BEFORE_HEAL = auto()
    AFTER_HEAL = auto()
    BEFORE_HURT = auto()
    AFTER_HURT = auto()

    # 生命周期与修饰符
    ON_MODIFIER_ADDED = auto()
    ON_MODIFIER_REMOVED = auto()
    ON_EFFECT_ADDED = auto()
    ON_EFFECT_REMOVED = auto()
    ON_SHIELD_CHANGE = auto()

    # 动作与状态
    BEFORE_NORMAL_ATTACK = auto()
    BEFORE_CHARGED_ATTACK = auto()
    BEFORE_PLUNGING_ATTACK = auto()
    BEFORE_SKILL = auto()
    AFTER_SKILL = auto()
    BEFORE_BURST = auto()
    AFTER_BURST = auto()
    BEFORE_DASH = auto()
    BEFORE_JUMP = auto()
    BEFORE_FALLING = auto()

    # 资源与纳塔机制
    BEFORE_ENERGY_CHANGE = auto()
    AFTER_ENERGY_CHANGE = auto()
    AFTER_CHARACTER_SWITCH = auto()
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
    data: dict[str, Any] = field(default_factory=dict)

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
