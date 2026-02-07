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

        # 1. 基础白值 (合并入角色基础攻击力)
        self.base_atk: float = 0.0
        
        # 2. 静态副词条属性 (合并入绿字百分比/固定值)
        self.static_stats: Dict[str, float] = {}

        if base_data:
            self.name = base_data.get("name", "Unknown")
            self.base_atk = base_data.get("base_atk", 0.0)
            
            # 处理副词条 (例如: 暴击率, 元素精通)
            sub_name = base_data.get("secondary_attribute")
            sub_val = base_data.get("secondary_value", 0.0)
            if sub_name:
                self.static_stats[sub_name] = sub_val
        else:
            self.name = "Unknown"

    def apply_static_stats(self) -> None:
        """[核心重构] 将武器的基础数值应用到角色面板。"""
        panel = self.character.attribute_panel
        
        # 1. 合并攻击力白值
        panel["攻击力"] += self.base_atk
        
        # 2. 合并副词条
        for attr, value in self.static_stats.items():
            if attr in panel:
                panel[attr] += value

    def skill(self) -> None:
        """激活武器技能特效 (子类实现，主要用于注册事件监听)。"""
        pass

    def update(self) -> None:
        """生命周期驱动 (由 CombatSpace 调用)。"""
        pass

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "level": self.level, "lv": self.lv, "name": self.name, "base_atk": self.base_atk}