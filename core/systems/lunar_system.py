"""
月曜反应系统核心类。

负责月曜反应的触发判定、资源管理（草露、月笼计数）。
"""

from typing import Any

from core.systems.base_system import GameSystem
from core.event import GameEvent, EventType
from core.tool import get_current_time
from core.registry import discover_lunar_trigger_characters


class LunarReactionSystem(GameSystem):
    """
    月曜反应系统。

    职责：
    1. 月曜触发角色配置管理
    2. 草露资源管理（上限、恢复、消耗）
    3. 月笼触发计数与溢出管理
    4. 月曜触发判定方法
    """

    # 默认配置（Registry 无结果时的回退）
    DEFAULT_LUNAR_BLOOM: set[str] = {"奈芙尔", "菈乌玛", "哥伦比娅"}
    DEFAULT_LUNAR_CHARGED: set[str] = {"菲林斯", "伊涅芙", "哥伦比娅"}
    DEFAULT_LUNAR_CRYSTALLIZE: set[str] = {"兹白", "哥伦比娅"}

    def __init__(self) -> None:
        super().__init__()

        # 月曜触发角色配置（从 Registry 自动发现或使用默认值）
        self._init_lunar_trigger_characters()

        # 草露资源
        self.grass_dew: int = 0
        self.grass_dew_max: int = 3
        self.grass_dew_recovery_timer: float = 0.0
        self.grass_dew_recovery_duration: float = 2.5  # 每2.5秒恢复1枚
        self.grass_dew_recovery_active: bool = False
        self.grass_dew_recovery_remaining: float = 0.0  # 剩余恢复时间

        # 月笼触发计数
        self.lunar_cage_counter: int = 0  # 当前计数
        self.lunar_cage_threshold: int = 3  # 触发阈值
        self.lunar_cage_overflow: int = 0  # 溢出计数（最多4层）
        self.lunar_cage_overflow_max: int = 4

        # 月笼谐奏来源角色记录（3次反应中参与的角色）
        self.lunar_cage_source_characters: list[Any] = []

        # 雷暴云附着来源角色记录
        self.thunder_cloud_source_characters: list[Any] = []

    def register_events(self, engine: Any) -> None:
        """订阅事件。"""
        engine.subscribe(EventType.AFTER_LUNAR_BLOOM, self)
        engine.subscribe(EventType.AFTER_LUNAR_CHARGED, self)
        engine.subscribe(EventType.AFTER_LUNAR_CRYSTALLIZE, self)

    def handle_event(self, event: GameEvent) -> None:
        """事件处理。"""
        if event.event_type == EventType.AFTER_LUNAR_BLOOM:
            self._on_lunar_bloom_triggered(event)
        elif event.event_type == EventType.AFTER_LUNAR_CHARGED:
            self._on_lunar_charged_triggered(event)
        elif event.event_type == EventType.AFTER_LUNAR_CRYSTALLIZE:
            self._on_lunar_crystallize_triggered(event)

    # ================================
    # 配置初始化
    # ================================

    def _init_lunar_trigger_characters(self) -> None:
        """从 Registry 自动发现月曜触发角色。"""
        discovered = discover_lunar_trigger_characters()
        self.lunar_bloom_characters = discovered["bloom"] or self.DEFAULT_LUNAR_BLOOM
        self.lunar_charged_characters = discovered["charged"] or self.DEFAULT_LUNAR_CHARGED
        self.lunar_crystallize_characters = discovered["crystallize"] or self.DEFAULT_LUNAR_CRYSTALLIZE

    # ================================
    # 触发判定方法
    # ================================

    def can_trigger_lunar_bloom(self, team_members: list[Any]) -> bool:
        """判定是否可触发月绽放。"""
        return any(
            getattr(m, 'name', None) in self.lunar_bloom_characters
            for m in team_members
        )

    def can_trigger_lunar_charged(self, team_members: list[Any]) -> bool:
        """判定是否可触发月感电。"""
        return any(
            getattr(m, 'name', None) in self.lunar_charged_characters
            for m in team_members
        )

    def can_trigger_lunar_crystallize(self, team_members: list[Any]) -> bool:
        """判定是否可触发月结晶。"""
        return any(
            getattr(m, 'name', None) in self.lunar_crystallize_characters
            for m in team_members
        )

    # ================================
    # 草露资源管理
    # ================================

    def start_grass_dew_recovery(self) -> None:
        """开始草露恢复计时。"""
        self.grass_dew_recovery_active = True
        self.grass_dew_recovery_timer = 0.0

    def stop_grass_dew_recovery(self) -> None:
        """停止草露恢复计时。"""
        self.grass_dew_recovery_active = False

    def refresh_grass_dew_recovery(self) -> None:
        """刷新草露恢复计时（再次触发月绽放时）。"""
        self.grass_dew_recovery_timer = 0.0
        self.grass_dew_recovery_active = True

    def update_grass_dew(self, dt: float) -> None:
        """
        更新草露恢复状态。

        每帧调用，检查是否需要恢复草露。
        """
        if not self.grass_dew_recovery_active:
            return

        if self.grass_dew >= self.grass_dew_max:
            self.grass_dew_recovery_active = False
            return

        self.grass_dew_recovery_timer += dt

        if self.grass_dew_recovery_timer >= self.grass_dew_recovery_duration:
            self.grass_dew_recovery_timer = 0.0
            self.add_grass_dew(1)

    def add_grass_dew(self, amount: int) -> int:
        """
        添加草露。

        Args:
            amount: 添加数量

        Returns:
            实际添加数量
        """
        old = self.grass_dew
        self.grass_dew = min(self.grass_dew + amount, self.grass_dew_max)
        actual = self.grass_dew - old

        if actual > 0 and self.engine:
            self.engine.publish(GameEvent(
                event_type=EventType.GRASS_DEW_GAIN,
                frame=get_current_time(),
                data={"amount": actual, "total": self.grass_dew}
            ))

        return actual

    def consume_grass_dew(self, amount: int) -> bool:
        """
        消耗草露。

        Args:
            amount: 消耗数量

        Returns:
            是否成功消耗
        """
        if self.grass_dew < amount:
            return False

        self.grass_dew -= amount

        if self.engine:
            self.engine.publish(GameEvent(
                event_type=EventType.GRASS_DEW_CONSUME,
                frame=get_current_time(),
                data={"amount": amount, "total": self.grass_dew}
            ))

        return True

    def can_consume_grass_dew(self, amount: int = 1) -> bool:
        """检查是否有足够草露消耗。"""
        return self.grass_dew >= amount

    # ================================
    # 月笼计数管理
    # ================================

    def add_lunar_cage_counter(self, source_character: Any) -> int:
        """
        增加月笼触发计数。

        Args:
            source_character: 触发月结晶的角色

        Returns:
            当前计数（加完后）
        """
        # 记录来源角色
        if source_character not in self.lunar_cage_source_characters:
            self.lunar_cage_source_characters.append(source_character)

        # 如果已达阈值，增加溢出计数
        if self.lunar_cage_counter >= self.lunar_cage_threshold:
            if self.lunar_cage_overflow < self.lunar_cage_overflow_max:
                self.lunar_cage_overflow += 1
            return self.lunar_cage_counter

        self.lunar_cage_counter += 1
        return self.lunar_cage_counter

    def check_and_reset_lunar_cage_counter(self) -> tuple[bool, list[Any]]:
        """
        检查是否达到阈值并重置计数。

        Returns:
            (是否触发谐奏, 参与角色列表)
        """
        if self.lunar_cage_counter >= self.lunar_cage_threshold:
            sources = self.lunar_cage_source_characters.copy()

            # 重置计数
            self.lunar_cage_counter = 0
            self.lunar_cage_source_characters.clear()

            # 消耗溢出计数
            if self.lunar_cage_overflow > 0:
                self.lunar_cage_counter = min(
                    self.lunar_cage_overflow,
                    self.lunar_cage_threshold - 1
                )
                self.lunar_cage_overflow -= self.lunar_cage_counter

            return True, sources

        return False, []

    # ================================
    # 雷暴云来源管理
    # ================================

    def add_thunder_cloud_source(self, character: Any) -> None:
        """添加雷暴云附着来源角色。"""
        if character not in self.thunder_cloud_source_characters:
            self.thunder_cloud_source_characters.append(character)

    def get_thunder_cloud_sources(self) -> list[Any]:
        """获取雷暴云附着来源角色列表。"""
        return self.thunder_cloud_source_characters.copy()

    def clear_thunder_cloud_sources(self) -> None:
        """清空雷暴云附着来源角色列表。"""
        self.thunder_cloud_source_characters.clear()

    # ================================
    # 每帧更新
    # ================================

    def on_frame_update(self, dt: float = 1 / 60) -> None:
        """每帧更新。"""
        self.update_grass_dew(dt)

    # ================================
    # 事件回调
    # ================================

    def _on_lunar_bloom_triggered(self, event: GameEvent) -> None:
        """月绽放触发回调。"""
        # 刷新草露恢复计时
        self.refresh_grass_dew_recovery()

    def _on_lunar_charged_triggered(self, event: GameEvent) -> None:
        """月感电触发回调。"""
        source = event.source
        if source:
            self.add_thunder_cloud_source(source)

    def _on_lunar_crystallize_triggered(self, event: GameEvent) -> None:
        """月结晶触发回调。"""
        source = event.source
        if source:
            self.add_lunar_cage_counter(source)
