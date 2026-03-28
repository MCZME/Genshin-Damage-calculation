"""哥伦比娅实体类：引力涟漪、月之领域等。"""

from __future__ import annotations
from typing import Any

from core.entities.base_entity import CombatEntity, Faction
from core.systems.contract.attack import (
    AttackConfig,
    HitboxConfig,
    AOEShape,
    StrikeType,
)
from core.systems.contract.damage import Damage
from core.event import GameEvent, EventType
from core.tool import get_current_time
from core.mechanics.aura import Element
from character.NODKRAI.columbina.data import (
    ATTACK_DATA,
    ELEMENTAL_SKILL_DATA,
)


class GravityRipple(CombatEntity):
    """
    引力涟漪 - 元素战技产物。

    特性：
    - 跟随场上角色
    - 持续造成水元素范围伤害
    - 队伍中角色触发月曜反应时积攒引力值
    - 引力值满后触发引力干涉
    """

    def __init__(
        self,
        owner: Any,
        context: Any,
        skill_lv: int,
    ) -> None:
        super().__init__(
            name="引力涟漪",
            faction=Faction.PLAYER,
            life_frame=1500,  # 25秒
            context=context,
        )
        self.owner = owner
        self.skill_lv = skill_lv

        # 伤害计时
        self.damage_timer = 0
        self.damage_interval = 60  # 每秒一次

        # 月兆·满辉状态
        self.is_full_moon = False

        # 预载攻击配置
        self.normal_config = self._build_attack_config("引力涟漪·持续伤害")
        self.full_moon_config = self._build_attack_config("引力涟漪·满辉")

        # 订阅事件
        if self.event_engine:
            self.event_engine.subscribe(EventType.AFTER_LUNAR_BLOOM, self)
            self.event_engine.subscribe(EventType.AFTER_LUNAR_CHARGED, self)
            self.event_engine.subscribe(EventType.AFTER_LUNAR_CRYSTALLIZE, self)
            self.event_engine.subscribe(EventType.LUNAR_DAMAGE_DEALT, self)

    def on_finish(self) -> None:
        """清理事件订阅。"""
        if self.event_engine:
            self.event_engine.unsubscribe(EventType.AFTER_LUNAR_BLOOM, self)
            self.event_engine.unsubscribe(EventType.AFTER_LUNAR_CHARGED, self)
            self.event_engine.unsubscribe(EventType.AFTER_LUNAR_CRYSTALLIZE, self)
            self.event_engine.unsubscribe(EventType.LUNAR_DAMAGE_DEALT, self)
        super().on_finish()

    def handle_event(self, event: GameEvent) -> None:
        """处理月曜反应事件。"""
        # 根据事件类型积攒引力值
        gravity_gain_map = {
            EventType.AFTER_LUNAR_BLOOM: 15,      # 月绽放
            EventType.AFTER_LUNAR_CHARGED: 12,    # 月感电
            EventType.AFTER_LUNAR_CRYSTALLIZE: 18, # 月结晶
            EventType.LUNAR_DAMAGE_DEALT: 8,      # 月曜伤害
        }

        gain = gravity_gain_map.get(event.event_type, 0)

        # 确定来源类型
        source_type = None
        if event.event_type == EventType.AFTER_LUNAR_BLOOM:
            source_type = "月绽放"
        elif event.event_type == EventType.AFTER_LUNAR_CHARGED:
            source_type = "月感电"
        elif event.event_type == EventType.AFTER_LUNAR_CRYSTALLIZE:
            source_type = "月结晶"

        if gain > 0 and source_type:
            self.owner.add_gravity(gain, source_type)

            # 检查是否达到满辉状态
            if self.owner.gravity_value >= self.owner.gravity_max:
                self.is_full_moon = True
                self._trigger_gravity_interference()

    def _perform_tick(self) -> None:
        """每帧逻辑。"""
        super()._perform_tick()

        # 跟随场上角色
        self._follow_active_character()

        # 周期伤害
        self.damage_timer += 1
        if self.damage_timer >= self.damage_interval:
            self._execute_periodic_damage()
            self.damage_timer = 0

        # 检查月之领域持续时间
        if hasattr(self.owner, "lunar_domain_duration"):
            if self.owner.lunar_domain_duration > 0:
                self.owner.lunar_domain_duration -= 1
            else:
                self.owner.lunar_domain_active = False

    def _follow_active_character(self) -> None:
        """跟随场上角色。"""
        if not self.ctx or not self.ctx.space:
            return

        active_char = self.ctx.space.get_active_character()
        if active_char:
            self.pos = list(active_char.pos)

    def _execute_periodic_damage(self) -> None:
        """执行周期性伤害。"""
        # 选择配置
        config = self.full_moon_config if self.is_full_moon else self.normal_config

        mult = ELEMENTAL_SKILL_DATA["引力涟漪·持续伤害"][1][self.skill_lv - 1]

        dmg_obj = Damage(
            element=(Element.HYDRO, 1.0),
            damage_multiplier=(mult,),
            scaling_stat=("生命值",),
            config=config,
            name="引力涟漪·持续伤害",
        )
        dmg_obj.set_element(Element.HYDRO, 1.0)

        self.event_engine.publish(
            GameEvent(
                EventType.BEFORE_DAMAGE,
                get_current_time(),
                source=self.owner,
                data={"character": self.owner, "damage": dmg_obj},
            )
        )

    def _trigger_gravity_interference(self) -> None:
        """
        触发引力干涉。

        根据积攒最多引力值的月曜反应类型造成不同伤害。
        """
        dominant_type = self.owner.get_dominant_gravity_type()

        # 发布引力干涉事件
        self.event_engine.publish(
            GameEvent(
                EventType.GRAVITY_INTERFERENCE,
                get_current_time(),
                source=self.owner,
                data={
                    "lunar_type": dominant_type,
                    "skill_lv": self.skill_lv,
                }
            )
        )

        # 重置引力值
        self.owner.reset_gravity()
        self.is_full_moon = False

    def _build_attack_config(self, name: str) -> AttackConfig:
        """构建攻击配置。"""
        p = ATTACK_DATA[name]

        shape_map = {
            "球": AOEShape.SPHERE,
            "圆柱": AOEShape.CYLINDER,
        }

        hitbox = HitboxConfig(
            shape=shape_map.get(p["shape"], AOEShape.SPHERE),
            radius=p.get("radius", 0.0),
            height=p.get("height", 0.0),
            offset=p.get("offset", (0.0, 0.0, 0.0)),
        )

        return AttackConfig(
            attack_tag=p["attack_tag"],
            extra_attack_tags=p.get("extra_attack_tags", []),
            icd_tag=p.get("icd_tag", "None"),
            icd_group=p.get("icd_group", "None"),
            is_ranged=p.get("is_ranged", True),
            hitbox=hitbox,
        )
