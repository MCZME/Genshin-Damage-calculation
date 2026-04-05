"""哥伦比娅技能实现。"""

import random
from typing import Any, Dict, Optional

from core.logger import get_emulation_logger
from core.skills.base import SkillBase, EnergySkill
from core.skills.common import (
    NormalAttackSkill,
    ChargedAttackSkill,
    PlungingAttackSkill,
)
from core.action.action_data import ActionFrameData
from core.systems.contract.attack import AttackConfig, HitboxConfig, AOEShape, StrikeType
from core.systems.contract.damage import Damage
from core.event import GameEvent, EventType
from core.tool import get_current_time
from core.mechanics.aura import Element
from core.systems.lunar_system import LunarReactionSystem
from character.NODKRAI.columbina.data import (
    ACTION_FRAME_DATA,
    ATTACK_DATA,
    MECHANISM_CONFIG,
    NORMAL_ATTACK_DATA,
    ELEMENTAL_SKILL_DATA,
    ELEMENTAL_BURST_DATA,
    FrameDataDict,
    AttackDataDict,
)
from character.NODKRAI.columbina.entities import GravityRipple, LunarDomain


class ColumbinaNormalAttack(NormalAttackSkill):
    """普通攻击：月露泼降。"""

    def __init__(self, lv: int, caster: Any) -> None:
        super().__init__(lv, caster)
        self.action_frame_data: dict[str, FrameDataDict] = ACTION_FRAME_DATA
        self.attack_data: dict[str, AttackDataDict] = ATTACK_DATA
        self.multiplier_data: dict[str, tuple[str, list[float] | list[int] | list[list[float]]]] = NORMAL_ATTACK_DATA

        # 物理名称到倍率标签的映射
        self.label_map: dict[str, str] = {
            "普通攻击1": "一段伤害",
            "普通攻击2": "二段伤害",
            "普通攻击3": "三段伤害",
        }

        # 当前段数
        self.current_combo: int = 0


