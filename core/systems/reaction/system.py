"""反应系统模块。"""

from typing import Any

from core.systems.contract.reaction import ReactionCategory
from core.context import EventEngine
from core.event import EventType, GameEvent
from core.logger import get_emulation_logger
from core.systems.base_system import GameSystem

from .icd import ICDManager
from .converter import LunarConverter
from .handlers.transformative import TransformativeHandler
from .handlers.status import StatusHandler
from .handlers.lunar import LunarHandler


class ReactionSystem(GameSystem):
    """
    元素反应逻辑分发系统。

    负责将 AuraManager 产出的原始反应结果 (ReactionResult) 转化为实际的游戏效果，
    包括生成剧变反应伤害、应用减抗效果等。
    同时处理月曜反应的触发判定与效果分发。
    """

    def __init__(self) -> None:
        super().__init__()

        # 初始化处理器
        self._icd_manager = ICDManager()
        self._converter = LunarConverter()
        self._transformative_handler = TransformativeHandler(self._icd_manager)
        self._status_handler = StatusHandler()
        self._lunar_handler = LunarHandler()

    def register_events(self, engine: EventEngine) -> None:
        """订阅反应事件。"""
        engine.subscribe(EventType.AFTER_ELEMENTAL_REACTION, self)
        engine.subscribe(EventType.ELECTRO_CHARGED_TICK, self)
        engine.subscribe(EventType.BURNING_TICK, self)
        # 月曜事件
        engine.subscribe(EventType.LUNAR_CHARGED_TICK, self)
        engine.subscribe(EventType.LUNAR_CRYSTALLIZE_ATTACK, self)

    def handle_event(self, event: GameEvent) -> None:
        """事件分发。"""
        # 更新处理器上下文
        self._update_handlers()

        if event.event_type == EventType.AFTER_ELEMENTAL_REACTION:
            res = event.data.get("elemental_reaction")
            if res:
                # 尝试转换为月曜反应
                res = self._converter.try_convert(self.context, event.source, res)
                self._apply_reaction_effect(event, res)
        elif event.event_type == EventType.ELECTRO_CHARGED_TICK:
            self._transformative_handler.handle_ec_tick(event)
        elif event.event_type == EventType.BURNING_TICK:
            self._transformative_handler.handle_burning_tick(event)
        elif event.event_type == EventType.LUNAR_CHARGED_TICK:
            self._lunar_handler.handle_lunar_charged_tick(event)
        elif event.event_type == EventType.LUNAR_CRYSTALLIZE_ATTACK:
            self._lunar_handler.handle_lunar_crystallize_attack(event)

    def _update_handlers(self) -> None:
        """更新处理器的上下文和引擎引用。"""
        if self.context:
            self._transformative_handler.set_context(self.context)
            self._status_handler.set_context(self.context)
            self._lunar_handler.set_context(self.context)
        if self.engine:
            self._transformative_handler.set_engine(self.engine)
            self._lunar_handler.set_engine(self.engine)

    def _apply_reaction_effect(self, event: GameEvent, res: Any) -> None:
        """根据反应类别分发逻辑。"""
        source_char = event.source
        target = event.data.get("target")

        # 跳过冷却中的普通结晶反应
        # 注意：月结晶已转换为 LUNAR 类别，不会进入此分支
        if res.is_cooldown_skipped:
            get_emulation_logger().log_info(
                f"结晶反应冷却中，跳过: {res.target_element.value}结晶"
            )
            return

        get_emulation_logger().log_reaction(
            source_char=source_char,
            reaction_type=res.reaction_type.value,
            target=target,
        )

        # 月曜反应分支
        if res.category == ReactionCategory.LUNAR:
            self._apply_lunar_reaction_effect(event, res)
            return

        # 1. 物理化副作用 (生成实体)
        from core.systems.contract.reaction import ElementalReactionType
        if res.reaction_type == ElementalReactionType.CRYSTALLIZE:
            self._status_handler.handle_crystallize(event, res)
        elif res.reaction_type == ElementalReactionType.BLOOM:
            self._status_handler.handle_bloom(event, res)

        # 2. 状态/Debuff 副作用
        if res.reaction_type == ElementalReactionType.SUPERCONDUCT:
            self._status_handler.handle_superconduct(event, res)
        elif res.reaction_type == ElementalReactionType.SWIRL:
            self._status_handler.handle_swirl(event, res)
        elif res.reaction_type == ElementalReactionType.FREEZE:
            self._status_handler.handle_freeze(event, res)

        # 3. 剧变伤害产生
        if res.category == ReactionCategory.TRANSFORMATIVE:
            self._transformative_handler.handle_transformative(event, res)

    def _apply_lunar_reaction_effect(self, event: GameEvent, res: Any) -> None:
        """月曜反应效果分发。"""
        from core.systems.contract.reaction import ElementalReactionType
        if res.reaction_type == ElementalReactionType.LUNAR_BLOOM:
            self._lunar_handler.handle_lunar_bloom(event, res)
        elif res.reaction_type == ElementalReactionType.LUNAR_CHARGED:
            self._lunar_handler.handle_lunar_charged(event, res)
        elif res.reaction_type == ElementalReactionType.LUNAR_CRYSTALLIZE:
            self._lunar_handler.handle_lunar_crystallize(event, res)
