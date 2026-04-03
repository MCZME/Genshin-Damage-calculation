"""哥伦比娅固有天赋。"""

from __future__ import annotations

import random

from core.effect.common import TalentEffect, MoonsignTalent
from core.event import EventType, GameEvent
from core.tool import get_current_time
from core.systems.utils import AttributeCalculator
from core.action.attack_tag_resolver import AttackTagResolver
from core.systems.lunar_system import LunarReactionSystem
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
    - 月绽放：为队伍提供山月草露（18秒窗口内至多3枚）
    - 月感电：雷暴云雷击有33%概率额外雷击
    - 月结晶：月笼谐奏攻击有33%概率额外攻击
    """

    def __init__(self):
        super().__init__("月之眷顾", unlock_level=60)

    def on_apply(self) -> None:
        if self.character and self.character.event_engine:
            # 订阅月绽放事件
            self.character.event_engine.subscribe(EventType.AFTER_LUNAR_BLOOM, self)
            # 订阅月笼谐奏攻击事件
            self.character.event_engine.subscribe(EventType.LUNAR_CRYSTALLIZE_ATTACK, self)
            # 订阅雷暴云攻击事件
            self.character.event_engine.subscribe(EventType.LUNAR_CHARGED_TICK, self)

    def handle_event(self, event: GameEvent) -> None:
        if event.event_type == EventType.AFTER_LUNAR_BLOOM:
            if self._is_trigger_in_domain(event):
                self._provide_mountain_grass_dew()
        elif event.event_type == EventType.LUNAR_CRYSTALLIZE_ATTACK:
            if self._has_active_domain():
                self._try_extra_cage_attack(event)
        elif event.event_type == EventType.LUNAR_CHARGED_TICK:
            if self._is_cloud_in_domain(event):
                self._try_extra_lightning_strike(event)

    def _is_trigger_in_domain(self, event: GameEvent) -> bool:
        """检查触发者是否在月之领域内。"""
        from character.NODKRAI.columbina.entities import LunarDomain
        trigger = event.source
        domains = LunarDomain.get_active_scenes("月之领域")
        if not domains:
            return False
        return any(trigger.entity_id in domain._entities_in_range for domain in domains)

    def _has_active_domain(self) -> bool:
        """检查是否存在激活的月之领域。"""
        from character.NODKRAI.columbina.entities import LunarDomain
        return len(LunarDomain.get_active_scenes("月之领域")) > 0

    def _provide_mountain_grass_dew(self) -> None:
        """提供山月草露（18秒窗口内至多3枚）。"""
        ctx = getattr(self.character, "ctx", None)
        if ctx:
            lunar_system = ctx.get_system(LunarReactionSystem)
            if lunar_system:
                lunar_system.add_mountain_grass_dew()

    def _try_extra_cage_attack(self, event: GameEvent) -> None:
        """月笼谐奏攻击有33%概率额外攻击一次。"""
        # 额外攻击不能再触发额外攻击，避免事件循环
        if event.data.get("is_extra_attack"):
            return

        if random.random() < 0.33:
            # 获取攻击参数
            cage = event.data.get("cage")
            target = event.data.get("target")
            source_characters = event.data.get("source_characters", [])

            if cage and target and source_characters and self.character and self.character.event_engine:
                # 发布额外的谐奏攻击事件
                self.character.event_engine.publish(GameEvent(
                    event_type=EventType.LUNAR_CRYSTALLIZE_ATTACK,
                    frame=get_current_time(),
                    source=cage,
                    data={
                        "cage": cage,
                        "target": target,
                        "source_characters": source_characters,
                        "is_extra_attack": True,  # 标记为额外攻击
                    }
                ))

    def _is_cloud_in_domain(self, event: GameEvent) -> bool:
        """检查雷暴云是否在月之领域内。"""
        from character.NODKRAI.columbina.entities import LunarDomain
        cloud = event.source
        if not cloud:
            return False

        # 获取雷暴云位置
        cloud_pos = tuple(cloud.pos) if hasattr(cloud, 'pos') else None
        if not cloud_pos:
            return False

        domains = LunarDomain.get_active_scenes("月之领域")
        if not domains:
            return False

        # 检查雷暴云是否在任一月之领域范围内
        for domain in domains:
            dx = cloud_pos[0] - domain.pos[0]
            dz = cloud_pos[1] - domain.pos[1]
            dist = (dx * dx + dz * dz) ** 0.5
            if dist <= domain.detection_radius:
                return True
        return False

    def _try_extra_lightning_strike(self, event: GameEvent) -> None:
        """雷暴云雷击有33%概率额外进行一次雷击。"""
        # 额外雷击不能再触发额外雷击，避免事件循环
        if event.data.get("is_extra_strike"):
            return

        if random.random() < 0.33:
            # 获取攻击参数
            cloud = event.data.get("cloud")
            target = event.data.get("target")
            source_characters = event.data.get("source_characters", [])

            if cloud and target and source_characters and self.character and self.character.event_engine:
                # 发布额外的雷击事件
                self.character.event_engine.publish(GameEvent(
                    event_type=EventType.LUNAR_CHARGED_TICK,
                    frame=get_current_time(),
                    source=cloud,
                    data={
                        "cloud": cloud,
                        "target": target,
                        "source_characters": source_characters,
                        "is_extra_strike": True,  # 标记为额外雷击
                    }
                ))


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
