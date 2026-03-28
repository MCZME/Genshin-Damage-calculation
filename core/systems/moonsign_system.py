"""
月兆系统核心类。

负责月兆等级计算、效果应用、非月兆角色增益管理。
参考元素共鸣系统的实现模式。
"""

from typing import Any

from core.systems.base_system import GameSystem
from core.systems.utils import AttributeCalculator
from core.event import GameEvent, EventType
from core.effect.common import MoonsignTalent, MoonsignNascentEffect, MoonsignAscendantEffect


class MoonsignSystem(GameSystem):
    """
    月兆系统 - 队伍级增益管理。

    月兆等级在战斗开始时确定，后续不会改变。

    等级规则：
    - 0级：无月兆角色
    - 1级（初辉）：1名月兆角色
    - 2级（满辉）：2名及以上月兆角色
    """

    # 增益上限
    NON_MOONSIGN_BONUS_CAP: float = 36.0

    def __init__(self) -> None:
        super().__init__()

        # 月兆等级 (0/1/2)，战斗开始时确定
        self.moonsign_level: int = 0

        # 月兆角色列表
        self.moonsign_characters: list[Any] = []

        # 非月兆角色增益
        self.non_moonsign_bonus: float = 0.0
        self.non_moonsign_source: Any = None
        self.non_moonsign_timer: int = 0  # 剩余帧数 (20秒 = 1200帧)
        self.non_moonsign_duration: int = 1200

    def initialize(self, context: Any) -> None:
        """初始化系统，检测月兆角色并应用效果。"""
        super().initialize(context)
        self._detect_and_apply_moonsign()

    def register_events(self, engine: Any) -> None:
        """订阅事件。"""
        engine.subscribe(EventType.AFTER_SKILL, self)
        engine.subscribe(EventType.AFTER_BURST, self)
        engine.subscribe(EventType.BEFORE_CALCULATE, self)

    def handle_event(self, event: GameEvent) -> None:
        """事件处理。"""
        if event.event_type == EventType.AFTER_SKILL:
            self._on_skill_or_burst(event)
        elif event.event_type == EventType.AFTER_BURST:
            self._on_skill_or_burst(event)
        elif event.event_type == EventType.BEFORE_CALCULATE:
            self._on_before_calculate(event)

    # ================================
    # 月兆等级管理（初始化时确定）
    # ================================

    def _detect_and_apply_moonsign(self) -> None:
        """检测月兆角色并应用效果（仅初始化时调用）。"""
        if not self.context or not self.context.space or not self.context.space.team:
            return

        members = self.context.space.team.get_members()

        # 检测月兆角色
        self.moonsign_characters = [
            c for c in members if self._is_moonsign_character(c)
        ]

        # 计算月兆等级：1名→初辉，2名及以上→满辉
        count = len(self.moonsign_characters)
        if count >= 2:
            self.moonsign_level = 2
        elif count == 1:
            self.moonsign_level = 1
        else:
            self.moonsign_level = 0

        # 应用效果标记
        self._apply_moonsign_effects(members)

    def _is_moonsign_character(self, character: Any) -> bool:
        """
        判断角色是否为月兆角色。

        通过检查角色的 talents 列表中是否有 MoonsignTalent 实例。
        """
        talents = getattr(character, 'talents', [])
        for talent in talents:
            if isinstance(talent, MoonsignTalent):
                return True
        return False

    def _apply_moonsign_effects(self, members: list[Any]) -> None:
        """为全队应用月兆效果标记。"""
        if self.moonsign_level == 0:
            return

        for character in members:
            # 应用初辉效果
            if self.moonsign_level >= 1:
                nascent = MoonsignNascentEffect(character)
                character.add_effect(nascent)

            # 应用满辉效果
            if self.moonsign_level >= 2:
                ascendant = MoonsignAscendantEffect(character)
                character.add_effect(ascendant)

    # ================================
    # 非月兆角色增益
    # ================================

    def _on_skill_or_burst(self, event: GameEvent) -> None:
        """处理元素战技/元素爆发事件。"""
        character = event.source

        # 检查是否为非月兆角色
        if self._is_moonsign_character(character):
            return

        # 计算增益值
        bonus = self._calculate_non_moonsign_bonus(character)

        # 覆盖之前的增益
        self.non_moonsign_bonus = bonus
        self.non_moonsign_source = character
        self.non_moonsign_timer = self.non_moonsign_duration

    def _calculate_non_moonsign_bonus(self, character: Any) -> float:
        """
        计算非月兆角色的月曜反应伤害增益。

        根据角色元素类型计算：
        - 火/雷/冰：每100攻击力 → +0.9%
        - 水：每1000生命值 → +0.6%
        - 岩：每100防御力 → +1%
        - 风/草：每100元素精通 → +2.25%

        上限：36%
        """
        element = getattr(character, 'element', '')
        bonus = 0.0

        # 火/雷/冰：基于攻击力
        if element in ('火', '雷', '冰'):
            atk = AttributeCalculator.get_val_by_name(character, '攻击力')
            bonus = (atk / 100) * 0.9

        # 水：基于生命值
        elif element == '水':
            hp = AttributeCalculator.get_val_by_name(character, '生命值')
            bonus = (hp / 1000) * 0.6

        # 岩：基于防御力
        elif element == '岩':
            def_ = AttributeCalculator.get_val_by_name(character, '防御力')
            bonus = (def_ / 100) * 1.0

        # 风/草：基于元素精通
        elif element in ('风', '草'):
            em = AttributeCalculator.get_val_by_name(character, '元素精通')
            bonus = (em / 100) * 2.25

        # 应用上限
        return min(bonus, self.NON_MOONSIGN_BONUS_CAP)

    def _on_before_calculate(self, event: GameEvent) -> None:
        """在伤害计算前注入月曜反应伤害加成。"""
        # 检查增益是否有效
        if self.non_moonsign_timer <= 0:
            return

        dmg_ctx = event.data.get('damage_context')
        if not dmg_ctx:
            return

        # 检查是否为月曜伤害
        dmg = getattr(dmg_ctx, 'damage', None)
        if not dmg:
            return

        is_lunar = dmg.data.get('is_lunar_damage', False)
        if not is_lunar:
            return

        # 注入增益
        if self.non_moonsign_bonus > 0:
            dmg_ctx.add_modifier(
                source="非月兆角色月曜增伤",
                stat="月曜反应伤害%",
                value=self.non_moonsign_bonus,
            )

    # ================================
    # 每帧更新
    # ================================

    def on_frame_update(self, dt: float = 1 / 60) -> None:
        """每帧更新。"""
        # 更新非月兆增益计时器
        if self.non_moonsign_timer > 0:
            self.non_moonsign_timer -= 1

    # ================================
    # 公共查询接口
    # ================================

    def get_moonsign_level(self) -> int:
        """获取当前月兆等级。"""
        return self.moonsign_level

    def get_moonsign_level_name(self) -> str:
        """获取月兆等级名称。"""
        names = {0: "无", 1: "月兆·初辉", 2: "月兆·满辉"}
        return names.get(self.moonsign_level, "无")

    def has_nascent(self, character: Any) -> bool:
        """检查角色是否拥有月兆·初辉效果。"""
        for effect in getattr(character, 'active_effects', []):
            if isinstance(effect, MoonsignNascentEffect):
                return True
        return False

    def has_ascendant(self, character: Any) -> bool:
        """检查角色是否拥有月兆·满辉效果。"""
        for effect in getattr(character, 'active_effects', []):
            if isinstance(effect, MoonsignAscendantEffect):
                return True
        return False

    def get_non_moonsign_bonus(self) -> float:
        """获取当前非月兆角色增益值。"""
        return self.non_moonsign_bonus if self.non_moonsign_timer > 0 else 0.0
