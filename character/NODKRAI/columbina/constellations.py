"""哥伦比娅命座实现。"""

from typing import Any

from core.action.attack_tag_resolver import AttackTagResolver
from core.effect.common import ConstellationEffect
from core.event import EventType, GameEvent
from core.logger import get_emulation_logger
from core.mechanics.aura import Element
from core.systems.contract.shield import ShieldConfig
from core.systems.shield_system import ShieldSystem
from core.systems.utils import AttributeCalculator
from core.tool import get_current_time


class ColumbinaConstellationEffect(ConstellationEffect):
    """
    哥伦比娅命座效果基类。

    提供所有命座共享的月曜伤害擢升效果。
    子类需要设置 self.lunar_damage_bonus 值（百分比）。
    """

    # 子类应覆盖此值，设为 0 则不生效
    lunar_damage_bonus: float = 0.0

    def on_apply(self) -> None:
        """子类应调用 super().on_apply() 或自行订阅事件。"""
        pass

    def handle_event(self, event: GameEvent) -> None:
        """处理事件，子类应调用 super().handle_event(event)。"""
        if self.lunar_damage_bonus > 0 and event.event_type == EventType.BEFORE_CALCULATE:
            self._apply_lunar_damage_bonus(event)

    def _subscribe_lunar_damage_event(self) -> None:
        """手动订阅月曜伤害擢升事件（当子类不调用 super().on_apply() 时使用）。"""
        if self.character and self.character.event_engine and self.lunar_damage_bonus > 0:
            self.character.event_engine.subscribe(EventType.BEFORE_CALCULATE, self)

    def _apply_lunar_damage_bonus(self, event: GameEvent) -> None:
        """
        队伍中附近的所有角色造成的月曜反应伤害擢升。
        效果值由子类的 lunar_damage_bonus 属性决定。
        """
        dmg_ctx = event.data.get("damage_context")
        if not dmg_ctx:
            return

        dmg = dmg_ctx.damage
        # 使用 AttackTagResolver 判断月曜伤害
        if not AttackTagResolver.is_lunar_damage(
            dmg.config.attack_tag,
            getattr(dmg.config, "extra_attack_tags", None)
        ):
            return

        dmg_ctx.add_modifier(
            source=f"C{self.unlock_constellation}月曜伤害",
            stat="月曜伤害擢升",
            value=self.lunar_damage_bonus,
            op="ADD",
            audit=True,
        )


