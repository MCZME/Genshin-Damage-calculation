from typing import Any
from artifact.base_artifact_set import BaseArtifactSet
from core.registry import register_artifact_set
from core.event import EventBus, EventType, EventHandler, GameEvent
from core.action.damage import DamageType
import core.tool as T
from core.effect.artifact.cinder_city import CinderCityEffect
from core.effect.artifact.flower_of_paradise_lost import FlowerOfParadiseLostEffect
from core.effect.artifact.marechaussee_hunter import MarechausseeHunterEffect
from core.effect.artifact.songs_of_days_past import ThirstEffect
from core.effect.artifact.nighttime_whispers import LuminescenceEffect

@register_artifact_set("翠绿之影")
class ViridescentVenerer(BaseArtifactSet):
    

    def apply_2_set_effect(self, character: Any) -> None:
        pass

    def apply_4_set_effect(self, character: Any) -> None:
        EventBus.subscribe(EventType.BEFORE_SWIRL, self)

    def handle_event(self, event):
        if (event.event_type == EventType.BEFORE_SWIRL and 
            event.data["elementalReaction"].source == self.character and
            self.character.on_field):
            element = event.data["elementalReaction"].target_element
            effect = ResistanceDebuffEffect(self.name+f"-{element}", self.character, event.data["elementalReaction"].target, 
                                            element, 40, 10*60)
            effect.apply()
