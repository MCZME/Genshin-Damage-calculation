from __future__ import annotations
from typing import Any

from core.effect.common import TalentEffect
from core.event import EventType, GameEvent
from core.systems.contract.healing import Healing, HealingType
from core.tool import get_current_time
from core.systems.utils import AttributeCalculator
from character.FONTAINE.furina.data import MECHANISM_CONFIG


class EndlessWaltz(TalentEffect):
    """
    固有天赋一：停不了的圆舞。
    当场上角色受到溢出治疗且来源非芙宁娜时，全队周期性回复血量。
    """

    def __init__(self):
        super().__init__("停不了的圆舞", unlock_level=20)
        self.active_timer = 0
        self.heal_timer = 0

    def on_apply(self):
        if self.character and self.character.event_engine:
            self.character.event_engine.subscribe(EventType.AFTER_HEAL, self)

    def handle_event(self, event: GameEvent):
        if event.event_type == EventType.AFTER_HEAL:
            # 条件：来源非芙宁娜 且 是当前场上角色 且 产生溢出
            heal_obj: Healing | None = event.data.get("healing")
            target = event.data.get("target")
            if (
                heal_obj
                and heal_obj.source != self.character
                and target
                and getattr(target, "on_field", False)
                and event.data.get("overflow", 0) > 0
            ):
                self.active_timer = 240
                self.heal_timer = 0

    def on_frame_update(self):
        if not self.is_active or self.active_timer <= 0:
            return

        self.active_timer -= 1
        self.heal_timer += 1

        if self.heal_timer >= 120:
            self._execute_team_healing()
            self.heal_timer = 0

    def _execute_team_healing(self):
        """为全队恢复 2% 最大生命值。"""
        ctx = getattr(self.character, "ctx", None)
        if not ctx or not ctx.team:
            return

        members = ctx.team.get_members()
        for m in members:
            max_hp = AttributeCalculator.get_final_hp(m)
            heal_val = max_hp * 0.02

            heal_obj = Healing(
                base_multiplier=0, healing_type=HealingType.PASSIVE, name=self.name
            )
            heal_obj.final_value = heal_val

            if self.character and self.character.event_engine:
                self.character.event_engine.publish(
                    GameEvent(
                        EventType.BEFORE_HEAL,
                        get_current_time(),
                        source=self.character,
                        data={
                            "character": self.character,
                            "target": m,
                            "healing": heal_obj,
                        },
                    )
                )


class UnheardConfession(TalentEffect):
    """
    固有天赋二：无人听的自白。
    基于 HP 上限提升沙龙成员伤害，缩短歌者治疗间隔。
    """

    def __init__(self):
        super().__init__("无人听的自白", unlock_level=60)

    def on_apply(self):
        if self.character and self.character.event_engine:
            self.character.event_engine.subscribe(EventType.BEFORE_CALCULATE, self)

    def handle_event(self, event: GameEvent):
        if event.event_type == EventType.BEFORE_CALCULATE:
            dmg_ctx = event.data.get("damage_context")
            if dmg_ctx and dmg_ctx.damage.config.icd_group in [
                "FurinaSalonShared",
                "None",
            ]:
                bonus = self._calculate_dmg_bonus()
                dmg_ctx.add_modifier(
                    source="固有天赋：无人听的自白",
                    stat="独立乘区系数",
                    value=1 + bonus,
                    op="MULT",
                )

    def on_frame_update(self):
        if not self.is_active or not self.character:
            return

        reduction_perc = self._calculate_heal_interval_reduction()
        base_interval = MECHANISM_CONFIG["SKILL_HEAL_INTERVAL"]
        setattr(
            self.character,
            "singer_interval_override",
            int(base_interval * (1 - reduction_perc))
        )

    def _calculate_dmg_bonus(self) -> float:
        """每 1000 点提升 0.7%，上限 28%。"""
        hp = AttributeCalculator.get_final_hp(self.character)
        bonus = (hp // 1000) * 0.007
        return min(0.28, bonus)

    def _calculate_heal_interval_reduction(self) -> float:
        """每 1000 点降低 0.4%，上限 16%。"""
        hp = AttributeCalculator.get_final_hp(self.character)
        reduction = (hp // 1000) * 0.004
        return min(0.16, reduction)
