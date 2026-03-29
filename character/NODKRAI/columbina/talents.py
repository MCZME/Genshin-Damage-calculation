"""哥伦比娅固有天赋。"""

from __future__ import annotations

from core.effect.common import TalentEffect, MoonsignTalent
from core.event import EventType, GameEvent
from core.tool import get_current_time
from core.systems.utils import AttributeCalculator
from core.action.attack_tag_resolver import AttackTagResolver
from character.NODKRAI.columbina.effects import LunarInducementStack


class LunarInducement(TalentEffect):
    """
    固有天赋一：月亮诱发的疯狂

    触发引力干涉时，哥伦比娅将获得月诱效果，使自身的暴击率提升5%，持续10秒。该效果至多叠加3层。
    """

    def __init__(self):
        super().__init__("月诱", unlock_level=20)

    def on_apply(self) -> None:
        if self.character and self.character.event_engine:
            self.character.event_engine.subscribe(EventType.GRAVITY_INTERFERENCE, self)

    def handle_event(self, event: GameEvent) -> None:
        if event.event_type == EventType.GRAVITY_INTERFERENCE:
            self._add_stack()

    def _add_stack(self) -> None:
        """添加一层暴击率效果。"""
        if not self.character:
            return

        effect = LunarInducementStack(self.character)
        effect.apply()


class MoonsDomainGrace(TalentEffect):
    """
    固有天赋二：新月自己的法则

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
        # 检查是否有活跃的月之领域
        from character.NODKRAI.columbina.entities import LunarDomain
        domains = LunarDomain.get_active_scenes("月之领域")
        if not domains:
            return

        # 检查触发者是否在任一领域内
        trigger = event.source
        in_domain = any(
            trigger.entity_id in domain._entities_in_range
            for domain in domains
        )
        if not in_domain:
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


class LunarGuidance(MoonsignTalent):
    """
    固有天赋三：月引（月兆天赋）。

    标识哥伦比娅为月兆角色。
    队伍中的角色触发感电/绽放/水结晶反应时，转为触发月曜反应。
    基于生命值上限提升月曜反应基础伤害：每1000点提升0.2%，至多7%。
    """

    def __init__(self):
        super().__init__("月引", unlock_level=1)
        # 定义可触发的月曜反应类型
        self.lunar_triggers = {"bloom", "charged", "crystallize"}
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
            if not dmg_ctx:
                return

            # 使用 AttackTagResolver 判定月曜伤害
            if not AttackTagResolver.is_lunar_damage(
                dmg_ctx.damage.config.attack_tag,
                dmg_ctx.damage.config.extra_attack_tags
            ):
                return

            # 注入月曜基础伤害加成
            bonus = self._get_lunar_damage_bonus()
            dmg_ctx.add_modifier(
                source="月引",
                stat="基础伤害提升",
                value=bonus * 100,  # 转为百分比
                op="ADD",
                audit=True,
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
