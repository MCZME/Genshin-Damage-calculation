from typing import Any
from core.effect.base import BaseEffect, StackingRule
from core.event import EventHandler, EventType, GameEvent
from core.tool import GetCurrentTime

class STWHealthBoostEffect(BaseEffect):
    """静水流涌之辉 - 生命值提升效果"""
    def __init__(self, owner: Any):
        super().__init__(owner, "静水流涌之辉_生命值", duration=6*60)
        self.bonus = 14
        self.stack = 0
        self.last_trigger = 0
        self.interval = 0.2*60

    def on_apply(self):
        self.stack = 1
        self._update_panel(1)

    def on_remove(self):
        self._update_panel(-1)

    def on_stack_added(self, other: 'STWHealthBoostEffect'):
        if GetCurrentTime() - self.last_trigger > self.interval:
            if self.stack < 2:
                self._update_panel(-1) # 先移除旧层数
                self.stack += 1
                self._update_panel(1) # 再增加新层数
            self.last_trigger = GetCurrentTime()
            self.duration = self.max_duration

    def _update_panel(self, sign: int):
        self.owner.attribute_panel['生命值%'] += sign * self.bonus * self.stack

class STWElementSkillBoostEffect(BaseEffect, EventHandler):
    """静水流涌之辉 - 元素战技伤害提升"""
    def __init__(self, owner: Any):
        super().__init__(owner, "静水流涌之辉_元素战技", duration=6*60)
        self.bonus = 8
        self.stack = 0
        self.last_trigger = 0
        self.interval = 0.2*60

    def on_apply(self):
        self.stack = 1
        self.owner.event_engine.subscribe(EventType.BEFORE_DAMAGE_BONUS, self)

    def on_remove(self):
        self.owner.event_engine.unsubscribe(EventType.BEFORE_DAMAGE_BONUS, self)

    def on_stack_added(self, other: 'STWElementSkillBoostEffect'):
        if GetCurrentTime() - self.last_trigger > self.interval:
            if self.stack < 3:
                self.stack += 1
            self.last_trigger = GetCurrentTime()
            self.duration = self.max_duration

    def handle_event(self, event: GameEvent):
        if event.source == self.owner:
            damage = event.data['damage']
            if damage.damage_type.value == '元素战技':
                damage.panel['伤害加成'] += self.bonus * self.stack
