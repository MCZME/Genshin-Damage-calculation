from enum import Enum, auto
from typing import Any, Optional
from core.context import get_context

class EntityState(Enum):
    """实体的生命周期状态"""
    INIT = auto()      # 初始化
    ACTIVE = auto()    # 活跃中
    FINISHING = auto() # 正在结束（触发销毁前逻辑）
    DESTROYED = auto() # 已彻底销毁

class BaseEntity:
    """
    仿真世界中的实体基类（召唤物、领域、护盾等）。
    负责生命周期驱动与状态管理。
    """
    def __init__(self, name: str, life_frame: float = float("inf"), context: Optional[Any] = None):
        self.name = name
        self.life_frame = life_frame
        self.current_frame = 0
        self.state = EntityState.ACTIVE
        
        # 属性注入
        if context:
            self.ctx = context
        else:
            try:
                self.ctx = get_context()
            except RuntimeError:
                self.ctx = None
        
        self.event_engine = self.ctx.event_engine if self.ctx else None

    @property
    def is_active(self) -> bool:
        return self.state == EntityState.ACTIVE

    def apply(self) -> None:
        """将实体注册到模拟环境中。"""
        if self.ctx and self.ctx.team:
            self.ctx.team.add_object(self)

    def update(self, target: Any) -> None:
        """
        每帧驱动逻辑。由 Simulator 调用。
        """
        if self.state != EntityState.ACTIVE:
            return
        
        self.current_frame += 1
        
        # 检查寿命
        if self.current_frame >= self.life_frame:
            self.finish(target)
            return
            
        self.on_frame_update(target)

    def finish(self, target: Any) -> None:
        """
        主动或被动结束实体生命周期。
        """
        if self.state != EntityState.ACTIVE:
            return
            
        self.state = EntityState.FINISHING
        self.on_finish(target)
        self.state = EntityState.DESTROYED
        
        # 通知环境清理
        # 实际移除逻辑通常由 Team 在一帧结束时统一处理，此处仅标记状态

    # -----------------------------------------------------
    # 生命周期钩子 (子类重写)
    # -----------------------------------------------------
    def on_frame_update(self, target: Any) -> None:
        """每一帧的业务逻辑实现。"""
        pass

    def on_finish(self, target: Any) -> None:
        """实体销毁时的业务逻辑实现。"""
        pass