class ColumbinaC1(ColumbinaConstellationEffect):
    """
    命座一：遍照花海，隐入群山。

    施放元素战技时，立刻触发一次引力干涉效果。
    每15秒至多触发一次。

    月兆·满辉状态下，触发引力干涉时根据月曜类型为场上角色提供增益：
    - 月感电：恢复6点元素能量
    - 月绽放：提升抗打断能力
    - 月结晶：唤出雨海护盾

    队伍中附近的所有角色造成的月曜反应伤害擢升1.5%。
    """

    lunar_damage_bonus = 1.5

    def __init__(self):
        super().__init__("遍照花海，隐入群山", unlock_constellation=1)
        self.last_trigger_frame = -9999
        self.cd_frames = 900  # 15秒

    def on_apply(self) -> None:
        super().on_apply()
        if self.character and self.character.event_engine:
            # 订阅元素战技事件（触发引力干涉）
            self.character.event_engine.subscribe(EventType.BEFORE_SKILL, self)
            # 订阅引力干涉事件（触发月兆·满辉效果）
            self.character.event_engine.subscribe(EventType.GRAVITY_INTERFERENCE, self)
            # 订阅月曜伤害擢升事件
            self._subscribe_lunar_damage_event()

    def handle_event(self, event: GameEvent) -> None:
        super().handle_event(event)
        if event.event_type == EventType.BEFORE_SKILL and event.source == self.character:
            self._handle_skill_event(event)
        elif event.event_type == EventType.GRAVITY_INTERFERENCE:
            self._handle_gravity_interference(event)

    def _handle_skill_event(self, event: GameEvent) -> None:
        """处理元素战技事件：触发引力干涉。"""
        current_frame = get_current_time()
        if current_frame - self.last_trigger_frame >= self.cd_frames:
            self._trigger_instant_interference()
            self.last_trigger_frame = current_frame

    def _trigger_instant_interference(self) -> None:
        """立刻触发一次引力干涉。"""
        if not self.character:
            return

        ctx = getattr(self.character, "ctx", None)
        if not ctx or not ctx.space:
            return

        # 确定月曜类型
        lunar_type = "月绽放"
        if hasattr(self.character, "get_dominant_gravity_type"):
            lunar_type = self.character.get_dominant_gravity_type() # type: ignore

        # 直接创建引力干涉攻击实体
        from character.NODKRAI.columbina.entities import GravityInterference

        skill = self.character.skills.get("elemental_skill")
        skill_lv = skill.lv if skill else 1

        interference = GravityInterference(
            owner=self.character,
            context=ctx,
            lunar_type=lunar_type,
            skill_lv=skill_lv,
        )
        ctx.space.register(interference)

        # 发布引力干涉事件，触发其他命座效果（C2皎辉、C4能量恢复等）
        if self.character.event_engine:
            self.character.event_engine.publish(
                GameEvent(
                    EventType.GRAVITY_INTERFERENCE,
                    get_current_time(),
                    source=self.character,
                    data={
                        "lunar_type": lunar_type,
                        "is_c1_trigger": True,
                    }
                )
            )

        get_emulation_logger().log_info(
            f"[C1] 立刻触发引力干涉·{lunar_type}",
            sender="ColumbinaC1"
        )

    def _is_ascendant_active(self) -> bool:
        """检查队伍是否处于月兆·满辉状态（通过检查角色是否有月兆·满辉效果标记）。"""
        if not self.character:
            return False
        return self.character.has_effect("月兆·满辉")

    def _handle_gravity_interference(self, event: GameEvent) -> None:
        """
        处理引力干涉事件：在月兆·满辉状态下为场上角色提供增益。
        """
        # 仅在月兆·满辉状态下触发
        if not self._is_ascendant_active():
            return

        lunar_type = event.data.get("lunar_type", "月绽放")
        self._apply_c1_bonus(lunar_type)

    def _apply_c1_bonus(self, lunar_type: str) -> None:
        """
        C1月兆·满辉效果：根据月曜类型为场上角色提供增益。

        Args:
            lunar_type: 月曜反应类型 ("月感电"/"月绽放"/"月结晶")
        """
        if not self.character:
            return

        ctx = getattr(self.character, "ctx", None)
        if not ctx:
            return

        # 获取当前场上角色
        active_char = None
        if ctx.space and ctx.space.team:
            active_char = ctx.space.team.current_character

        if not active_char:
            return

        # 根据月曜类型触发对应效果
        if lunar_type == "月感电":
            self._apply_energy_restore(active_char)
        elif lunar_type == "月绽放":
            self._apply_interruption_resistance(active_char)
        elif lunar_type == "月结晶":
            self._apply_rain_shield(active_char)

    def _apply_energy_restore(self, target: Any) -> None:
        """
        月感电：为队伍中当前场上角色恢复6点元素能量。
        """
        if hasattr(target, "elemental_energy") and target.elemental_energy:
            target.elemental_energy.gain(6.0)
            get_emulation_logger().log_info(
                f"[C1月兆·满辉] 月感电为 {target.name} 恢复6点元素能量",
                sender="ColumbinaC1"
            )

    def _apply_interruption_resistance(self, target: Any) -> None:
        """
        月绽放：提升队伍中当前场上角色的抗打断能力，持续8秒。
        模拟中不考虑抗打断效果，仅记录日志。
        """
        get_emulation_logger().log_info(
            f"[C1月兆·满辉] 月绽放为 {target.name} 提供抗打断能力（模拟忽略）",
            sender="ColumbinaC1"
        )

    def _apply_rain_shield(self, target: Any) -> None:
        """
        月结晶：唤出雨海护盾。
        - 伤害吸收量受益于哥伦比娅生命值上限的12%
        - 对水元素伤害有250%的吸收效果
        - 持续8秒
        """
        ctx = getattr(self.character, "ctx", None)
        if not ctx:
            return

        # 计算护盾量：哥伦比娅生命值上限 * 12%
        columbina_hp = AttributeCalculator.get_val_by_name(self.character, "生命值")
        shield_hp = columbina_hp * 0.12

        # 获取护盾系统
        shield_sys = ctx.get_system(ShieldSystem)
        if shield_sys:
            config = ShieldConfig(
                base_hp=shield_hp,
                element=Element.HYDRO,  # 水元素护盾，对水伤害有250%吸收
                duration=480,  # 8秒
                name="雨海护盾",
                creator=self.character,
            )
            shield_sys.add_shield(target, config)

            get_emulation_logger().log_info(
                f"[C1月兆·满辉] 月结晶为 {target.name} 创建雨海护盾 (吸收量: {round(shield_hp, 1)})",
                sender="ColumbinaC1"
            )


