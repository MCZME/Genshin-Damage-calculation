"""哥伦比娅实体类：引力涟漪、引力干涉等。"""

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
    ACTION_FRAME_DATA,
    ATTACK_DATA,
    ELEMENTAL_SKILL_DATA,
)
from character.NODKRAI.columbina.effects import CrescentSignEffect


class GravityRipple(CombatEntity):
    """
    引力涟漪 - 元素战技产物。

    特性：
    - 跟随场上角色
    - 每隔2秒持续造成水元素范围伤害
    - 触发月曜反应或造成月曜伤害时为哥伦比娅添加「新月之示」效果
    - 监听引力干涉事件，生成对应的攻击实体
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

        # 周期伤害计时（每2秒一次）
        self.damage_timer = 0
        self.damage_interval = 120

        # 预载攻击配置
        self.normal_config = self._build_attack_config("引力涟漪·持续伤害")
        self.full_moon_config = self._build_attack_config("引力涟漪·满辉")

        # 订阅事件
        if self.event_engine:
            self.event_engine.subscribe(EventType.AFTER_LUNAR_BLOOM, self)
            self.event_engine.subscribe(EventType.AFTER_LUNAR_CHARGED, self)
            self.event_engine.subscribe(EventType.AFTER_LUNAR_CRYSTALLIZE, self)
            self.event_engine.subscribe(EventType.LUNAR_DAMAGE_DEALT, self)
            self.event_engine.subscribe(EventType.GRAVITY_INTERFERENCE, self)

    def on_finish(self) -> None:
        """清理事件订阅和引力值。"""
        if self.event_engine:
            self.event_engine.unsubscribe(EventType.AFTER_LUNAR_BLOOM, self)
            self.event_engine.unsubscribe(EventType.AFTER_LUNAR_CHARGED, self)
            self.event_engine.unsubscribe(EventType.AFTER_LUNAR_CRYSTALLIZE, self)
            self.event_engine.unsubscribe(EventType.LUNAR_DAMAGE_DEALT, self)
            self.event_engine.unsubscribe(EventType.GRAVITY_INTERFERENCE, self)

        # 引力涟漪结束时移除引力值
        self.owner.reset_gravity()

        super().on_finish()

    def handle_event(self, event: GameEvent) -> None:
        """处理月曜反应事件和引力干涉事件。"""
        if event.event_type == EventType.GRAVITY_INTERFERENCE:
            self._spawn_gravity_interference(event)
        else:
            # 月曜反应事件：为哥伦比娅添加新月之示效果
            lunar_type = self._get_lunar_type(event)
            if lunar_type:
                effect = CrescentSignEffect(self.owner, lunar_type=lunar_type)
                effect.apply()

    def _get_lunar_type(self, event: GameEvent) -> str | None:
        """从事件中提取月曜类型。"""
        if event.event_type == EventType.AFTER_LUNAR_BLOOM:
            return "月绽放"
        elif event.event_type == EventType.AFTER_LUNAR_CHARGED:
            return "月感电"
        elif event.event_type == EventType.AFTER_LUNAR_CRYSTALLIZE:
            return "月结晶"
        elif event.event_type == EventType.LUNAR_DAMAGE_DEALT:
            return event.data.get("lunar_type")
        return None

    def _perform_tick(self) -> None:
        """每帧逻辑。"""
        super()._perform_tick()

        # 跟随场上角色
        self._follow_active_character()

        # 周期伤害（每2秒）
        self.damage_timer += 1
        if self.damage_timer >= self.damage_interval:
            self._execute_periodic_damage()
            self.damage_timer = 0

    def _follow_active_character(self) -> None:
        """跟随角色（队伍角色坐标同步）。"""
        if self.owner:
            self.pos = list(self.owner.pos)

    def _execute_periodic_damage(self) -> None:
        """执行周期性伤害（每2秒）。"""
        # 通过月兆系统检查是否处于满辉状态
        is_ascendant = self._check_moonsign_ascendant()

        # 满辉状态下扩大范围
        config = self.full_moon_config if is_ascendant else self.normal_config

        mult: float = ELEMENTAL_SKILL_DATA["引力涟漪·持续伤害"][1][self.skill_lv - 1]  # type: ignore[assignment]

        dmg_obj = Damage(
            element=(Element.HYDRO, 1.0),
            damage_multiplier=(mult,),
            scaling_stat=("生命值",),
            config=config,
            name="引力涟漪·持续伤害",
        )
        dmg_obj.set_element(Element.HYDRO, 1.0)

        if self.event_engine:
            self.event_engine.publish(
            GameEvent(
                EventType.BEFORE_DAMAGE,
                get_current_time(),
                source=self.owner,
                data={"character": self.owner, "damage": dmg_obj},
            )
        )

    def _check_moonsign_ascendant(self) -> bool:
        """检查角色是否处于月兆·满辉状态。"""
        if not self.ctx:
            return False

        system_manager = getattr(self.ctx, "system_manager", None)
        if not system_manager:
            return False

        moonsign_sys = system_manager.get_system("moonsign")
        if not moonsign_sys:
            return False

        return moonsign_sys.has_ascendant(self.owner)

    def _spawn_gravity_interference(self, event: GameEvent) -> None:
        """生成引力干涉攻击实体。"""
        lunar_type = event.data.get("lunar_type", "月绽放")

        interference = GravityInterference(
            owner=self.owner,
            context=self.ctx,
            lunar_type=lunar_type,
            skill_lv=self.skill_lv,
        )
        if self.ctx and self.ctx.space:
            self.ctx.space.register(interference)

    def _build_attack_config(self, name: str) -> AttackConfig:
        """构建攻击配置。"""
        p = ATTACK_DATA[name]

        shape_map: dict[str, AOEShape] = {
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
            strike_type=StrikeType.DEFAULT,
            is_ranged=p.get("is_ranged", True),
            hitbox=hitbox,
        )


class GravityInterference(CombatEntity):
    """
    引力干涉 - 引力值满时触发的攻击实体。

    根据积攒最多引力值的月曜类型造成不同伤害：
    - 月感电：雷元素范围伤害（1次）
    - 月绽放：发射5枚月露之印（草元素，5次）
    - 月结晶：岩元素范围伤害（1次）
    """

    # 元素类型映射
    ELEMENT_MAP = {
        "月感电": Element.ELECTRO,
        "月绽放": Element.DENDRO,
        "月结晶": Element.GEO,
    }

    # 伤害倍率键名映射
    MULTIPLIER_KEY_MAP = {
        "月感电": "引力干涉·月感电伤害",
        "月绽放": "引力干涉·月绽放伤害",
        "月结晶": "引力干涉·月结晶伤害",
    }

    # 攻击数据键名映射
    ATTACK_KEY_MAP = {
        "月感电": "引力干涉·月感电",
        "月绽放": "引力干涉·月绽放",
        "月结晶": "引力干涉·月结晶",
    }

    # 帧数据键名映射
    FRAME_KEY_MAP = {
        "月感电": "引力干涉·月感电",
        "月绽放": "引力干涉·月绽放",
        "月结晶": "引力干涉·月结晶",
    }

    def __init__(
        self,
        owner: Any,
        context: Any,
        lunar_type: str,
        skill_lv: int,
    ) -> None:
        self.owner = owner
        self.lunar_type = lunar_type
        self.skill_lv = skill_lv

        # 根据类型获取帧数据
        frame_key = self.FRAME_KEY_MAP.get(lunar_type, "引力干涉·月绽放")
        frame_data = ACTION_FRAME_DATA[frame_key]

        super().__init__(
            name=f"引力干涉·{lunar_type}",
            faction=Faction.PLAYER,
            life_frame=frame_data["total_frames"],
            context=context,
        )

        # 命中帧数据
        self.hit_frames = frame_data["hit_frames"]
        self.hit_index = 0

        # 预载攻击配置
        attack_key = self.ATTACK_KEY_MAP.get(lunar_type, "引力干涉·月绽放")
        self.attack_config = self._build_attack_config(attack_key)

    def _perform_tick(self) -> None:
        """每帧逻辑，在指定帧执行攻击。"""
        super()._perform_tick()

        # 检查是否到达命中帧
        if self.hit_index < len(self.hit_frames):
            if self.current_frame >= self.hit_frames[self.hit_index]:
                self._execute_attack()
                self.hit_index += 1

    def _execute_attack(self) -> None:
        """执行攻击。"""
        element = self.ELEMENT_MAP.get(self.lunar_type, Element.DENDRO)
        mult_key = self.MULTIPLIER_KEY_MAP.get(self.lunar_type, "引力干涉·月绽放伤害")

        # 月绽放类型每枚月露之印单独计算伤害
        # 其他类型只有一次攻击
        mult: float = ELEMENTAL_SKILL_DATA[mult_key][1][self.skill_lv - 1]  # type: ignore[assignment]

        dmg_obj = Damage(
            element=(element, 0),  # 月曜伤害无附着
            damage_multiplier=(mult,),
            scaling_stat=("生命值",),
            config=self.attack_config,
            name=f"引力干涉·{self.lunar_type}",
        )
        # 标记为月曜伤害
        dmg_obj.data["is_lunar_damage"] = True
        dmg_obj.data["lunar_type"] = self.lunar_type

        if self.event_engine:
            self.event_engine.publish(
            GameEvent(
                EventType.BEFORE_DAMAGE,
                get_current_time(),
                source=self.owner,
                data={"character": self.owner, "damage": dmg_obj},
            )
        )

    def _build_attack_config(self, name: str) -> AttackConfig:
        """构建攻击配置。"""
        p = ATTACK_DATA[name]

        shape_map: dict[str, AOEShape] = {
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
            strike_type=StrikeType.DEFAULT,
            is_ranged=p.get("is_ranged", True),
            hitbox=hitbox,
        )
