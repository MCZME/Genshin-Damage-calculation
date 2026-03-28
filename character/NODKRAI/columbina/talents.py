"""哥伦比娅固有天赋。"""

from __future__ import annotations

from core.effect.common import TalentEffect
from core.event import EventType, GameEvent
from core.tool import get_current_time
from core.systems.utils import AttributeCalculator
from character.NODKRAI.columbina.data import ELEMENTAL_SKILL_DATA


class LunarInducement(TalentEffect):
    """
    固有天赋一：月诱。

    触发引力干涉时，暴击率提升5%，持续10秒。
    至多叠加3层。
    """

    def __init__(self):
        super().__init__("月诱", unlock_level=20)
        self.stacks = 0
        self.max_stacks = 3
        self.stack_timers: list[int] = []  # 每层的独立计时器

    def on_apply(self) -> None:
        if self.character and self.character.event_engine:
            self.character.event_engine.subscribe(EventType.GRAVITY_INTERFERENCE, self)

    def handle_event(self, event: GameEvent) -> None:
        if event.event_type == EventType.GRAVITY_INTERFERENCE:
            self._add_stack()

    def _add_stack(self) -> None:
        """添加一层暴击率。"""
        if self.stacks < self.max_stacks:
            self.stacks += 1
            self.stack_timers.append(600)  # 10秒 = 600帧

            # 注入暴击率修饰符
            self.character.add_modifier(
                source=f"月诱-{self.stacks}层",
                stat="暴击率",
                value=5.0,
            )

    def on_frame_update(self) -> None:
        """更新计时器。"""
        if not self.is_active:
            return

        # 更新每层计时器
        expired_count = 0
        new_timers = []
        for timer in self.stack_timers:
            timer -= 1
            if timer > 0:
                new_timers.append(timer)
            else:
                expired_count += 1

        self.stack_timers = new_timers

        # 如果有层过期，更新暴击率
        if expired_count > 0:
            self.stacks = len(self.stack_timers)
            # 移除旧修饰符，重新添加
            self.character.dynamic_modifiers = [
                m for m in self.character.dynamic_modifiers
                if not m.source.startswith("月诱-")
            ]
            for i in range(self.stacks):
                self.character.add_modifier(
                    source=f"月诱-{i + 1}层",
                    stat="暴击率",
                    value=5.0,
                )


class MoonsDomainGrace(TalentEffect):
    """
    固有天赋二：月之眷顾。

    处于月之领域中的角色触发月曜反应时：
    - 月感电：雷暴云有33%概率额外雷击
    - 月绽放：为队伍提供山月草露（每18秒至多3枚）
    - 月结晶：每枚月笼有33%概率额外攻击
    """

    def __init__(self):
        super().__init__("月之眷顾", unlock_level=60)
        self.mountain_dew_timer = 0
        self.mountain_dew_cooldown = 1080  # 18秒
        self.mountain_dew_count = 0
        self.max_mountain_dew = 3

    def on_apply(self) -> None:
        if self.character and self.character.event_engine:
            self.character.event_engine.subscribe(EventType.AFTER_LUNAR_BLOOM, self)
            self.character.event_engine.subscribe(EventType.AFTER_LUNAR_CHARGED, self)
            self.character.event_engine.subscribe(EventType.AFTER_LUNAR_CRYSTALLIZE, self)

    def handle_event(self, event: GameEvent) -> None:
        # 检查是否在月之领域内
        if not getattr(self.character, "lunar_domain_active", False):
            return

        if event.event_type == EventType.AFTER_LUNAR_BLOOM:
            self._provide_mountain_dew()
        elif event.event_type == EventType.AFTER_LUNAR_CHARGED:
            self._enhance_thunder_cloud(event)
        elif event.event_type == EventType.AFTER_LUNAR_CRYSTALLIZE:
            self._enhance_lunar_cage(event)

    def _provide_mountain_dew(self) -> None:
        """提供山月草露。"""
        if self.mountain_dew_count >= self.max_mountain_dew:
            return

        self.mountain_dew_timer += 1
        if self.mountain_dew_timer >= 0:  # 每次触发都提供
            ctx = getattr(self.character, "ctx", None)
            if ctx and hasattr(ctx, "lunar_system"):
                ctx.lunar_system.add_grass_dew(1)
                self.mountain_dew_count += 1
                if self.mountain_dew_count >= self.max_mountain_dew:
                    self.mountain_dew_timer = 0

    def _enhance_thunder_cloud(self, event: GameEvent) -> None:
        """增强雷暴云（33%额外雷击）。"""
        # 在月曜反应系统中处理
        event.data["extra_lightning_chance"] = 0.33

    def _enhance_lunar_cage(self, event: GameEvent) -> None:
        """增强月笼（33%额外攻击）。"""
        event.data["extra_attack_chance"] = 0.33

    def on_frame_update(self) -> None:
        """冷却计时。"""
        if not self.is_active:
            return

        # 重置山月草露计数（每18秒重置）
        if self.mountain_dew_count >= self.max_mountain_dew:
            self.mountain_dew_timer += 1
            if self.mountain_dew_timer >= self.mountain_dew_cooldown:
                self.mountain_dew_count = 0
                self.mountain_dew_timer = 0


class LunarGuidance(TalentEffect):
    """
    固有天赋三：月引。

    队伍中的角色触发感电/绽放/水结晶反应时，转为触发月曜反应。
    基于生命值上限提升月曜反应基础伤害：每1000点提升0.2%，至多7%。
    """

    def __init__(self):
        super().__init__("月引", unlock_level=1)
        self.cached_bonus: float = 0.0
        self.hp_cache_frame: int = -1

    def on_apply(self) -> None:
        """应用时注册事件。"""
        # 月曜反应伤害加成在 BEFORE_CALCULATE 中处理
        if self.character and self.character.event_engine:
            self.character.event_engine.subscribe(EventType.BEFORE_CALCULATE, self)

    def handle_event(self, event: GameEvent) -> None:
        if event.event_type == EventType.BEFORE_CALCULATE:
            dmg_ctx = event.data.get("damage_context")
            if dmg_ctx and dmg_ctx.damage.data.get("is_lunar_damage"):
                # 注入月曜基础伤害加成
                bonus = self._get_lunar_damage_bonus()
                dmg_ctx.add_modifier(
                    source="月引",
                    stat="月曜基础伤害",
                    value=bonus,
                    op="ADD",
                )

    def _get_lunar_damage_bonus(self) -> float:
        """计算月曜反应基础伤害加成（缓存优化）。"""
        current_frame = get_current_time()
        if current_frame == self.hp_cache_frame:
            return self.cached_bonus

        hp = AttributeCalculator.get_val_by_name(self.character, "生命值")
        bonus = min(0.07, (hp / 1000) * 0.002)

        self.cached_bonus = bonus
        self.hp_cache_frame = current_frame
        return bonus
