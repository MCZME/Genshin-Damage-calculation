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

@register_artifact_set("教官")
class Instructor(BaseArtifactSet):
    

    def apply_2_set_effect(self, character: Any) -> None:
        attributrPanel = character.attribute_panel
        attributrPanel["元素精通"] += 80
    
    def apply_4_set_effect(self, character: Any) -> None:
        EventBus.subscribe(EventType.AFTER_ELEMENTAL_REACTION, self)

    def handle_event(self, event):
        if event.event_type == EventType.AFTER_ELEMENTAL_REACTION:
            if event.data["elementalReaction"].source == self.character:
                for c in Team.team:
                    effect = ElementalMasteryBoostEffect(self.character, c, "教官", 120, 8*60)
                    effect.apply()