class ColumbinaC2(ColumbinaConstellationEffect):
    """
    命座二：为夜增辉，与君遥伴。

    引力值积攒速度提升34%。
    触发引力干涉时，获得皎辉效果（生命值上限+40%，持续8秒）。

    月兆·满辉状态下，皎辉期间触发引力干涉时，根据月曜类型为场上角色提供属性加成：
    - 月感电：攻击力 + 生命值上限的1%
    - 月绽放：元素精通 + 生命值上限的0.35%
    - 月结晶：防御力 + 生命值上限的1%

    月曜反应伤害擢升7%。
    """

    lunar_damage_bonus = 7.0

    def __init__(self):
        super().__init__("为夜增辉，与君遥伴", unlock_constellation=2)

    def on_apply(self) -> None:
        super().on_apply()
        # 积攒速度加成在 char.add_gravity 中处理
        if self.character and self.character.event_engine:
            self.character.event_engine.subscribe(EventType.GRAVITY_INTERFERENCE, self)
            # 订阅月曜伤害擢升事件
            self._subscribe_lunar_damage_event()

    def handle_event(self, event: GameEvent) -> None:
        super().handle_event(event)
        if event.event_type == EventType.GRAVITY_INTERFERENCE:
            self._on_gravity_interference(event)

    def _is_ascendant_active(self) -> bool:
        """检查队伍是否处于月兆·满辉状态（通过检查角色是否有月兆·满辉效果标记）。"""
        if not self.character:
            return False
        return self.character.has_effect("月兆·满辉")

    def _on_gravity_interference(self, event: GameEvent) -> None:
        """处理引力干涉事件。"""
        # 检查是否有皎辉效果
        has_radiance = self._has_radiance_effect()

        # 触发或刷新皎辉效果
        self._apply_radiance()

        # 月兆·满辉状态下，皎辉期间触发属性加成（只在新获得皎辉时不触发，刷新时触发）
        if has_radiance and self._is_ascendant_active():
            self._apply_c2_stat_bonus(event)

    def _has_radiance_effect(self) -> bool:
        """检查角色是否有皎辉效果。"""
        if not self.character:
            return False
        return self.character.has_effect("皎辉")

    def _get_radiance_effect(self) -> Any:
        """获取皎辉效果实例。"""
        if not self.character:
            return None
        return self.character.get_effect("皎辉")

    def _apply_radiance(self) -> None:
        """触发或刷新皎辉效果。"""
        if not self.character:
            return

        from character.NODKRAI.columbina.effects import RadianceEffect

        # 使用 apply() 方法，它会自动处理堆叠/刷新逻辑
        RadianceEffect(self.character).apply()

    def _apply_c2_stat_bonus(self, event: GameEvent) -> None:
        """
        C2月兆·满辉效果：皎辉期间触发引力干涉时，根据月曜类型为场上角色提供属性加成。
        """
        if not self.character:
            return

        ctx = getattr(self.character, "ctx", None)
        if not ctx or not ctx.space or not ctx.space.team:
            return

        # 获取当前场上角色
        active_char = ctx.space.team.current_character
        if not active_char:
            return

        # 获取皎辉效果的剩余时间
        radiance = self._get_radiance_effect()
        if not radiance:
            return
        remaining_frames = radiance.duration

        # 获取月曜类型
        lunar_type = event.data.get("lunar_type", "月绽放")

        from character.NODKRAI.columbina.effects import C2StatBonusEffect

        # 移除之前的C2属性加成效果
        self._clear_c2_stat_bonus(active_char)

        # 创建新的属性加成效果
        C2StatBonusEffect(
            owner=active_char,
            source_char=self.character,
            lunar_type=lunar_type,
            duration=remaining_frames,
        ).apply()

    def _clear_c2_stat_bonus(self, target: Any) -> None:
        """清除目标角色上的C2月兆·满辉效果。"""
        for effect in target.get_effects_by_prefix("C2月兆·满辉"):
            effect.remove()


class ColumbinaC3(ColumbinaConstellationEffect):
    """
    命座三：柔光凝露，梦湖起波。

    元素战技等级+3。

    队伍中附近的所有角色造成的月曜反应伤害擢升1.5%。
    """
    lunar_damage_bonus = 1.5

    def __init__(self):
        super().__init__("柔光凝露，梦湖起波", unlock_constellation=3)

    def on_apply(self) -> None:
        super().on_apply()
        if self.character:
            self.character.skill_params[1] = min(15, self.character.skill_params[1] + 3)
        self._subscribe_lunar_damage_event()


