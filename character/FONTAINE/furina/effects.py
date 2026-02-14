from typing import Any

from core.effect.base import BaseEffect, StackingRule
from core.event import EventType, GameEvent
from core.logger import get_emulation_logger
from core.systems.utils import AttributeCalculator
from core.mechanics.aura import Element
from core.systems.contract.healing import Healing, HealingType
from core.tool import get_current_time
from character.FONTAINE.furina.data import ELEMENTAL_BURST_DATA


class FurinaFanfareEffect(BaseEffect):
    """
    芙宁娜核心效果：普世欢腾 (Fanfare)。
    负责全队血量监控、气氛值叠层及属性转化。
    """

    def __init__(self, owner: Any, duration: int):
        # owner 是芙宁娜实例
        super().__init__(
            owner, "普世欢腾", duration=duration, stacking_rule=StackingRule.REFRESH
        )

        # 从技能倍率表中提取转化比例
        self.skill_lv = owner.skill_params[2]  # 大招等级
        self.dmg_ratio = ELEMENTAL_BURST_DATA["气氛值转化提升伤害比例"][1][
            self.skill_lv - 1
        ]
        self.heal_ratio = ELEMENTAL_BURST_DATA["气氛值转化受治疗加成比例"][1][
            self.skill_lv - 1
        ]

        self.points: float = 0.0
        self.max_points: float = ELEMENTAL_BURST_DATA["气氛值叠层上限"][1][
            self.skill_lv - 1
        ]
        self.efficiency: float = 1.0  # 叠层效率 (C2 修改)

        if owner.constellation_level >= 1:
            self.points = 150.0
            self.max_points = 400.0

        if owner.constellation_level >= 2:
            self.efficiency = 3.5

    def on_apply(self):
        self.owner.event_engine.subscribe(EventType.AFTER_HURT, self)
        self.owner.event_engine.subscribe(EventType.AFTER_HEAL, self)
        self.owner.event_engine.subscribe(EventType.BEFORE_CALCULATE, self)
        self.owner.event_engine.subscribe(EventType.BEFORE_HEAL, self)

    def on_remove(self):
        self.owner.event_engine.unsubscribe(EventType.AFTER_HURT, self)
        self.owner.event_engine.unsubscribe(EventType.AFTER_HEAL, self)
        self.owner.event_engine.unsubscribe(EventType.BEFORE_CALCULATE, self)
        self.owner.event_engine.unsubscribe(EventType.BEFORE_HEAL, self)

        self.owner.dynamic_modifiers = [
            m for m in self.owner.dynamic_modifiers if m.source != "芙宁娜C2生命加成"
        ]

    def handle_event(self, event: GameEvent):
        if event.event_type in [EventType.AFTER_HURT, EventType.AFTER_HEAL]:
            self._process_hp_change(event)

        elif event.event_type == EventType.BEFORE_CALCULATE:
            dmg_ctx = event.data.get("damage_context")
            if dmg_ctx:
                bonus = self.points * self.dmg_ratio
                source_label = f"芙宁娜-气氛值({int(self.points)}层)"
                dmg_ctx.add_modifier(source=source_label, stat="伤害加成", value=bonus)

        elif event.event_type == EventType.BEFORE_HEAL:
            target = event.data.get("target")
            if target:
                bonus = self.points * self.heal_ratio
                event.data["fanfare_heal_bonus"] = bonus

    def _process_hp_change(self, event: GameEvent):
        target = event.target
        amount = 0.0

        if event.event_type == EventType.AFTER_HURT:
            amount = event.data.get("amount", 0.0)
        else:
            amount = getattr(event, "healing").final_value

        if amount <= 0:
            return

        max_hp = AttributeCalculator.get_hp(target)
        if max_hp <= 0:
            return

        change_points = (amount / max_hp) * 100.0 * self.efficiency

        old_points = self.points
        self.points += change_points

        if self.owner.constellation_level >= 2:
            if self.points > self.max_points:
                overflow = self.points - self.max_points
                hp_bonus = min(140.0, overflow * 0.35)
                self.owner.dynamic_modifiers = [
                    m
                    for m in self.owner.dynamic_modifiers
                    if m.source != "芙宁娜C2生命加成"
                ]
                self.owner.add_modifier(
                    source="芙宁娜C2生命加成", stat="生命值%", value=hp_bonus
                )

        self.points = min(
            self.points,
            1000.0 if self.owner.constellation_level >= 2 else self.max_points,
        )

        if int(self.points) != int(old_points):
            get_emulation_logger().log_effect(
                self.owner,
                f"气氛值叠加: {old_points:.1f} -> {self.points:.1f}",
                action="更新",
            )

    def on_tick(self, target: Any):
        pass


