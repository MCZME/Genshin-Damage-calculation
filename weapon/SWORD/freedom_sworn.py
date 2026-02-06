from typing import Any
from core.logger import get_emulation_logger
from core.action.damage import DamageType
from core.event import EventBus, EventHandler, EventType, GameEvent
from core.team import Team
import core.tool as T
from weapon.weapon import Weapon
from core.registry import register_weapon
from core.effect.base import BaseEffect

class FreedomSwornEffect(BaseEffect, EventHandler):
    """苍古自由之誓效果"""
    def __init__(self, owner: Any, lv: int):
        super().__init__(owner, "苍古自由之誓", duration=12*60)
        self.lv = lv
        self.dmg_bonus = [16, 20, 24, 28, 32]
        self.atk_bonus = [20, 25, 30, 35, 40]

    def on_apply(self):
        # 兼容旧代码使用 attribute_panel
        panel = getattr(self.owner, "attribute_panel", getattr(self.owner, "attribute_panel", {}))
        panel["攻击力%"] = panel.get("攻击力%", 0) + self.atk_bonus[self.lv-1]
        self.owner.event_engine.subscribe(EventType.BEFORE_DAMAGE_BONUS, self)

    def on_remove(self):
        panel = getattr(self.owner, "attribute_panel", getattr(self.owner, "attribute_panel", {}))
        panel["攻击力%"] -= self.atk_bonus[self.lv-1]
        self.owner.event_engine.unsubscribe(EventType.BEFORE_DAMAGE_BONUS, self)

    def handle_event(self, event: GameEvent):
        if event.data["character"] == self.owner:
            damage = event.data["damage"]
            # 兼容旧代码 damage_type 和 damage_type
            d_type = getattr(damage, "damage_type", getattr(damage, "damage_type", None))
            if d_type in [DamageType.NORMAL, DamageType.CHARGED, DamageType.PLUNGING]:
                damage.panel["伤害加成"] += self.dmg_bonus[self.lv-1]
                damage.setDamageData(self.name, self.dmg_bonus[self.lv-1])

@register_weapon("苍古自由之誓", "单手剑")
class FreedomSworn(Weapon, EventHandler):
    ID = 42
    def __init__(self, character, level=1, lv=1):
        super().__init__(character, FreedomSworn.ID, level, lv)
        self.last_tigger_time = 0
        self.stacks = 0
        self.lasr_effect_time = -20*60

    def skill(self):
        self.character.attribute_panel["伤害加成"] += 10
        self.event_engine.subscribe(EventType.AFTER_ELEMENTAL_REACTION, self)

    def handle_event(self, event: GameEvent):
        if event.event_type == EventType.AFTER_ELEMENTAL_REACTION:
            if event.data["elementalReaction"].source == self.character:
                curr_time = T.get_current_time()
                if curr_time - self.last_tigger_time > 0.5*60 and curr_time - self.lasr_effect_time > 20*60:
                    self.stacks += 1
                    self.last_tigger_time = curr_time
                    if self.stacks == 2:
                        for c in Team.team:
                            FreedomSwornEffect(c, self.lv).apply()
                        self.stacks = 0
                        self.lasr_effect_time = curr_time