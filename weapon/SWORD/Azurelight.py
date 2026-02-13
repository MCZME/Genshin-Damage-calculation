from typing import Any
from core.event import EventHandler, EventType, GameEvent
from weapon.weapon import Weapon
from core.registry import register_weapon
from core.effect.base import BaseEffect

class AzurelightEffect(BaseEffect):
    """武器: 苍耀 的效果实现。"""
    def __init__(self, owner: Any, lv: int):
        super().__init__(owner, "苍耀效果", duration=10*60)
        self.lv = lv
        self.bonus = [12, 15, 18, 21, 24]

    def on_apply(self) -> None:
        panel = self.character.attribute_panel
        for e in ["火", "水", "雷", "风", "冰", "岩", "草"]:
            key = f"{e}元素伤害加成"
            panel[key] = panel.get(key, 0.0) + self.bonus[self.lv-1]

    def on_remove(self) -> None:
        panel = self.character.attribute_panel
        for e in ["火", "水", "雷", "风", "冰", "岩", "草"]:
            key = f"{e}元素伤害加成"
            panel[key] = panel.get(key, 0.0) - self.bonus[self.lv-1]

@register_weapon("苍耀", "单手剑")
class Azurelight(Weapon, EventHandler):
    """武器: 苍耀 的实现类。"""
    ID = 216
    def __init__(self, character: Any, level: int = 1, lv: int = 1):
        super().__init__(character, Azurelight.ID, level, lv)

    def skill(self) -> None:
        self.event_engine.subscribe(EventType.BEFORE_SKILL, self)

    def handle_event(self, event: GameEvent) -> None:
        if event.data["character"] == self.character:
            AzurelightEffect(self.character, self.lv).apply()
