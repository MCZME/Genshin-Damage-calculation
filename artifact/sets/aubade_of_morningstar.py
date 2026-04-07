from typing import Any

from artifact.base_artifact_set import BaseArtifactSet
from core.registry import register_artifact_set
from core.event import EventType, GameEvent
from core.action.attack_tag_resolver import AttackTagResolver
from core.effect.common import MoonsignAscendantEffect


@register_artifact_set("晨星与月的晓歌")
class AubadeOfMorningstarSet(BaseArtifactSet):
    """
    晨星与月的晓歌套装效果实现。

    2件套：元素精通提高80点。
    4件套：
        - 装备者处于队伍后台时，造成的月曜反应伤害提升20%
        - 队伍的月兆等级至少为满辉时，造成的月曜反应伤害进一步提升40%
        - 上述效果将在装备者位于场上3秒后移除
    """

    # 常量定义
    ON_FIELD_THRESHOLD: int = 180  # 3秒 = 180帧
    BASE_BONUS: float = 20.0       # 后台基础加成
    FULL_MOON_BONUS: float = 40.0  # 满辉额外加成

    def __init__(self) -> None:
        super().__init__("晨星与月的晓歌")
        self.char: Any = None
        self.on_field_timer: int = 0
        self._effect_active: bool = True

    def apply_2_set_effect(self, character: Any) -> None:
        """2件套：元素精通提高80点（静态加成）。"""
        character.add_modifier(
            source=self.name + " (2件套)",
            stat="元素精通",
            value=80.0
        )

    def apply_4_set_effect(self, character: Any) -> None:
        """4件套：订阅事件处理动态效果。"""
        self.char = character
        self._effect_active = True

        # 订阅伤害计算前事件，用于注入月曜伤害加成
        character.event_engine.subscribe(EventType.BEFORE_CALCULATE, self)

        # 订阅帧更新事件，用于计时
        character.event_engine.subscribe(EventType.FRAME_END, self)

    def handle_event(self, event: GameEvent) -> None:
        """统一事件处理入口。"""
        if event.event_type == EventType.BEFORE_CALCULATE:
            self._apply_lunar_bonus(event)
        elif event.event_type == EventType.FRAME_END:
            self._handle_frame_update(event)

    def _is_off_field(self) -> bool:
        """判断装备者是否处于后台。"""
        return self.char is not None and not self.char.on_field

    def _is_full_moon(self) -> bool:
        """判断队伍月兆等级是否为满辉。"""
        if not self.char:
            return False

        # 检查角色是否拥有月兆·满辉效果
        for effect in getattr(self.char, 'active_effects', []):
            if isinstance(effect, MoonsignAscendantEffect):
                return True

        return False

    def _is_lunar_damage(self, dmg_ctx: Any) -> bool:
        """判断当前伤害是否为月曜反应伤害。"""
        config = getattr(dmg_ctx, 'config', None)
        if not config:
            return False

        return AttackTagResolver.is_lunar_damage(
            config.attack_tag,
            getattr(config, 'extra_attack_tags', None)
        )

    def _handle_frame_update(self, event: GameEvent) -> None:
        """处理帧更新：场上计时。"""
        if not self.char:
            return

        if self.char.on_field:
            # 角色在场上，累计计时
            self.on_field_timer += 1

            # 达到3秒阈值，禁用效果
            if self.on_field_timer >= self.ON_FIELD_THRESHOLD:
                self._effect_active = False
        else:
            # 角色下场，重置计时器并激活效果
            self.on_field_timer = 0
            self._effect_active = True

    def _apply_lunar_bonus(self, event: GameEvent) -> None:
        """
        在伤害计算前注入月曜反应伤害加成。

        条件：
        1. 效果处于激活状态
        2. 角色处于后台
        3. 当前伤害为月曜反应伤害
        """
        # 检查效果是否激活
        if not self._effect_active:
            return

        # 检查是否在后台
        if not self._is_off_field():
            return

        dmg_ctx = event.data.get("damage_context")
        if not dmg_ctx:
            return

        # 检查是否为月曜反应伤害
        if not self._is_lunar_damage(dmg_ctx):
            return

        # 注入后台基础加成 20%
        dmg_ctx.add_modifier(
            source=self.name + " (4件套后台)",
            stat="月曜反应伤害提升",
            value=self.BASE_BONUS,
            op="ADD",
            audit=True
        )

        # 如果满辉，额外注入 40%
        if self._is_full_moon():
            dmg_ctx.add_modifier(
                source=self.name + " (4件套满辉)",
                stat="月曜反应伤害提升",
                value=self.FULL_MOON_BONUS,
                op="ADD",
                audit=True
            )
