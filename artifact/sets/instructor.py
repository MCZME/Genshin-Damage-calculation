from core.context import get_context
from typing import Any
from artifact.base_artifact_set import BaseArtifactSet
from core.registry import register_artifact_set
from core.event import EventType

@register_artifact_set("教官")
class Instructor(BaseArtifactSet):
    

    def apply_2_set_effect(self, character: Any) -> None:
        attributrPanel = character.attribute_data
        attributrPanel["元素精通"] += 80
    
    def apply_4_set_effect(self, character: Any) -> None:
        get_context().event_engine.subscribe(EventType.AFTER_ELEMENTAL_REACTION, self)

    def handle_event(self, event):
        if event.event_type == EventType.AFTER_ELEMENTAL_REACTION:
            if event.data["elementalReaction"].source == self.character:
                for c in Team.team:
                    effect = ElementalMasteryBoostEffect(self.character, c, "教官", 120, 8*60)
                    effect.apply()

