from abc import ABC, abstractmethod
from typing import Optional
from core.context import SimulationContext, EventEngine

class GameSystem(ABC):
    """
    游戏核心子系统基类。
    负责处理特定领域的逻辑（伤害、反应、能量等）。
    """
    def __init__(self):
        self.context: Optional[SimulationContext] = None
        self.engine: Optional[EventEngine] = None

    def initialize(self, context: SimulationContext):
        """系统初始化，注入 Context 并注册事件"""
        self.context = context
        self.engine = context.event_engine
        self.register_events(self.engine)

    @abstractmethod
    def register_events(self, engine: EventEngine):
        """在此处注册该系统关心的事件"""
        pass
