from typing import Any
from core.effect.base import BaseEffect
from core.event import EventHandler, EventType, GameEvent
import core.tool as T
from weapon.weapon import Weapon
from core.registry import register_weapon

class RongHuaZhiGeEffect(BaseEffect):
    """荣花之歌 - 个人效果"""
    def __init__(self, owner: Any, lv: int):
        super().__init__(owner, "荣花之歌", duration=6*60)
        self.lv = lv
        self.defense_bonus = [8, 10, 12, 14, 16]
        self.damage_bonus = [10, 12.5, 15, 17.5, 20]
        self.stack = 0
        self.last_trigger = 0

    def on_apply(self):
        self.stack = 1
        self._update_panel(1)

    def on_remove(self):
        self._update_panel(-1)

    def on_stack_added(self, other: "RongHuaZhiGeEffect"):
        now = T.get_current_time()
        if now - self.last_trigger > 0.1*60:
            if self.stack < 2:
                self._update_panel(-1)
                self.stack += 1
                self._update_panel(1)
                if self.stack == 2:
                    # 触发全队效果
                    from core.team import Team
                    for char in Team.team:
                        RongHuaZhiGeTeamEffect(char, self.owner, self.lv).apply()
            self.last_trigger = now
            self.duration = self.max_duration

    def _update_panel(self, sign: int):
        panel = getattr(self.owner, "attribute_data", getattr(self.owner, "attribute_data", {}))
        panel["防御力%"] = panel.get("防御力%", 0) + sign * self.defense_bonus[self.lv-1] * self.stack
        for e in ["水", "火", "风", "雷", "冰", "岩"]:
            key = f"{e}元素伤害加成"
            panel[key] = panel.get(key, 0) + sign * self.damage_bonus[self.lv-1] * self.stack

class RongHuaZhiGeTeamEffect(BaseEffect):
    """荣花之歌 - 队伍效果"""
    def __init__(self, owner: Any, source_char: Any, lv: int):
        super().__init__(owner, "荣花之歌-队伍", duration=15*60)
        self.lv = lv
        self.bonus_per_1000 = [8, 10, 12, 14, 16]
        self.max_bonus = [25.6, 32, 38.4, 44.8, 51.2]
        self.val = self._calculate_val(source_char)

    def _calculate_val(self, source):
        # 简单计算，未来应使用 AttributeCalculator
        panel = getattr(source, "attribute_data", getattr(source, "attribute_data", {}))
        defense = (panel.get("防御力", 0) * (1 + panel.get("防御力%", 0)/100) + 
                   panel.get("固定防御力", 0))
        return min((defense/1000) * self.bonus_per_1000[self.lv-1], self.max_bonus[self.lv-1])

    def on_apply(self):
        panel = getattr(self.owner, "attribute_data", getattr(self.owner, "attribute_data", {}))
        for e in ["水", "火", "风", "雷", "冰", "岩"]:
            key = f"{e}元素伤害加成"
            panel[key] = panel.get(key, 0) + self.val

    def on_remove(self):
        panel = getattr(self.owner, "attribute_data", getattr(self.owner, "attribute_data", {}))
        for e in ["水", "火", "风", "雷", "冰", "岩"]:
            key = f"{e}元素伤害加成"
            panel[key] = panel.get(key, 0) - self.val

@register_weapon("岩峰巡歌", "单手剑")
class PeakPatrolSong(Weapon, EventHandler):
    ID = 52
    def __init__(self, character, level=1, lv=1):
        super().__init__(character, PeakPatrolSong.ID, level, lv)
        self.last_trigger_time = 0
        self.interval = 0.1 * 60
    
    def skill(self):
        self.event_engine.subscribe(EventType.AFTER_NORMAL_ATTACK, self)
        self.event_engine.subscribe(EventType.AFTER_PLUNGING_ATTACK, self)
    
    def handle_event(self, event: GameEvent):
        if event.data["character"] != self.character:
            return
            
        current_time = T.get_current_time()
        if current_time - self.last_trigger_time < self.interval:
            return
            
        if event.event_type in [EventType.AFTER_NORMAL_ATTACK, EventType.AFTER_PLUNGING_ATTACK]:
            RongHuaZhiGeEffect(self.character, self.lv).apply()
            self.last_trigger_time = current_time