class ColumbinaC4(ColumbinaConstellationEffect):
    """
    命座四：花岚云翳，山岩树影。

    触发引力干涉时，为哥伦比娅恢复4点元素能量。
    根据月曜反应类型提升引力干涉伤害：
    - 月感电：生命值上限的12.5%
    - 月绽放：生命值上限的2.5%
    - 月结晶：生命值上限的12.5%
    上述效果每15秒至多触发一次。

    队伍中附近的所有角色造成的月曜反应伤害擢升1.5%。
    """
    lunar_damage_bonus = 1.5

    # 月曜类型 -> 生命值倍率
    LUNAR_BONUS_MAP = {
        "月感电": 0.125,
        "月绽放": 0.025,
        "月结晶": 0.125,
    }

    # 不同类型的引力干涉持续时间（帧数）
    INTERFERENCE_DURATION = {
        "月感电": 30,  # 约0.5秒
        "月绽放": 150,  # 约2.5秒（5段伤害）
        "月结晶": 30,  # 约0.5秒
    }

    def __init__(self):
        super().__init__("花岚云翳，山岩树影", unlock_constellation=4)
        self.last_damage_bonus_frame = -9999
        self.damage_bonus_cd = 900  # 15秒
        # 当前激活的伤害加成信息
        self.active_bonus: float = 0.0
        self.active_bonus_end_frame: int = -9999  # 加成失效帧

    def on_apply(self) -> None:
        super().on_apply()
        if self.character and self.character.event_engine:
            self.character.event_engine.subscribe(EventType.GRAVITY_INTERFERENCE, self)
            self._subscribe_lunar_damage_event()

    def handle_event(self, event: GameEvent) -> None:
        super().handle_event(event)
        if event.event_type == EventType.GRAVITY_INTERFERENCE:
            self._on_gravity_interference(event)
        elif event.event_type == EventType.BEFORE_CALCULATE:
            self._apply_damage_bonus_to_context(event)

    def _on_gravity_interference(self, event: GameEvent) -> None:
        """处理引力干涉事件。"""
        # 恢复能量
        if self.character and hasattr(self.character, "elemental_energy") and self.character.elemental_energy:
            self.character.elemental_energy.gain(4.0)

        # 伤害加成（每15秒至多一次）
        current_frame = get_current_time()
        if current_frame - self.last_damage_bonus_frame >= self.damage_bonus_cd:
            self._activate_damage_bonus(event)
            self.last_damage_bonus_frame = current_frame

    def _activate_damage_bonus(self, event: GameEvent) -> None:
        """
        激活伤害加成，在引力干涉持续期间对所有伤害段生效。
        """
        if not self.character:
            return

        lunar_type = event.data.get("lunar_type", "月绽放")
        multiplier = self.LUNAR_BONUS_MAP.get(lunar_type, 0.025)

        # 计算伤害加成值
        columbina_hp = AttributeCalculator.get_val_by_name(self.character, "生命值")
        self.active_bonus = columbina_hp * multiplier

        # 设置有效期
        duration = self.INTERFERENCE_DURATION.get(lunar_type, 30)
        self.active_bonus_end_frame = get_current_time() + duration

        get_emulation_logger().log_info(
            f"[C4] {lunar_type}引力干涉伤害提升激活: {round(self.active_bonus, 1)}，持续{duration}帧",
            sender="ColumbinaC4"
        )

    def _apply_damage_bonus_to_context(self, event: GameEvent) -> None:
        """
        在伤害计算前应用C4的伤害加成。
        仅对引力干涉伤害生效，且在有效期内。
        """
        # 检查是否在有效期内
        if self.active_bonus <= 0 or get_current_time() > self.active_bonus_end_frame:
            self.active_bonus = 0.0
            return

        dmg_ctx = event.data.get("damage_context")
        if not dmg_ctx:
            return

        dmg = dmg_ctx.damage
        # 检查是否为引力干涉伤害（通过伤害名称判断）
        if dmg.name and dmg.name.startswith("引力干涉"):
            # 月曜伤害使用"附加伤害"字段
            dmg.data["附加伤害"] = dmg.data.get("附加伤害", 0) + self.active_bonus
            get_emulation_logger().log_info(
                f"[C4] 引力干涉伤害提升 {round(self.active_bonus, 1)} 已应用",
                sender="ColumbinaC4"
            )


