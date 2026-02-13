from abc import ABC
from enum import Enum, auto
from typing import Any, Optional
from core.logger import get_emulation_logger
from core.tool import get_current_time

class StackingRule(Enum):
    REFRESH = auto()    # 刷新持续时间 (默认)
    ADD = auto()        # 增加层数
    INDEPENDENT = auto() # 独立存在

class BaseEffect(ABC):
    """
    效果基类。
    支持完整的生命周期管理与去全局化 Context。
    """
    def __init__(self, owner: Any, name: str, duration: float = 0, 
                 stacking_rule: StackingRule = StackingRule.REFRESH):
        self.owner = owner          # 效果持有者 (Character 或 Target)
        self.name = name
        self.duration = duration    # 剩余帧数 (float('inf') 为永久)
        self.max_duration = duration
        self.stacking_rule = stacking_rule
        self.is_active = False
        self.start_frame = 0

    def apply(self):
        """应用效果的入口逻辑"""
        # 处理堆叠逻辑
        existing = self._find_existing()
        if existing:
            if self.stacking_rule == StackingRule.REFRESH:
                existing.duration = max(existing.duration, self.duration)
                return
            elif self.stacking_rule == StackingRule.ADD:
                existing.on_stack_added(self)
                return
            # INDEPENDENT 模式下继续执行新增

        self.is_active = True
        self.start_frame = get_current_time()
        self.owner.add_effect(self)
        self.on_apply()
        get_emulation_logger().log_effect(self.owner, self.name, action="获得")

    def remove(self):
        """移除效果"""
        if not self.is_active:
            return
        self.is_active = False
        self.on_remove()
        self.owner.remove_effect(self)
        get_emulation_logger().log_effect(self.owner, self.name, action="结束")

    def update(self, target: Any):
        """每一帧的驱动逻辑"""
        if not self.is_active:
            return

        # 处理持续时间
        if self.duration != float('inf'):
            self.duration -= 1
            if self.duration <= 0:
                self.remove()
                return

        # 触发每帧钩子
        self.on_tick(target)

    def _find_existing(self) -> Optional['BaseEffect']:
        """在 owner 身上查找同名效果"""
        if not hasattr(self.owner, 'active_effects'):
            return None
        return next((e for e in self.owner.active_effects if e.name == self.name and isinstance(e, self.__class__)), None)

    # -----------------------------------------------------
    # 生命周期钩子 (子类重写)
    # -----------------------------------------------------
    def on_apply(self): pass
    def on_remove(self): pass
    def on_tick(self, target: Any): pass
    def on_stack_added(self, other: 'BaseEffect'): pass
