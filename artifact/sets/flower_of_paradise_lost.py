from core.context import get_context
from typing import Any
from artifact.base_artifact_set import BaseArtifactSet
from core.registry import register_artifact_set
from core.event import EventType
import core.tool as T
from core.effect.artifact.flower_of_paradise_lost import FlowerOfParadiseLostEffect

@register_artifact_set("乐园遗落之花")
class FlowerOfParadiseLost(BaseArtifactSet):
    

    def apply_2_set_effect(self, character: Any) -> None:
        pass

    def apply_4_set_effect(self, character: Any) -> None:
        get_context().event_engine.subscribe(EventType.AFTER_BLOOM, self)
        get_context().event_engine.subscribe(EventType.AFTER_HYPERBLOOM, self)
        get_context().event_engine.subscribe(EventType.AFTER_BURGEON, self)

    def handle_event(self, event):
        if event.event_type in [EventType.AFTER_BLOOM, EventType.AFTER_HYPERBLOOM, EventType.AFTER_BURGEON]:
            e = event.data["elementalReaction"]
            if e.source == self.character and T.get_current_time() - self.last_tigger_time > self.inveral:
                self.last_tigger_time = T.get_current_time()
                FlowerOfParadiseLostEffect(self.character).apply()

