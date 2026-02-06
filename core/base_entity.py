from typing import Any, Optional

class BaseEntity:
    """
    仿真世界中的实体基类（召唤物、领域、护盾等）。
    """
    def __init__(self, name: str, life_frame: float = float('inf'), context=None):
        self.name = name
        self.life_frame = life_frame
        self.current_frame = 0
        self.is_active = True
        
        # 优先使用传入的 context，否则尝试自动获取
        if context:
            self.ctx = context
            self.event_engine = self.ctx.event_engine
        else:
            from core.context import get_context
            try:
                self.ctx = get_context()
                self.event_engine = self.ctx.event_engine
            except RuntimeError:
                self.ctx = None
                self.event_engine = None

    def apply(self):
        """应用实体到队伍中"""
        if self.ctx and self.ctx.team:
            self.ctx.team.add_object(self)

    def update(self, target: Any):
        """每帧驱动逻辑"""
        if not self.is_active: return
        
        self.current_frame += 1
        if self.current_frame >= self.life_frame:
            self.on_finish(target)
            self.is_active = False
            return
            
        self.on_frame_update(target)

    def on_frame_update(self, target: Any): pass
    def on_finish(self, target: Any): pass

# ---------------------------------------------------------
# 兼容性别名 (用于旧代码中对 BaseObject/baseObject 的引用)
# ---------------------------------------------------------
BaseObject = BaseEntity
baseObject = BaseEntity