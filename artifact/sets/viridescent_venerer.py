from core.context import get_context
from typing import Any
from artifact.base_artifact_set import BaseArtifactSet
from core.registry import register_artifact_set
from core.event import EventType

@register_artifact_set("翠绿之影")
class ViridescentVenerer(BaseArtifactSet):
    

    def apply_2_set_effect(self, character: Any) -> None:
        pass

    def apply_4_set_effect(self, character: Any) -> None:
        get_context().event_engine.subscribe(EventType.BEFORE_SWIRL, self)

    def handle_event(self, event):
        if (event.event_type == EventType.BEFORE_SWIRL and 
            event.data["elementalReaction"].source == self.character and
            self.character.on_field):
            element = event.data["elementalReaction"].target_element
            effect = ResistanceDebuffEffect(self.name+f"-{element}", self.character, event.data["elementalReaction"].target, 
                                            element, 40, 10*60)
            effect.apply()