class ColumbinaC5(ColumbinaConstellationEffect):
    """
    命座五：万籁俱寂，唯闻君唱。

    元素爆发等级+3。

    队伍中附近的所有角色造成的月曜反应伤害擢升1.5%。
    """
    lunar_damage_bonus = 1.5

    def __init__(self):
        super().__init__("万籁俱寂，唯闻君唱", unlock_constellation=5)

    def on_apply(self) -> None:
        super().on_apply()
        if self.character:
            self.character.skill_params[2] = min(15, self.character.skill_params[2] + 3)
        self._subscribe_lunar_damage_event()


class ColumbinaC6(ColumbinaConstellationEffect):
    """
    命座六：夜昏且暗，且随月光。

    处于月之领域中的所有角色触发月曜反应后的8秒内，
    依据参与反应的元素类型，使队伍中的所有角色造成的
    对应元素类型伤害的暴击伤害提升80%。
    同种元素类型的暴击伤害提升效果无法叠加。

    队伍中附近的所有角色造成的月曜反应伤害擢升7%。
    """
    lunar_damage_bonus = 7.0

    # 月曜反应事件类型 -> 元素类型
    EVENT_ELEMENT_MAP = {
        EventType.AFTER_LUNAR_BLOOM: "草",
        EventType.AFTER_LUNAR_CHARGED: "雷",
        EventType.AFTER_LUNAR_CRYSTALLIZE: "岩",
    }

    # Element枚举 -> 中文名
    ELEMENT_NAME_MAP = {
        "DENDRO": "草",
        "ELECTRO": "雷",
        "GEO": "岩",
    }

    def __init__(self):
        super().__init__("夜昏且暗，且随月光", unlock_constellation=6)
        # 元素类型 -> 失效帧（同种元素无法叠加，只刷新时间）
        self.element_crit_bonus_end: dict[str, int] = {}

    def on_apply(self) -> None:
        super().on_apply()
        if self.character and self.character.event_engine:
            self.character.event_engine.subscribe(EventType.AFTER_LUNAR_BLOOM, self)
            self.character.event_engine.subscribe(EventType.AFTER_LUNAR_CHARGED, self)
            self.character.event_engine.subscribe(EventType.AFTER_LUNAR_CRYSTALLIZE, self)
            self._subscribe_lunar_damage_event()

    def handle_event(self, event: GameEvent) -> None:
        super().handle_event(event)
        if event.event_type in self.EVENT_ELEMENT_MAP:
            self._on_lunar_reaction(event)
        elif event.event_type == EventType.BEFORE_CALCULATE:
            self._apply_crit_bonus(event)

    def _on_lunar_reaction(self, event: GameEvent) -> None:
        """
        处理月曜反应事件。
        检查触发者是否在月之领域内，如果是则激活对应元素的暴击伤害加成。
        """
        # 获取触发者
        trigger = event.source
        if not trigger:
            return

        # 检查触发者是否在月之领域内
        if not self._is_in_lunar_domain(trigger):
            return

        # 确定元素类型
        element = self.EVENT_ELEMENT_MAP[event.event_type]

        # 激活暴击伤害加成（8秒 = 480帧）
        current_frame = get_current_time()
        self.element_crit_bonus_end[element] = current_frame + 480

        get_emulation_logger().log_info(
            f"[C6] {element}元素暴击伤害+80% 激活，持续8秒",
            sender="ColumbinaC6"
        )

    def _is_in_lunar_domain(self, character: Any) -> bool:
        """检查角色是否在月之领域内。"""
        from character.NODKRAI.columbina.entities import LunarDomain

        domains = LunarDomain.get_active_scenes("月之领域")
        for domain in domains:
            if hasattr(domain, "_entities_in_range"):
                if character.entity_id in domain._entities_in_range:
                    return True
        return False

    def _apply_crit_bonus(self, event: GameEvent) -> None:
        """
        在伤害计算前应用暴击伤害加成。
        对队伍中所有角色生效，检查伤害元素类型是否匹配激活的加成。
        """
        # 检查是否有激活的加成
        current_frame = get_current_time()
        active_elements = [
            elem for elem, end_frame in self.element_crit_bonus_end.items()
            if end_frame > current_frame
        ]

        if not active_elements:
            return

        dmg_ctx = event.data.get("damage_context")
        if not dmg_ctx:
            return

        dmg = dmg_ctx.damage

        # 获取伤害元素类型（中文名）
        element_enum = str(dmg.element[0]).replace("Element.", "")
        element_cn = self.ELEMENT_NAME_MAP.get(element_enum)

        if not element_cn or element_cn not in active_elements:
            return

        # 应用暴击伤害加成
        dmg_ctx.add_modifier(
            source=f"C6-{element_cn}暴伤",
            stat="暴击伤害",
            value=80.0,
        )
