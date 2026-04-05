"""帷间夜曲 - 5星法器"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from core.effect.base import BaseEffect, StackingRule
from core.event import EventType, GameEvent
from core.tool import get_current_time
from core.action.attack_tag_resolver import AttackTagResolver
from weapon.weapon import Weapon
from core.registry import register_weapon

if TYPE_CHECKING:
    from character.character import Character


class NectarsDionysusEffect(BaseEffect):
    """
    丰饶海的神酒效果。

    持续12秒，提供：
    - 额外生命值上限
    - 月曜反应伤害暴击伤害提升（通过 BEFORE_CALCULATE 事件注入）
    """

    def __init__(self, owner: Any, extra_hp: float, lunar_crit_dmg: float):
        super().__init__(
            owner,
            name="丰饶海的神酒",
            duration=720,  # 12秒 = 720帧
            stacking_rule=StackingRule.REFRESH,
        )
        self.extra_hp = extra_hp
        self.lunar_crit_dmg = lunar_crit_dmg
        self._hp_modifier: Any = None
        self._is_subscribed = False

    def on_apply(self) -> None:
        """应用属性修饰符并订阅事件。"""
        if not hasattr(self.owner, "add_modifier"):
            return

        # 额外生命值上限
        self._hp_modifier = self.owner.add_modifier(
            source="丰饶海的神酒",
            stat="生命值%",
            value=self.extra_hp * 100,
        )

        # 订阅伤害计算事件，用于注入月曜暴击伤害
        if self.owner and hasattr(self.owner, "event_engine") and self.owner.event_engine:
            self.owner.event_engine.subscribe(EventType.BEFORE_CALCULATE, self)
            self._is_subscribed = True

    def on_remove(self) -> None:
        """移除属性修饰符和事件订阅。"""
        if hasattr(self.owner, "remove_modifier"):
            if self._hp_modifier:
                self.owner.remove_modifier(self._hp_modifier)

        # 取消事件订阅
        if self._is_subscribed and self.owner and hasattr(self.owner, "event_engine") and self.owner.event_engine:
            self.owner.event_engine.unsubscribe(EventType.BEFORE_CALCULATE, self)
            self._is_subscribed = False

    def handle_event(self, event: GameEvent) -> None:
        """处理伤害计算事件，为月曜伤害注入暴击伤害加成。"""
        if event.event_type != EventType.BEFORE_CALCULATE:
            return

        dmg_ctx = event.data.get("damage_context")
        if not dmg_ctx:
            return

        # 检测是否为月曜伤害
        if not self._is_lunar_damage(dmg_ctx):
            return

        # 注入暴击伤害加成
        dmg_ctx.add_modifier(
            source="丰饶海的神酒",
            stat="暴击伤害",
            value=self.lunar_crit_dmg * 100,  # 转为百分比形式
            op="ADD",
            audit=True,
        )

    def _is_lunar_damage(self, dmg_ctx: Any) -> bool:
        """检测是否为月曜伤害。"""
        damage = dmg_ctx.damage
        attack_tag = getattr(damage.config, "attack_tag", "")
        extra_tags = getattr(damage.config, "extra_tags", None)
        return AttackTagResolver.is_lunar_damage(attack_tag, extra_tags)


@register_weapon("帷间夜曲", "法器")
class NocturnesCurtainCall(Weapon):
    """
    帷间夜曲：十字路的旅歌

    特效：
    - 生命值上限提高 10%/12%/14%/16%/18%
    - 触发月曜反应或造成月曜反应伤害时：
      - 恢复 14/15/16/17/18 点元素能量（18秒 CD）
      - 获得12秒「丰饶海的神酒」：
        - 生命值上限进一步提高 14%/16%/18%/20%/22%
        - 月曜反应伤害暴击伤害提升 60%/80%/100%/120%/140%
    - 后台可触发
    """

    ID = 223

    # 精炼参数 (基础生命%, 能量恢复, 神酒生命%, 月曜暴伤)
    REFINEMENT_PARAMS = {
        1: (0.10, 14, 0.14, 0.60),
        2: (0.12, 15, 0.16, 0.80),
        3: (0.14, 16, 0.18, 1.00),
        4: (0.16, 17, 0.20, 1.20),
        5: (0.18, 18, 0.22, 1.40),
    }

    # 能量恢复冷却（帧数）
    ENERGY_RESTORE_CD = 1080  # 18秒 = 1080帧

    def __init__(
        self,
        character: Character,
        level: int = 1,
        lv: int = 1,
        base_data: dict[str, Any] | None = None,
    ):
        super().__init__(character, NocturnesCurtainCall.ID, level, lv, base_data)
        self._energy_cd_end: int = 0  # 能量恢复冷却结束帧
        self._is_subscribed = False

    def skill(self) -> None:
        """实现武器特效。"""
        params = self.REFINEMENT_PARAMS.get(self.lv, self.REFINEMENT_PARAMS[1])
        hp_bonus = params[0]

        # 基础生命值加成
        self.character.add_modifier(
            source="帷间夜曲",
            stat="生命值%",
            value=hp_bonus * 100,
        )

        # 订阅月曜反应事件
        self._subscribe_lunar_events()

    def _subscribe_lunar_events(self) -> None:
        """订阅月曜反应事件。"""
        if self._is_subscribed or not self.event_engine:
            return

        # 触发月曜反应
        self.event_engine.subscribe(EventType.AFTER_LUNAR_BLOOM, self)
        self.event_engine.subscribe(EventType.AFTER_LUNAR_CHARGED, self)
        self.event_engine.subscribe(EventType.AFTER_LUNAR_CRYSTALLIZE, self)
        # 造成月曜伤害（通过 BEFORE_DAMAGE + AttackTagResolver.is_lunar_damage 判断）
        self.event_engine.subscribe(EventType.BEFORE_DAMAGE, self)
        self._is_subscribed = True

    def handle_event(self, event: GameEvent) -> None:
        """处理月曜反应事件。"""
        # BEFORE_DAMAGE 事件需要额外判断是否为月曜伤害
        if event.event_type == EventType.BEFORE_DAMAGE:
            dmg = event.data.get("damage")
            if not dmg:
                return
            # 使用 AttackTagResolver 判断月曜伤害
            if not AttackTagResolver.is_lunar_damage(
                dmg.config.attack_tag,
                getattr(dmg.config, "extra_attack_tags", None)
            ):
                return

        # 检查触发者是否为装备者（包括后台触发）
        trigger = event.source
        if trigger != self.character:
            # 检查是否为召唤物触发的伤害
            if hasattr(trigger, "owner"):
                if trigger.owner != self.character:
                    return
            else:
                return

        self._on_lunar_reaction()

    def _on_lunar_reaction(self) -> None:
        """月曜反应触发时的处理逻辑。"""
        current_frame = get_current_time()

        # 检查能量恢复冷却
        if current_frame < self._energy_cd_end:
            # 仅刷新神酒效果（不恢复能量）
            self._apply_nectar_effect()
            return

        # 恢复元素能量（通过事件系统）
        params = self.REFINEMENT_PARAMS.get(self.lv, self.REFINEMENT_PARAMS[1])
        energy_restore = params[1]

        if self.event_engine:
            self.event_engine.publish(
                GameEvent(
                    event_type=EventType.BEFORE_ENERGY_CHANGE,
                    frame=current_frame,
                    source=self.character,
                    data={
                        "character": self.character,
                        "amount": float(energy_restore),
                        "is_fixed": True,  # 固定值恢复
                    }
                )
            )

        # 设置冷却
        self._energy_cd_end = current_frame + self.ENERGY_RESTORE_CD

        # 应用神酒效果
        self._apply_nectar_effect()

    def _apply_nectar_effect(self) -> None:
        """应用丰饶海的神酒效果。"""
        params = self.REFINEMENT_PARAMS.get(self.lv, self.REFINEMENT_PARAMS[1])
        _, _, extra_hp, lunar_crit_dmg = params

        # 创建并应用效果（StackingRule.REFRESH 会自动处理重复应用）
        effect = NectarsDionysusEffect(
            owner=self.character,
            extra_hp=extra_hp,
            lunar_crit_dmg=lunar_crit_dmg,
        )
        effect.apply()

    def on_frame_update(self) -> None:
        """每帧更新（用于调试或扩展）。"""
        pass
