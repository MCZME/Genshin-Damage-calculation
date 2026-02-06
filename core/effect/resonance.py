from typing import Any
from core.effect.base import BaseEffect
from core.event import EventHandler, EventType, GameEvent
from core.tool import get_shield

class SwiftWindEffect(BaseEffect):
    """迅捷之风 (双风共鸣)"""
    def on_apply(self):
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
        # 订阅反应事件以触发动态精通提升
        self.owner.event_engine.subscribe(EventType.AFTER_BURNING, self)
        self.owner.event_engine.subscribe(EventType.AFTER_BLOOM, self)
        self.owner.event_engine.subscribe(EventType.AFTER_QUICKEN, self)

    def handle_event(self, event: GameEvent):
        # 简化版：仅更新计时器
        self.time_1 = 6 * 60

class SteadfastStoneEffect(BaseEffect, EventHandler):
    """坚定之岩 (双岩共鸣)"""
    def __init__(self, owner: Any):
        super().__init__(owner, "坚定之岩", duration=float('inf'))
        self.is_applied = False

    def on_apply(self):
        self.owner.event_engine.subscribe(EventType.AFTER_DAMAGE, self)

    def on_tick(self, target: Any):
        # 原版逻辑：护盾存在时提升 15% 伤害
        shield = get_shield()
        if not self.is_applied and shield:
            self.owner.attribute_panel['伤害加成'] += 15
            self.is_applied = True
        elif self.is_applied and not shield:
            self.owner.attribute_panel['伤害加成'] -= 15
            self.is_applied = False

    def handle_event(self, event: GameEvent):
        # 触发减岩抗效果
        if event.source == self.owner:
            from core.effect.debuff import ResistanceDebuffEffect
            ResistanceDebuffEffect(self.owner, "坚定之岩_减抗", ['岩'], 20, 15*60).apply()