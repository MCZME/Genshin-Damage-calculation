from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional

from core.context import get_context

if TYPE_CHECKING:
    from character.character import Character
    from core.context import EventEngine, SimulationContext


class Weapon:
    """
    武器基类。
    """

    def __init__(
        self,
        character: Character,
        id: int = 1,
        level: int = 1,
        lv: int = 1,
        base_data: Optional[Dict[str, Any]] = None,
    ):
        self.character = character
        self.id = id
        self.level = level
        self.lv = lv

        try:
            self.ctx: Optional[SimulationContext] = get_context()
            self.event_engine: Optional[EventEngine] = (
                self.ctx.event_engine if self.ctx else None
            )
        except RuntimeError:
            self.ctx = None
            self.event_engine = None

        self.base_atk: float = 0.0
        self.static_stats: Dict[str, float] = {}

        if base_data:
            self.name = base_data.get("name", "Unknown")
            self.base_atk = base_data.get("base_atk", 0.0)
            sub_name = base_data.get("secondary_attribute")
            sub_val = base_data.get("secondary_value", 0.0)
            if sub_name:
                self.static_stats[sub_name] = sub_val
        else:
            self.name = "Unknown"

    def apply_static_stats(self) -> None:
        panel = self.character.attribute_panel
        panel["攻击力"] += self.base_atk
        for attr, value in self.static_stats.items():
            if attr in panel:
                panel[attr] += value

    def skill(self) -> None:
        pass

    def on_frame_update(self) -> None:
        """统一每帧逻辑更新接口"""
        pass

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "level": self.level, "lv": self.lv, "name": self.name, "base_atk": self.base_atk}
