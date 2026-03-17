from typing import Any, Dict
from core.effect.base import BaseEffect, StackingRule
from core.event import EventType, GameEvent

class TestAuditSuiteEffect(BaseEffect):
    """
    测试专用效果器：审计全乘区套件 (攻击者侧)。
    参考 StatModifierEffect 的数据结构，但使用事件驱动以支持审计追踪。
    """

    def __init__(self, owner: Any, mode: str = "全乘区Buff"):
        super().__init__(
            owner, "审计验证套件", duration=600, stacking_rule=StackingRule.REFRESH
        )
        self.mode = mode
        # 定义不同模式下的属性增益字典
        self.mode_stats: Dict[str, Dict[str, float]] = {
            "全乘区Buff": {
                "独立乘区%": 20.0,
                "倍率加值%": 15.0,
                "固定伤害值加成": 5000.0,
                "伤害加成": 40.0,
                "暴击率": 100.0,
                "暴击伤害": 150.0
            }
        }

    def on_apply(self):
        if self.owner.event_engine:
            self.owner.event_engine.subscribe(EventType.BEFORE_CALCULATE, self)

    def on_remove(self):
        if self.owner.event_engine:
            self.owner.event_engine.unsubscribe(EventType.BEFORE_CALCULATE, self)

    def handle_event(self, event: GameEvent):
        if event.event_type == EventType.BEFORE_CALCULATE:
            dmg_ctx = event.data.get("damage_context")
            if not dmg_ctx or self.mode not in self.mode_stats:
                return

            # 只有当此效果的持有者（self.owner）是当前伤害的来源时才生效
            if dmg_ctx.source == self.owner:
                stats = self.mode_stats[self.mode]
                for stat, value in stats.items():
                    op = "SET" if stat == "暴击率" else "ADD"
                    # 瞬时注入：显式设置 audit=True 以进入审计链
                    dmg_ctx.add_modifier(self.name, stat, value, op, audit=True)

class TestDebuffEffect(BaseEffect):
    """
    测试专用减益效果：极致穿透 (目标侧)。
    参考 StatModifierEffect 结构，模拟减防/减抗。
    """
    def __init__(self, owner: Any, stats: Dict[str, float] = None):
        super().__init__(
            owner, "极致穿透减益", duration=600, stacking_rule=StackingRule.REFRESH
        )
        self.stats = stats or {
            "防御力%": -30.0,
            "火元素抗性": -40.0
        }
        self.modifier_records = []

    def on_apply(self):
        m1 = self.owner.add_modifier(self.name, "防御力%", self.stats.get("防御力%", 0.0), "ADD")
        m2 = self.owner.add_modifier(self.name, "火元素抗性", self.stats.get("火元素抗性", 0.0), "ADD")
        self.modifier_records.extend([m1, m2])

    def on_remove(self):
        for modifier in self.modifier_records:
            self.owner.remove_modifier(modifier)
        self.modifier_records.clear()
