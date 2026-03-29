"""
月曜反应系统核心类。

负责月曜反应的触发判定、资源管理（草露、月笼计数）。
"""

from typing import Any

from core.systems.base_system import GameSystem
from core.event import GameEvent, EventType
from core.tool import get_current_time
from core.effect.common import MoonsignTalent


class LunarReactionSystem(GameSystem):
    """
    月曜反应系统。

    职责：
    1. 月曜触发判定（运行时从月兆天赋检测）
    2. 草露资源管理（上限、恢复、消耗）
    3. 月笼触发计数与溢出管理
    """

    def __init__(self) -> None:
        super().__init__()

        # 草露资源
        self.grass_dew: float = 0.0  # 浮点类型，支持持续恢复
        self.grass_dew_max: int = 3
        self.grass_dew_recovery_rate: float = 1.0 / 2.5  # 恢复速率：0.4枚/秒
        self.grass_dew_recovery_timer: float = 0.0  # 恢复状态剩余时间
        self.grass_dew_recovery_active: bool = False

        # 山月草露（独立资源，整数类型）
        self.mountain_grass_dew: int = 0
        self.mountain_grass_dew_max: int = 3
        self.mountain_grass_dew_window_start: int | None = None  # 窗口起始帧
        self.mountain_grass_dew_window_duration: int = 1080  # 18秒

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
    # 触发判定方法（运行时检测）
    # ================================

    def can_trigger_lunar_bloom(self, team_members: list[Any]) -> bool:
        """检查队伍中是否有角色可触发月绽放。"""
        return any(self._has_lunar_trigger(m, "bloom") for m in team_members)

    def can_trigger_lunar_charged(self, team_members: list[Any]) -> bool:
        """检查队伍中是否有角色可触发月感电。"""
        return any(self._has_lunar_trigger(m, "charged") for m in team_members)

    def can_trigger_lunar_crystallize(self, team_members: list[Any]) -> bool:
        """检查队伍中是否有角色可触发月结晶。"""
        return any(self._has_lunar_trigger(m, "crystallize") for m in team_members)

    def _has_lunar_trigger(self, character: Any, trigger_type: str) -> bool:
        """
        检查角色的月兆天赋是否包含指定触发类型。

        Args:
            character: 角色对象
            trigger_type: 触发类型 ("bloom"/"charged"/"crystallize")

        Returns:
            是否具备该触发能力
        """
        talents = getattr(character, 'talents', [])
        for talent in talents:
            if isinstance(talent, MoonsignTalent):
                return trigger_type in talent.get_lunar_triggers()
        return False

    # ================================
    # 草露资源管理
    # ================================

    def start_grass_dew_recovery(self) -> None:
        """开始草露恢复状态（持续2.5秒）。"""
        self.grass_dew_recovery_active = True
        self.grass_dew_recovery_timer = 2.5  # 2.5秒恢复期

    def stop_grass_dew_recovery(self) -> None:
        """停止草露恢复。"""
        self.grass_dew_recovery_active = False
        self.grass_dew_recovery_timer = 0.0

    def refresh_grass_dew_recovery(self) -> None:
        """刷新草露恢复持续时间（再次触发月绽放时）。"""
        self.grass_dew_recovery_timer = 2.5  # 重置为2.5秒
        self.grass_dew_recovery_active = True

    def update_grass_dew(self, dt: float) -> None:
        """
        更新草露恢复状态。

        在恢复状态激活期间，按速率持续累积草露。
        每2.5秒可恢复1枚草露（速率为0.4枚/秒）。
        """
        if not self.grass_dew_recovery_active:
            return

        # 减少剩余恢复时间
        self.grass_dew_recovery_timer -= dt

        # 持续累积草露
        if self.grass_dew < self.grass_dew_max:
            self.grass_dew = min(
                self.grass_dew + self.grass_dew_recovery_rate * dt,
                float(self.grass_dew_max)
            )

        # 恢复时间结束或达到上限，停止恢复
        if self.grass_dew_recovery_timer <= 0 or self.grass_dew >= self.grass_dew_max:
            self.grass_dew_recovery_active = False

    def add_grass_dew(self, amount: float) -> float:
        """
        添加草露。

        Args:
            amount: 添加数量（支持浮点）

        Returns:
            实际添加数量
        """
        old = self.grass_dew
        self.grass_dew = min(self.grass_dew + amount, float(self.grass_dew_max))
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
        消耗草露（优先普通草露，不足时消耗山月草露）。

        Args:
            amount: 消耗数量（整数枚）

        Returns:
            是否成功消耗
        """
        # 优先消耗普通草露
        if self.grass_dew >= float(amount):
            self.grass_dew -= float(amount)

            if self.engine:
                self.engine.publish(GameEvent(
                    event_type=EventType.GRASS_DEW_CONSUME,
                    frame=get_current_time(),
                    data={"amount": amount, "total": self.grass_dew}
                ))

            return True

        # 普通草露不足，计算剩余需求
        remaining = amount - int(self.grass_dew)

        # 尝试消耗山月草露
        if self.mountain_grass_dew >= remaining:
            consumed_from_grass_dew = int(self.grass_dew)
            self.grass_dew = 0.0
            self.mountain_grass_dew -= remaining

            if self.engine:
                self.engine.publish(GameEvent(
                    event_type=EventType.GRASS_DEW_CONSUME,
                    frame=get_current_time(),
                    data={
                        "amount": amount,
                        "total": self.grass_dew,
                        "from_mountain_dew": remaining,
                        "mountain_dew_remaining": self.mountain_grass_dew,
                    }
                ))

            return True

        return False

    def can_consume_grass_dew(self, amount: int = 1) -> bool:
        """检查是否有足够草露消耗（需要满1枚才能消耗）。"""
        return self.grass_dew >= float(amount)

    # ================================
    # 山月草露资源管理
    # ================================

    def add_mountain_grass_dew(self) -> bool:
        """
        尝试提供一枚山月草露。

        山月草露是由天赋二「新月自己的法则」提供的特殊草露资源，
        与普通草露分开计算。18秒窗口内至多提供3枚。

        Returns:
            是否成功提供
        """
        current = get_current_time()

        # 初始化或重置窗口
        if self.mountain_grass_dew_window_start is None:
            self.mountain_grass_dew_window_start = current
        elif current - self.mountain_grass_dew_window_start >= self.mountain_grass_dew_window_duration:
            self.mountain_grass_dew_window_start = current
            self.mountain_grass_dew = 0

        # 窗口内提供
        if self.mountain_grass_dew < self.mountain_grass_dew_max:
            self.mountain_grass_dew += 1
            return True

        return False

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