class ColumbinaChargedAttack(ChargedAttackSkill):
    """
    重击：月露涤荡。

    特殊机制：
    - 若拥有至少1枚草露，重击替换为月露涤荡
    - 消耗1枚草露，造成3次草元素月曜伤害
    - 不消耗体力
    """

    def __init__(self, lv: int, caster: Any) -> None:
        super().__init__(lv, caster)
        self.action_frame_data: dict[str, FrameDataDict] = ACTION_FRAME_DATA
        self.attack_data: dict[str, AttackDataDict] = ATTACK_DATA
        self.multiplier_data: dict[str, tuple[str, list[float] | list[int] | list[list[float]]]] = NORMAL_ATTACK_DATA

    def to_action_data(
        self, intent: Optional[Dict[str, Any]] = None
    ) -> ActionFrameData:
        """构建重击动作数据。"""
        # 检查是否有草露
        ctx = getattr(self.caster, "ctx", None)
        has_grass_dew = False

        if ctx:
            lunar_system = ctx.get_system(LunarReactionSystem)
            if lunar_system:
                has_grass_dew = lunar_system.can_consume_grass_dew(1)

        if has_grass_dew:
            # 使用月露涤荡数据
            f = ACTION_FRAME_DATA["月露涤荡"]
            return ActionFrameData(
                name="月露涤荡",
                action_type="charged_attack",
                total_frames=f["total_frames"],
                hit_frames=f["hit_frames"],
                interrupt_frames=f["interrupt_frames"],
                attack_config=None,  # 在 on_execute_hit 中动态构建
                origin_skill=self,
            )
        else:
            # 普通重击
            f = ACTION_FRAME_DATA["重击"]
            return ActionFrameData(
                name="重击",
                action_type="charged_attack",
                total_frames=f["total_frames"],
                hit_frames=f["hit_frames"],
                interrupt_frames=f["interrupt_frames"],
                attack_config=self._build_attack_config("重击"),
                origin_skill=self,
            )

    def on_execute_hit(self, target: Any, hit_index: int) -> None:
        """命中后执行伤害。"""
        ctx = getattr(self.caster, "ctx", None)

        # 检查是否使用月露涤荡
        instance = self.caster.action_manager.current_action
        if instance and instance.data.name == "月露涤荡":
            self._execute_dew_dissolution(target, hit_index, ctx)
        else:
            self._execute_normal_charged(target, hit_index)

    def _execute_normal_charged(self, target: Any, hit_index: int) -> None:
        """执行普通重击。"""
        values = NORMAL_ATTACK_DATA["重击伤害"][1]
        mult: float = values[self.lv - 1]  # type: ignore[assignment, arg-type, index]

        attack_config = self._build_attack_config("重击")
        dmg_obj = Damage(
            element=(Element.HYDRO, 1.0),
            damage_multiplier=(mult,),
            scaling_stat=("攻击力",),
            config=attack_config,
            name="重击",
        )
        dmg_obj.set_element(Element.HYDRO, ATTACK_DATA["重击"]["element_u"])

        self.caster.event_engine.publish(
            GameEvent(
                EventType.BEFORE_DAMAGE,
                get_current_time(),
                source=self.caster,
                data={"character": self.caster, "damage": dmg_obj},
            )
        )

    def _execute_dew_dissolution(
        self, target: Any, hit_index: int, ctx: Any
    ) -> None:
        """
        执行月露涤荡。

        月露涤荡造成3次草元素月曜伤害，每次使用不同的攻击配置。
        """
        if hit_index not in [0, 1, 2]:
            return

        # 第一次命中时消耗草露
        if hit_index == 0 and ctx:
            lunar_system = ctx.get_system(LunarReactionSystem)
            if lunar_system:
                lunar_system.consume_grass_dew(1)

        # 获取对应攻击配置
        attack_names = ["月露涤荡A", "月露涤荡B", "月露涤荡C"]
        attack_name = attack_names[hit_index]

        values = NORMAL_ATTACK_DATA["月露涤荡伤害"][1]
        mult: float = values[self.lv - 1]  # type: ignore[assignment, arg-type, index]

        attack_config = self._build_attack_config(attack_name)
        dmg_obj = Damage(
            element=(Element.DENDRO, 0),  # 月曜伤害无附着
            damage_multiplier=(mult,),
            scaling_stat=("生命值",),
            config=attack_config,
            name=f"月露涤荡-{hit_index + 1}",
        )
        # 标记为月绽放伤害
        dmg_obj.data["is_lunar_damage"] = True
        dmg_obj.data["lunar_type"] = "月绽放"

        self.caster.event_engine.publish(
            GameEvent(
                EventType.BEFORE_DAMAGE,
                get_current_time(),
                source=self.caster,
                data={"character": self.caster, "damage": dmg_obj},
            )
        )

    def _build_attack_config(self, name: str) -> AttackConfig:
        """构建攻击配置。"""
        p = ATTACK_DATA[name]

        shape_map = {
            "球": AOEShape.SPHERE,
            "圆柱": AOEShape.CYLINDER,
            "长方体": AOEShape.BOX,
        }
        strike_map = {
            "默认": StrikeType.DEFAULT,
            "钝击": StrikeType.BLUNT,
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
            strike_type=strike_map.get(p.get("strike_type", "默认"), StrikeType.DEFAULT),
            is_ranged=p.get("is_ranged", False),
            hitbox=hitbox,
        )


class ColumbinaPlungingAttack(PlungingAttackSkill):
    """下落攻击。"""

    def __init__(self, lv: int, caster: Any) -> None:
        super().__init__(lv, caster)
        self.action_frame_data: dict[str, FrameDataDict] = ACTION_FRAME_DATA
        self.attack_data: dict[str, AttackDataDict] = ATTACK_DATA
        self.multiplier_data: dict[str, tuple[str, list[float] | list[int] | list[list[float]]]] = NORMAL_ATTACK_DATA


