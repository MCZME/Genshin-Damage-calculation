"""哥伦比娅命座实现。"""

from core.effect.common import ConstellationEffect
from core.event import EventType, GameEvent
from core.tool import get_current_time
from core.systems.utils import AttributeCalculator
from core.systems.contract.healing import Healing, HealingType


class ColumbinaC1(ConstellationEffect):
    """
    命座一：遍照花海，隐入群山。

    施放元素战技时，立刻触发一次引力干涉效果。
    每15秒至多触发一次。

    月兆·满辉效果：
    - 月感电：恢复6点元素能量
    - 月绽放：提升抗打断能力
    - 月结晶：唤出雨海护盾
    """

    def __init__(self):
        super().__init__("遍照花海，隐入群山", unlock_constellation=1)
        self.last_trigger_frame = -9999
        self.cd_frames = 900  # 15秒

    def on_apply(self) -> None:
        if self.character and self.character.event_engine:
            self.character.event_engine.subscribe(EventType.BEFORE_SKILL, self)

    def handle_event(self, event: GameEvent) -> None:
        if event.event_type == EventType.BEFORE_SKILL:
            current_frame = get_current_time()
            if current_frame - self.last_trigger_frame >= self.cd_frames:
                # 触发引力干涉
                self._trigger_instant_interference()
                self.last_trigger_frame = current_frame

    def _trigger_instant_interference(self) -> None:
        """立刻触发一次引力干涉。"""
        # 发布引力干涉事件
        self.character.event_engine.publish(
            GameEvent(
                EventType.GRAVITY_INTERFERENCE,
                get_current_time(),
                source=self.character,
                data={
                    "lunar_type": self.character.get_dominant_gravity_type(),
                    "is_c1_trigger": True,
                }
            )
        )


class ColumbinaC2(ConstellationEffect):
    """
    命座二：为夜增辉，与君遥伴。

    引力值积攒速度提升34%。
    触发引力干涉时，获得皎辉效果（生命值上限+40%，持续8秒）。
    """

    def __init__(self):
        super().__init__("为夜增辉，与君遥伴", unlock_constellation=2)
        self.radiance_active = False
        self.radiance_timer = 0

    def on_apply(self) -> None:
        # 积攒速度加成在 char.add_gravity 中处理
        if self.character and self.character.event_engine:
            self.character.event_engine.subscribe(EventType.GRAVITY_INTERFERENCE, self)

    def handle_event(self, event: GameEvent) -> None:
        if event.event_type == EventType.GRAVITY_INTERFERENCE:
            self._activate_radiance()

    def _activate_radiance(self) -> None:
        """激活皎辉效果。"""
        self.radiance_active = True
        self.radiance_timer = 480  # 8秒

        # 注入生命值加成
        self.character.add_modifier(
            source="皎辉",
            stat="生命值%",
            value=40.0,
        )

    def on_frame_update(self) -> None:
        if not self.is_active or not self.radiance_active:
            return

        self.radiance_timer -= 1
        if self.radiance_timer <= 0:
            self._deactivate_radiance()

    def _deactivate_radiance(self) -> None:
        """移除皎辉效果。"""
        self.radiance_active = False
        self.character.dynamic_modifiers = [
            m for m in self.character.dynamic_modifiers
            if m.source != "皎辉"
        ]


class ColumbinaC3(ConstellationEffect):
    """命座三：柔光凝露，梦湖起波。元素战技等级+3。"""

    def __init__(self):
        super().__init__("柔光凝露，梦湖起波", unlock_constellation=3)

    def on_apply(self) -> None:
        if self.character:
            self.character.skill_params[1] = min(15, self.character.skill_params[1] + 3)


