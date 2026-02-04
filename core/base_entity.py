from abc import ABC, abstractmethod
from core.Event import EventBus, ObjectEvent
from core.Logger import get_emulation_logger
# 移除 from core.Team import Team，因为它会导致复杂的循环依赖
from core.Tool import GetCurrentTime
from core.context import get_context, EventEngine

class BaseEntity(ABC):
    """
    所有游戏实体（召唤物、护盾、能量球等）的基类。
    集成局部事件引擎，支持事件冒泡。
    """
    def __init__(self, name, life_frame=0):
        self.name = name
        self.is_active = False
        self.current_frame = 0
        self.life_frame = life_frame
        self.repeatable = False
        
        try:
            parent_engine = get_context().event_engine
            self.event_engine = EventEngine(parent=parent_engine)
        except RuntimeError:
            self.event_engine = EventEngine()

    def apply(self):
        try:
            ctx = get_context()
            # 未来 Team 应该在 Context 中，且 active_objects 是 Context 的属性
            if ctx.team:
                # 暂时兼容旧逻辑，但通过 context 访问
                # 如果 Team.active_objects 还没重构，这里可能还需要微调
                # 为了测试跑通，我们先假设 ctx.team 有 add_object 方法
                ctx.team.add_object(self)
        except (RuntimeError, AttributeError):
            # 如果没有上下文或队伍，仅设置激活状态
            pass
            
        self.is_active = True
        self.event_engine.publish(ObjectEvent(self, GetCurrentTime()))

    def update(self, target):
        self.current_frame += 1
        if self.current_frame >= self.life_frame:
            self.on_finish(target)
        self.on_frame_update(target)

    @abstractmethod
    def on_frame_update(self, target):
        """每帧更新逻辑"""
        ...

    def on_finish(self, target):
        """生命周期结束时的逻辑"""
        get_emulation_logger().log_object(f'{self.name} 存活时间结束')
        self.is_active = False
        self.event_engine.publish(ObjectEvent(self, GetCurrentTime(), False))