class ColumbinaElementalSkill(SkillBase):
    """
    元素战技：万古潮汐。

    核心机制：
    1. 造成水元素范围伤害
    2. 唤出引力涟漪（跟随角色，持续伤害）
    3. 积攒引力值 -> 触发引力干涉
    """

    def __init__(self, lv: int, caster: Any) -> None:
        super().__init__(lv, caster)
        self.active_ripple: Optional[GravityRipple] = None
        self.remaining_frames = 0
        self.cd_frames = 1020  # 17秒

        # 产球冷却（战技和引力涟漪共用）
        self.last_particle_frame: int = -9999
        self.particle_cd: int = MECHANISM_CONFIG["ENERGY_PARTICLE_CD"]  # type: ignore[assignment]

    def to_action_data(
        self, intent: Optional[Dict[str, Any]] = None
    ) -> ActionFrameData:
        f = ACTION_FRAME_DATA["元素战技"]

        return ActionFrameData(
            name="元素战技",
            action_type="elemental_skill",
            total_frames=f["total_frames"],
            hit_frames=f["hit_frames"],
            interrupt_frames=f["interrupt_frames"],
            attack_config=self._build_attack_config("元素战技"),
            origin_skill=self,
        )

    def on_execute_hit(self, target: Any, hit_index: int) -> None:
        """战技命中后创建引力涟漪。"""
        # 造成初始伤害
        mult: float = ELEMENTAL_SKILL_DATA["技能伤害"][1][self.lv - 1]  # type: ignore[index]
        attack_config = self._build_attack_config("元素战技")

        dmg_obj = Damage(
            element=(Element.HYDRO, 1.0),
            damage_multiplier=(mult,),
            scaling_stat=("生命值",),
            config=attack_config,
            name="万古潮汐",
        )
        dmg_obj.set_element(Element.HYDRO, ATTACK_DATA["元素战技"]["element_u"])

        self.caster.event_engine.publish(
            GameEvent(
                EventType.BEFORE_DAMAGE,
                get_current_time(),
                source=self.caster,
                data={"character": self.caster, "damage": dmg_obj},
            )
        )

        # 产球逻辑
        self._try_spawn_energy_particle()

        # 创建引力涟漪
        self._spawn_gravity_ripple()

    def _try_spawn_energy_particle(self) -> bool:
        """
        尝试产生能量微粒。

        触发条件：元素战技命中
        产出：1~2个水元素微粒，概率 66.67%:33.33%
        冷却：3.5秒（与引力涟漪共用）

        Returns:
            bool: 是否成功产球
        """
        current_frame = get_current_time()
        particle_cd: int = self.particle_cd  # type: ignore[assignment]
        if current_frame - self.last_particle_frame < particle_cd:
            return False

        # 更新冷却
        self.last_particle_frame = current_frame

        # 随机决定微粒数量
        rates: tuple[float, float] = MECHANISM_CONFIG["ENERGY_PARTICLE_RATES"]  # type: ignore[assignment]
        num_particles = 1 if random.random() < rates[0] else 2

        # 产球
        from core.factory.entity_factory import EntityFactory
        EntityFactory.spawn_energy(
            num=num_particles,
            character=self.caster,
            element_energy=("水", 2),  # 水元素微粒，每个提供2点能量
            time=40,  # 约0.67秒后生效
        )

        get_emulation_logger().log_info(
            f"[元素战技] 产生 {num_particles} 个水元素微粒",
            sender="ColumbinaElementalSkill"
        )
        return True

    def can_spawn_particle(self) -> bool:
        """检查是否可以产球（供引力涟漪调用）。"""
        current_frame = get_current_time()
        return current_frame - self.last_particle_frame >= self.particle_cd

    def spawn_particle(self, source_name: str = "引力涟漪") -> bool:
        """
        执行产球逻辑（供引力涟漪调用）。

        Args:
            source_name: 产球来源名称，用于日志

        Returns:
            bool: 是否成功产球
        """
        current_frame = get_current_time()
        if current_frame - self.last_particle_frame < self.particle_cd:
            return False

        self.last_particle_frame = current_frame
        rates: tuple[float, float] = MECHANISM_CONFIG["ENERGY_PARTICLE_RATES"]  # type: ignore[assignment]
        num_particles = 1 if random.random() < rates[0] else 2

        from core.factory.entity_factory import EntityFactory
        EntityFactory.spawn_energy(
            num=num_particles,
            character=self.caster,
            element_energy=("水", 2),
            time=40,
        )

        get_emulation_logger().log_info(
            f"[{source_name}] 产生 {num_particles} 个水元素微粒",
            sender="ColumbinaElementalSkill"
        )
        return True

    def _spawn_gravity_ripple(self) -> None:
        """生成引力涟漪实体。"""
        # 清理旧的涟漪
        if self.active_ripple:
            self.active_ripple.finish()

        # 创建新涟漪
        self.active_ripple = GravityRipple(
            owner=self.caster,
            context=self.caster.ctx,
            skill_lv=self.lv,
        )
        duration: int = MECHANISM_CONFIG["GRAVITY_RIPPLE_DURATION"]  # type: ignore[assignment]
        self.active_ripple.life_frame = duration
        self.caster.ctx.space.register(self.active_ripple)

        self.remaining_frames = duration

    def on_frame_update(self) -> None:
        """每帧更新。"""
        if self.remaining_frames > 0:
            self.remaining_frames -= 1

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
            icd_tag=p.get("icd_tag", "None"),
            icd_group=p.get("icd_group", "None"),
            is_ranged=p.get("is_ranged", False),
            hitbox=hitbox,
        )


