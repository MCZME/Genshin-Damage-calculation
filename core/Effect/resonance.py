from typing import Any
from core.effect.base import BaseEffect
from core.event import EventHandler, EventType, GameEvent

class SwiftWindEffect(BaseEffect):
    """迅捷之风 (双风共鸣)"""
    def on_apply(self):
        # 冷却时间减少 5%
        if hasattr(self.owner, 'Skill'): self.owner.Skill.cd = int(0.95 * self.owner.Skill.cd)
        if hasattr(self.owner, 'Burst'): self.owner.Burst.cd = int(0.95 * self.owner.Burst.cd)

    def on_remove(self):
        if hasattr(self.owner, 'Skill'): self.owner.Skill.cd = int(self.owner.Skill.cd / 0.95)
        if hasattr(self.owner, 'Burst'): self.owner.Burst.cd = int(self.owner.Burst.cd / 0.95)

class CreepingGrassEffect(BaseEffect, EventHandler):
    """蔓生之草 (双草共鸣)"""
    def __init__(self, owner: Any):
        super().__init__(owner, "蔓生之草", duration=float('inf'))
        self.time_1 = 0
        self.time_2 = 0

    def on_apply(self):
        self.owner.attribute_panel['元素精通'] += 50
        self.owner.event_engine.subscribe(EventType.AFTER_BURNING, self)
        # 其他订阅...

    def handle_event(self, event: GameEvent):
        # 处理精通提升逻辑...
        pass

    def on_tick(self, target: Any):
        # 处理内部计时器倒计时...
        pass
