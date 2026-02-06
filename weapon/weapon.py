from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional

from core.context import get_context

if TYPE_CHECKING:
    from character.character import Character
    from core.context import EventEngine, SimulationContext


class Weapon:
    """
    武器基类。
    所有具体武器类均继承自此类，遵循 snake_case 命名规范与类型标注。
    """

    def __init__(
        self,
        character: Character,
        id: int = 1,
        level: int = 1,
        lv: int = 1,
        base_data: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化武器。

        Args:
            character: 武器持有者。
            id: 武器 ID。
            level: 武器等级 (1-90)。
            lv: 精炼等级 (1-5)。
            base_data: 从数据源注入的基础数值。
        """
        self.character = character
        self.id = id
        self.level = level
        self.lv = lv

        # 初始化上下文
        try:
            self.ctx: Optional[SimulationContext] = get_context()
            self.event_engine: Optional[EventEngine] = (
                self.ctx.event_engine if self.ctx else None
            )
        except RuntimeError:
            self.ctx = None
            self.event_engine = None

        self.attribute_data: Dict[str, float] = {
            "攻击力": 0.0,
            "元素精通": 0.0,
            "暴击率": 0.0,
            "暴击伤害": 0.0,
            "治疗加成": 0.0,
            "受治疗加成": 0.0,
            "元素充能效率": 0.0,
            "生命值%": 0.0,
            "攻击力%": 0.0,
            "防御力%": 0.0,
            "火元素伤害加成": 0.0,
            "水元素伤害加成": 0.0,
            "雷元素伤害加成": 0.0,
            "冰元素伤害加成": 0.0,
            "岩元素伤害加成": 0.0,
            "风元素伤害加成": 0.0,
            "草元素伤害加成": 0.0,
            "物理伤害加成": 0.0,
        }

        if base_data:
            self.name = base_data.get("name", "Unknown")
            # 填充基础数值
            self.attribute_data["攻击力"] = base_data.get("base_atk", 0.0)

            # 处理副词条
            sub_name = base_data.get("secondary_attribute")
            sub_val = base_data.get("secondary_value", 0.0)
            if sub_name and sub_name in self.attribute_data:
                self.attribute_data[sub_name] = sub_val
        else:
            self.name = "Unknown"

    def update_panel(self) -> None:
        """将武器属性应用到角色的面板上。"""
        # 兼容处理：尝试获取 attribute_panel 或 attributePanel
        panel = getattr(
            self.character,
            "attribute_panel",
            getattr(self.character, "attributePanel", {}),
        )
        for attr, value in self.attribute_data.items():
            if attr in panel:
                panel[attr] += value

    def skill(self) -> None:
        """激活武器技能效果（子类重写）。"""
        pass

    def update(self, target: Any) -> None:
        """每帧驱动逻辑（子类重写）。"""
        pass

    def to_dict(self) -> Dict[str, Any]:
        """将武器状态序列化。"""
        return {"id": self.id, "level": self.level, "lv": self.lv, "name": self.name}