class ColumbinaElementalBurst(EnergySkill):
    """
    元素爆发：她的乡愁。

    核心机制：
    1. 造成水元素范围伤害
    2. 创建月之领域（持续20秒）
    3. 领域内月曜反应伤害提升
    """

    def __init__(self, lv: int, caster: Any) -> None:
        super().__init__(lv, caster)
        self.cd_frames = 900  # 15秒
        self.energy_cost = 60
        self.active_domain: Optional[LunarDomain] = None

    def to_action_data(
        self, intent: Optional[Dict[str, Any]] = None
    ) -> ActionFrameData:
        f = ACTION_FRAME_DATA["元素爆发"]

        return ActionFrameData(
            name="元素爆发",
            action_type="elemental_burst",
            total_frames=f["total_frames"],
            hit_frames=f["hit_frames"],
            interrupt_frames=f["interrupt_frames"],
            attack_config=self._build_attack_config("元素爆发"),
            origin_skill=self,
        )

    def on_execute_hit(self, target: Any, hit_index: int) -> None:
        """爆发命中后创建月之领域。"""
        # 造成初始伤害
        mult: float = ELEMENTAL_BURST_DATA["技能伤害"][1][self.lv - 1]  # type: ignore[index]
        attack_config = self._build_attack_config("元素爆发")

        dmg_obj = Damage(
            element=(Element.HYDRO, 2.0),
            damage_multiplier=(mult,),
            scaling_stat=("生命值",),
            config=attack_config,
            name="她的乡愁",
        )
        dmg_obj.set_element(Element.HYDRO, ATTACK_DATA["元素爆发"]["element_u"])

        self.caster.event_engine.publish(
            GameEvent(
                EventType.BEFORE_DAMAGE,
                get_current_time(),
                source=self.caster,
                data={"character": self.caster, "damage": dmg_obj},
            )
        )

        # 创建月之领域实体
        self._spawn_lunar_domain()

    def _spawn_lunar_domain(self) -> None:
        """生成月之领域实体。"""
        # 清理旧领域
        if self.active_domain:
            self.active_domain.finish()

        # 创建新领域
        self.active_domain = LunarDomain(
            owner=self.caster,
            context=self.caster.ctx,
            burst_lv=self.lv,
        )
        self.caster.ctx.space.register(self.active_domain)

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
            icd_tag=p.get("icd_tag", "None"),
            icd_group=p.get("icd_group", "None"),
            is_ranged=p.get("is_ranged", False),
            hitbox=hitbox,
        )