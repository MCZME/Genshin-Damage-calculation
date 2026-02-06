from typing import Any
from core.effect.base import BaseEffect
from core.event import EventHandler, EventType, GameEvent
import core.tool as T
from weapon.weapon import Weapon
from core.registry import register_weapon

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

    def on_stack_added(self, other: "STWHealthBoostEffect"):
        curr_time = T.get_current_time()
        if curr_time - self.last_trigger > self.interval:
            if self.stack < 2:
                self._update_panel(-1)
                self.stack += 1
                self._update_panel(1)
            self.last_trigger = curr_time
            self.duration = self.max_duration

    def _update_panel(self, sign: int):
        panel = getattr(self.owner, "attribute_panel", getattr(self.owner, "attribute_panel", {}))
        panel["生命值%"] = panel.get("生命值%", 0) + sign * self.bonus * self.stack

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

    def on_stack_added(self, other: "STWElementSkillBoostEffect"):
        curr_time = T.get_current_time()
        if curr_time - self.last_trigger > self.interval:
            if self.stack < 3:
                self.stack += 1
            self.last_trigger = curr_time
            self.duration = self.max_duration

    def handle_event(self, event: GameEvent):
        if event.data["character"] == self.owner:
            damage = event.data["damage"]
            from core.action.damage import DamageType
            d_type = getattr(damage, "damage_type", getattr(damage, "damage_type", None))
            if d_type == DamageType.SKILL:
                damage.panel["伤害加成"] += self.bonus * self.stack
                damage.setDamageData(self.name, self.bonus * self.stack)

@register_weapon("静水流涌之辉", "单手剑")
class SplendorOfTranquilWaters(Weapon, EventHandler):
    ID = 49
    def __init__(self, character, level=1, lv=1):
        super().__init__(character, SplendorOfTranquilWaters.ID, level, lv)

    def skill(self):
        self.event_engine.subscribe(EventType.AFTER_HEALTH_CHANGE, self)

    def handle_event(self, event: GameEvent):
        if event.event_type == EventType.AFTER_HEALTH_CHANGE and event.data["amount"] != 0:
            if event.data["character"] == self.character:
                STWElementSkillBoostEffect(self.character).apply()
            else:
                STWHealthBoostEffect(self.character).apply()