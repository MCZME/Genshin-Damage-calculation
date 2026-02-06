from typing import Any, Dict
from core.effect.base import BaseEffect
from core.event import EventHandler, EventType, GameEvent
from core.action.damage import DamageType

class LuminescenceEffect(BaseEffect, EventHandler):
    """回声之林夜话 - 永照的流辉"""
    def __init__(self, owner: Any, initial_stack: int):
        super().__init__(owner, "永照的流辉", duration=6*60)
        self.stack = initial_stack
        # 记录每种来源的到期时间
        self.stack_sources: Dict[Any, int] = {}

    def on_apply(self):
        self.owner.event_engine.subscribe(EventType.BEFORE_DAMAGE_BONUS, self)

    def on_remove(self):
        self.owner.event_engine.unsubscribe(EventType.BEFORE_DAMAGE_BONUS, self)

    def add_source(self, source_type: Any):
        self.stack_sources[source_type] = 6*60
        self._recalculate_stack()

    def _recalculate_stack(self):
        # 简化逻辑：每一帧在 update 中处理
        pass

    def on_tick(self, target: Any):
        to_remove = []
        for s in self.stack_sources:
            self.stack_sources[s] -= 1
            if self.stack_sources[s] <= 0: to_remove.append(s)
        
        for s in to_remove:
            del self.stack_sources[s]
            # 根据来源类型减少层数逻辑...
            
        if not self.stack_sources:
            self.remove()

    def handle_event(self, event: GameEvent):
        damage = event.data['damage']
        if event.source == self.owner and damage.damage_type == DamageType.PLUNGING:
            damage.panel['伤害加成'] += 15 * self.stack
