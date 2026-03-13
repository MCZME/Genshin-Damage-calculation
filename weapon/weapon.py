from __future__ import annotations

from typing import TYPE_CHECKING, Any

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
        base_data: dict[str, Any] | None = None,
    ):
        self.character = character
        self.id = id
        self.level = level
        self.lv = lv

        try:
            self.ctx: SimulationContext | None = get_context()
            self.event_engine: EventEngine | None = (
                self.ctx.event_engine if self.ctx else None
            )
        except RuntimeError:
            self.ctx = None
            self.event_engine = None

        self.base_atk: float = 0.0
        self.static_stats: dict[str, float] = {}

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
        """通过审计链注入武器静态属性。"""
        # 武器基础攻击力注入攻击力乘区
        if self.base_atk > 0:
            self.character.add_modifier(
                source=f"武器-{self.name}",
                stat="攻击力",
                value=self.base_atk
            )
        # 副属性注入
        for attr, value in self.static_stats.items():
            if value > 0:
                self.character.add_modifier(
                    source=f"武器-{self.name}",
                    stat=attr,
                    value=value
                )

    def skill(self) -> None:
        pass

    def on_frame_update(self) -> None:
        """统一每帧逻辑更新接口"""
        pass

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "level": self.level,
            "lv": self.lv,
            "name": self.name,
            "base_atk": self.base_atk,
        }