class ColumbinaC4(ConstellationEffect):
    """
    命座四：花岚云翳，山岩树影。

    触发引力干涉时，恢复4点元素能量。
    根据月曜反应类型提升引力干涉伤害（每15秒至多一次）。
    """

    def __init__(self):
        super().__init__("花岚云翳，山岩树影", unlock_constellation=4)
        self.last_damage_bonus_frame = -9999
        self.damage_bonus_cd = 900  # 15秒

    def on_apply(self) -> None:
        if self.character and self.character.event_engine:
            self.character.event_engine.subscribe(EventType.GRAVITY_INTERFERENCE, self)

    def handle_event(self, event: GameEvent) -> None:
        if event.event_type == EventType.GRAVITY_INTERFERENCE:
            # 恢复能量
            if hasattr(self.character, "elemental_energy") and self.character.elemental_energy:
                self.character.elemental_energy.gain_energy(4.0, source_type="命座四")

            # 伤害加成标记
            current_frame = get_current_time()
            if current_frame - self.last_damage_bonus_frame >= self.damage_bonus_cd:
                event.data["c4_damage_bonus"] = True
                self.last_damage_bonus_frame = current_frame


class ColumbinaC5(ConstellationEffect):
    """命座五：万籁俱寂，唯闻君唱。元素爆发等级+3。"""

    def __init__(self):
        super().__init__("万籁俱寂，唯闻君唱", unlock_constellation=5)

    def on_apply(self) -> None:
        if self.character:
            self.character.skill_params[2] = min(15, self.character.skill_params[2] + 3)


class ColumbinaC6(ConstellationEffect):
    """
    命座六：夜昏且暗，且随月光。

    处于月之领域中的角色触发月曜反应后，
    对应元素类型的暴击伤害提升80%，持续8秒。
    """

    def __init__(self):
        super().__init__("夜昏且暗，且随月光", unlock_constellation=6)
        self.element_crit_bonus: dict[str, int] = {}  # element -> remaining_frames

    def on_apply(self) -> None:
        if self.character and self.character.event_engine:
            self.character.event_engine.subscribe(EventType.AFTER_LUNAR_BLOOM, self)
            self.character.event_engine.subscribe(EventType.AFTER_LUNAR_CHARGED, self)
            self.character.event_engine.subscribe(EventType.AFTER_LUNAR_CRYSTALLIZE, self)
            self.character.event_engine.subscribe(EventType.BEFORE_CALCULATE, self)

    def handle_event(self, event: GameEvent) -> None:
        current_frame = get_current_time()

        if event.event_type in [
            EventType.AFTER_LUNAR_BLOOM,
            EventType.AFTER_LUNAR_CHARGED,
            EventType.AFTER_LUNAR_CRYSTALLIZE,
        ]:
            # 检查是否在月之领域内
            if not getattr(self.character, "lunar_domain_active", False):
                return

            # 根据反应类型确定元素
            element_map = {
                EventType.AFTER_LUNAR_BLOOM: "草",
                EventType.AFTER_LUNAR_CHARGED: "雷",
                EventType.AFTER_LUNAR_CRYSTALLIZE: "岩",
            }
            element = element_map[event.event_type]
            self.element_crit_bonus[element] = 480  # 8秒

        elif event.event_type == EventType.BEFORE_CALCULATE:
            dmg_ctx = event.data.get("damage_context")
            if dmg_ctx:
                dmg = dmg_ctx.damage
                element = str(dmg.element[0]).replace("Element.", "")
                element_name_map = {
                    "DENDRO": "草",
                    "ELECTRO": "雷",
                    "GEO": "岩",
                }
                element_cn = element_name_map.get(element)
                if element_cn and element_cn in self.element_crit_bonus:
                    if self.element_crit_bonus[element_cn] > 0:
                        dmg_ctx.add_modifier(
                            source=f"C6-{element_cn}暴伤",
                            stat="暴击伤害",
                            value=80.0,
                        )

    def on_frame_update(self) -> None:
        if not self.is_active:
            return

        # 更新计时器
        for element in list(self.element_crit_bonus.keys()):
            self.element_crit_bonus[element] -= 1
            if self.element_crit_bonus[element] <= 0:
                del self.element_crit_bonus[element]