class FurinaCenterOfAttentionHeal(BaseEffect):
    """C6 荒性分支产生的全队持续治疗效果。"""

    def __init__(self, owner: Any):
        super().__init__(owner, "万众瞩目·愈", duration=174)  # 2.9s
        self.timer = 0

    def on_tick(self, target: Any):
        self.timer += 1
        if self.timer >= 60:
            self._do_team_heal()
            self.timer = 0

    def _do_team_heal(self):
        hp = AttributeCalculator.get_hp(self.owner)
        heal_val = hp * 0.04

        if self.owner.ctx.space and self.owner.ctx.space.team:
            team = self.owner.ctx.space.team.get_members()
            for m in team:
                heal_obj = Healing(
                    base_multiplier=(0, heal_val),
                    healing_type=HealingType.PASSIVE,
                    name="万众瞩目·愈",
                )
                heal_obj.set_scaling_stat("生命值")

                self.owner.event_engine.publish(
                    GameEvent(
                        EventType.BEFORE_HEAL,
                        get_current_time(),
                        source=self.owner,
                        data={
                            "character": self.owner,
                            "target": m,
                            "healing": heal_obj,
                        },
                    )
                )


class FurinaCenterOfAttentionEffect(BaseEffect):
    """
    芙宁娜 6 命效果状态机：万众瞩目 (Center of Attention)。
    """

    def __init__(self, owner: Any, duration: int = 600):
        super().__init__(
            owner, "万众瞩目", duration=duration, stacking_rule=StackingRule.REFRESH
        )
        self.remaining_hits = 6

    def on_apply(self):
        # 1. 注入水附魔 (最高优先级)
        self.owner.infusion_manager.add_infusion(
            element=Element.HYDRO,
            priority=100,
            source=self.name,
            can_be_overridden=False,
        )
        self.owner.event_engine.subscribe(EventType.BEFORE_CALCULATE, self)
        self.owner.event_engine.subscribe(EventType.AFTER_DAMAGE, self)

    def on_remove(self):
        self.owner.infusion_manager.remove_infusion(self.name)
        self.owner.event_engine.unsubscribe(EventType.BEFORE_CALCULATE, self)
        self.owner.event_engine.unsubscribe(EventType.AFTER_DAMAGE, self)

    def handle_event(self, event: GameEvent):
        if self.remaining_hits <= 0:
            return

        if event.event_type == EventType.BEFORE_CALCULATE:
            self._apply_flat_damage(event)
        elif event.event_type == EventType.AFTER_DAMAGE:
            self._process_hit_effect(event)

    def _apply_flat_damage(self, event: GameEvent):
        dmg_ctx = event.data.get("damage_context")
        if not dmg_ctx:
            return

        from core.action.attack_tag_resolver import AttackTagResolver, AttackCategory

        tags = AttackTagResolver.resolve_categories(
            dmg_ctx.config.attack_tag, dmg_ctx.config.extra_attack_tags
        )
        if not (
            AttackCategory.NORMAL in tags
            or AttackCategory.CHARGED in tags
            or AttackCategory.PLUNGING in tags
        ):
            return

        max_hp = AttributeCalculator.get_hp(self.owner)
        bonus_val = max_hp * 0.18
        if self.owner.arkhe_mode == "芒":
            bonus_val = max_hp * 0.43

        dmg_ctx.add_modifier(self.name, "固定伤害值加成", bonus_val)

    def _process_hit_effect(self, event: GameEvent):
        if self.remaining_hits <= 0:
            return
        dmg = event.data.get("damage")
        if not dmg or dmg.source != self.owner:
            return

        from core.action.attack_tag_resolver import AttackTagResolver, AttackCategory

        tags = AttackTagResolver.resolve_categories(
            dmg.config.attack_tag, dmg.config.extra_attack_tags
        )
        if not (
            AttackCategory.NORMAL in tags
            or AttackCategory.CHARGED in tags
            or AttackCategory.PLUNGING in tags
        ):
            return

        mode = self.owner.arkhe_mode
        if mode == "荒":
            FurinaCenterOfAttentionHeal(self.owner).apply()
        else:
            self._trigger_pneuma_consume()

        self.remaining_hits -= 1
        if self.remaining_hits <= 0:
            self.remove()

    def _trigger_pneuma_consume(self):
        """芒形态：全队扣血。"""
        if self.owner.ctx.space and self.owner.ctx.space.team:
            for m in self.owner.ctx.space.team.get_members():
                self.owner.event_engine.publish(
                    GameEvent(
                        EventType.BEFORE_HURT,
                        get_current_time(),
                        source=self.owner,
                        data={
                            "character": self.owner,
                            "target": m,
                            "amount": m.current_hp * 0.01,
                            "ignore_shield": True,
                        },
                    )
                )
