from typing import Any
from artifact.base_artifact_set import BaseArtifactSet
from core.registry import register_artifact_set
from core.event import EventBus, EventType
from core.effect.artifact.cinder_city import CinderCityEffect

@register_artifact_set("烬城勇者绘卷")
class ScrolloftheHeroOfCinderCity(BaseArtifactSet):
    

    def apply_2_set_effect(self, character: Any) -> None:
        EventBus.subscribe(EventType.NightsoulBurst, self)

    def apply_4_set_effect(self, character: Any) -> None:
        EventBus.subscribe(EventType.AFTER_ELEMENTAL_REACTION, self)

    def handle_event(self, event):
        if event.event_type == EventType.NightsoulBurst:
            summon_energy(1, self.character, ("无", 6),True,True,0)
        elif event.event_type == EventType.AFTER_ELEMENTAL_REACTION:
            reaction = event.data["elementalReaction"]
            if reaction.source == self.character:
                for character in Team.team:
                    effect = CinderCityEffect(self.character,character,[reaction.target_element, reaction.damage.element[0]])
                    effect.apply([reaction.target_element, reaction.damage.element[0]])
