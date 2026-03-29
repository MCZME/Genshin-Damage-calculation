"""伤害系统模块。"""

from __future__ import annotations
from typing import Any, cast, TYPE_CHECKING

from core.systems.base_system import GameSystem
from core.event import GameEvent, EventType
from core.logger import get_emulation_logger
from core.action.attack_tag_resolver import AttackTagResolver

from .context import DamageContext
from .pipeline import DamagePipeline
from .lunar_pipeline import LunarDamagePipeline

if TYPE_CHECKING:
    from core.context import EventEngine
    from core.systems.contract.damage import Damage


class DamageSystem(GameSystem):
    """伤害系统，负责伤害计算的事件分发和流水线调用。"""

    def initialize(self, context: Any):
        super().initialize(context)
        if self.engine:
            self.pipeline = DamagePipeline(self.engine)
            self.lunar_pipeline = LunarDamagePipeline(self.engine)

    def register_events(self, engine: EventEngine):
        engine.subscribe(EventType.BEFORE_DAMAGE, self)

    def handle_event(self, event: GameEvent):
        if event.event_type == EventType.BEFORE_DAMAGE:
            char = event.data["character"]
            dmg = cast('Damage', event.data["damage"])
            target = event.data.get("target")

            ctx = DamageContext(dmg, char, target)

            # 检查是否跳过计算（已预计算的伤害）
            if dmg.data.get("skip_damage_calculation"):
                # 只执行日志和后续事件，跳过计算
                if dmg.target:
                    get_emulation_logger().log_damage(char, dmg.target, dmg)
                    if self.engine:
                        self.engine.publish(
                            GameEvent(
                                event_type=EventType.AFTER_DAMAGE,
                                frame=event.frame,
                                source=char,
                                data={
                                    "character": char,
                                    "target": dmg.target,
                                    "target_id": getattr(dmg.target, "entity_id", None),
                                    "damage": dmg
                                },
                            )
                        )
                return

            # 判断使用哪个流水线
            is_lunar = AttackTagResolver.is_lunar_damage(
                dmg.config.attack_tag,
                dmg.config.extra_attack_tags
            )

            if hasattr(self, "pipeline"):
                if is_lunar:
                    self.lunar_pipeline.run(ctx)
                else:
                    self.pipeline.run(ctx)

            if dmg.target:
                get_emulation_logger().log_damage(char, dmg.target, dmg)
                if self.engine:
                    self.engine.publish(
                        GameEvent(
                            event_type=EventType.AFTER_DAMAGE,
                            frame=event.frame,
                            source=char,
                            data={
                                "character": char,
                                "target": dmg.target,
                                "target_id": getattr(dmg.target, "entity_id", None),
                                "damage": dmg
                            },
                        )
                    )
