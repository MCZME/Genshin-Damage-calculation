"""哥伦比娅实体类：引力涟漪、引力干涉、月之领域等。"""

from __future__ import annotations
from typing import Any

from core.entities.base_entity import CombatEntity, Faction
from core.entities.attack_entity import AttackEntity, AttackTriggerType
from core.entities.scene_entity import SceneEntity
from core.logger import get_emulation_logger
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
from core.action.attack_tag_resolver import AttackTagResolver
from character.NODKRAI.columbina.data import (
    ACTION_FRAME_DATA,
    ATTACK_DATA,
    ELEMENTAL_SKILL_DATA,
    ELEMENTAL_BURST_DATA,
    MECHANISM_CONFIG,
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

        # 产球冷却（从战技对象获取）
        self.particle_cd = MECHANISM_CONFIG["ENERGY_PARTICLE_CD"]

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
            self.event_engine.subscribe(EventType.AFTER_DAMAGE, self)

    def on_finish(self) -> None:
        """清理事件订阅和引力值。"""
        if self.event_engine:
            self.event_engine.unsubscribe(EventType.AFTER_LUNAR_BLOOM, self)
            self.event_engine.unsubscribe(EventType.AFTER_LUNAR_CHARGED, self)
            self.event_engine.unsubscribe(EventType.AFTER_LUNAR_CRYSTALLIZE, self)
            self.event_engine.unsubscribe(EventType.LUNAR_DAMAGE_DEALT, self)
            self.event_engine.unsubscribe(EventType.GRAVITY_INTERFERENCE, self)
            self.event_engine.unsubscribe(EventType.AFTER_DAMAGE, self)

        # 引力涟漪结束时移除引力值
        self.owner.reset_gravity()

        super().on_finish()

    def handle_event(self, event: GameEvent) -> None:
        """处理月曜反应事件和引力干涉事件。"""
        if event.event_type == EventType.GRAVITY_INTERFERENCE:
            # C1 触发的引力干涉由 C1 自己创建实体，引力涟漪不再重复创建
            if event.data.get("is_c1_trigger"):
                return
            self._spawn_gravity_interference(event)
        elif event.event_type == EventType.AFTER_DAMAGE:
            # 产球逻辑：引力涟漪·持续伤害命中时
            self._try_spawn_energy_particle(event)
        else:
            # 月曜反应事件：为哥伦比娅添加新月之示效果
            lunar_type = self._get_lunar_type(event)
            if lunar_type:
                effect = CrescentSignEffect(self.owner, lunar_type=lunar_type)
                effect.apply()

    def _try_spawn_energy_particle(self, event: GameEvent) -> None:
        """
        尝试产生能量微粒。

        触发条件：引力涟漪·持续伤害命中
        产出：1~2个水元素微粒，概率 66.67%:33.33%
        冷却：3.5秒（与战技共用）
        """
        # 检查是否为引力涟漪·持续伤害
        dmg = event.data.get("damage")
        if not dmg or dmg.name != "引力涟漪·持续伤害":
            return

        # 从战技对象获取冷却状态
        skill = self.owner.skills.get("elemental_skill")
        if not skill:
            return

        current_frame = get_current_time()
        if current_frame - skill.last_particle_frame < self.particle_cd:
            return

        # 更新冷却
        skill.last_particle_frame = current_frame

        # 随机决定微粒数量
        import random
        rates: tuple[float, float] = MECHANISM_CONFIG["ENERGY_PARTICLE_RATES"]  # type: ignore[assignment]
        num_particles = 1 if random.random() < rates[0] else 2

        # 产球
        from core.factory.entity_factory import EntityFactory
        EntityFactory.spawn_energy(
            num=num_particles,
            character=self.owner,
            element_energy=("水", 2),  # 水元素微粒，每个提供2点能量
            time=40,  # 约0.67秒后生效
        )

        get_emulation_logger().log_info(
            f"[引力涟漪] 产生 {num_particles} 个水元素微粒",
            sender="GravityRipple"
        )

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

        # 使用类引用获取月兆系统
        from core.systems.moonsign_system import MoonsignSystem
        moonsign_sys = system_manager.get_system(MoonsignSystem)
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


class GravityInterference(AttackEntity):
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

        # 构建攻击配置和伤害对象
        attack_key = self.ATTACK_KEY_MAP.get(lunar_type, "引力干涉·月绽放")
        attack_config = self._build_attack_config(attack_key)
        dmg_obj = self._build_damage(lunar_type, skill_lv, attack_config)

        super().__init__(
            name=f"引力干涉·{lunar_type}",
            damage=dmg_obj,
            source=owner,
            life_frame=frame_data["total_frames"],
            trigger_type=AttackTriggerType.ON_HIT_FRAME,
            context=context,
        )

        # 设置命中帧（AttackEntity 内置支持）
        self.set_hit_frames(frame_data["hit_frames"])

        # 保存攻击配置，用于每次命中帧重新构建伤害
        self._attack_config = self._build_attack_config(
            self.ATTACK_KEY_MAP.get(lunar_type, "引力干涉·月绽放")
        )

    def _execute_attack(self) -> None:
        """
        执行攻击：每次命中帧发布独立的伤害事件。

        重写父类方法以支持多帧攻击（月绽放类型需要5次攻击）。
        """
        # 重新构建伤害对象（每次命中帧独立计算）
        dmg_obj = self._build_damage(
            self.lunar_type, self.skill_lv, self._attack_config
        )

        if self.event_engine:
            self.event_engine.publish(
                GameEvent(
                    EventType.BEFORE_DAMAGE,
                    get_current_time(),
                    source=self.owner,
                    data={"character": self.owner, "damage": dmg_obj},
                )
            )

    def _build_damage(
        self,
        lunar_type: str,
        skill_lv: int,
        config: AttackConfig,
    ) -> Damage:
        """构建伤害对象。"""
        element = self.ELEMENT_MAP.get(lunar_type, Element.DENDRO)
        mult_key = self.MULTIPLIER_KEY_MAP.get(lunar_type, "引力干涉·月绽放伤害")
        mult: float = ELEMENTAL_SKILL_DATA[mult_key][1][skill_lv - 1]  # type: ignore[assignment]

        dmg_obj = Damage(
            element=(element, 0),  # 月曜伤害无附着
            damage_multiplier=(mult,),
            scaling_stat=("生命值",),
            config=config,
            name=f"引力干涉·{lunar_type}",
        )
        # 标记为月曜伤害
        dmg_obj.data["is_lunar_damage"] = True
        dmg_obj.data["lunar_type"] = lunar_type
        return dmg_obj

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


class LunarDomain(SceneEntity):
    """
    月之领域 - 元素爆发产物。

    特性：
    - 固定位置的领域效果
    - 持续20秒
    - 领域内角色触发月曜反应时获得伤害加成
    """

    def __init__(
        self,
        owner: Any,
        context: Any,
        burst_lv: int,
    ) -> None:
        super().__init__(
            name="月之领域",
            pos=tuple(owner.pos),  # 在角色当前位置创建
            life_frame=1200,  # 20秒
            context=context,
            owner=owner,
            detection_radius=6.5,  # 与大招范围一致
            affect_factions=[Faction.PLAYER],
            tick_interval=60,
        )
        self.burst_lv = burst_lv
        self.dmg_bonus: float = ELEMENTAL_BURST_DATA["月曜反应伤害提升"][1][burst_lv - 1]  # type: ignore[assignment]

        # 订阅伤害计算事件
        if self.event_engine:
            self.event_engine.subscribe(EventType.BEFORE_CALCULATE, self)

    def on_finish(self) -> None:
        """清理事件订阅。"""
        if self.event_engine:
            self.event_engine.unsubscribe(EventType.BEFORE_CALCULATE, self)
        super().on_finish()

    def handle_event(self, event: GameEvent) -> None:
        """处理伤害计算事件，为领域内角色的月曜伤害提供加成。"""
        if event.event_type != EventType.BEFORE_CALCULATE:
            return

        dmg_ctx = event.data.get("damage_context")
        if not dmg_ctx:
            return

        # 使用 AttackTagResolver 判定月曜伤害
        if not AttackTagResolver.is_lunar_damage(
            dmg_ctx.damage.config.attack_tag,
            dmg_ctx.damage.config.extra_attack_tags
        ):
            return

        # 检查伤害来源是否在领域内
        trigger = event.source
        if trigger and trigger.entity_id in self._entities_in_range:
            # 注入月曜反应伤害提升修饰符
            dmg_ctx.add_modifier(
                source="月之领域",
                stat="月曜反应伤害提升",
                value=self.dmg_bonus,
                op="ADD",
                audit=True,
            )
