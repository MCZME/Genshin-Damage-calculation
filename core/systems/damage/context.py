"""伤害计算上下文模块。"""

from __future__ import annotations
from typing import Any, TYPE_CHECKING

from core.systems.contract.modifier import ModifierRecord

if TYPE_CHECKING:
    from core.systems.contract.damage import Damage


class DamageContext:
    """伤害计算上下文 (V2.5 审计状态机)。"""

    def __init__(self, damage: Damage, source: Any, target: Any | None = None):
        self.damage = damage
        self.source = source
        self.target = target
        self.config = damage.config

        # 核心代数槽位 (根据 V2.5 审计规范定义)
        self.stats: dict[str, float] = {
            "固定伤害值加成": 0.0,
            "伤害加成": 0.0,
            "暴击率": 0.0,
            "暴击伤害": 0.0,
            "暴击乘数": 1.0,
            "防御区系数": 1.0,
            "抗性区系数": 1.0,
            "反应基础倍率": 1.0,
            "反应加成系数": 0.0,
            "元素精通": 0.0,
            "无视防御%": 0.0,
            "独立乘区%": 0.0,  # 对应规范 2.2 中的 【独立乘区%】
            "倍率加值%": 0.0,  # 对应规范 2.2 中的 【倍率加值%】
            # 月曜伤害专用槽位
            "基础伤害提升": 0.0,  # 月曜基础伤害提升%
            "月曜反应伤害提升": 0.0,  # 月曜反应造成的伤害提升%
            "月曜伤害擢升": 0.0,  # 月曜伤害擢升%（独立乘区）
        }
        self.audit_trail: list[ModifierRecord] = []
        self.final_result: float = 0.0
        self.is_crit: bool = False

    def add_modifier(
        self, source: str, stat: str, value: float, op: str = "ADD", audit: bool = True
    ) -> None:
        """更新数值并同步审计。"""
        if stat not in self.stats:
            self.stats[stat] = 0.0 if op == "ADD" else 1.0

        if op == "ADD":
            self.stats[stat] += value
        elif op == "MULT":
            self.stats[stat] *= value
        elif op == "SET":
            self.stats[stat] = value

        if not audit:
            return

        from core.context import get_context
        m_id = 0
        try:
            m_id = get_context().get_next_modifier_id()
        except Exception:
            pass

        self.audit_trail.append(ModifierRecord(m_id, source, stat, value, op))
