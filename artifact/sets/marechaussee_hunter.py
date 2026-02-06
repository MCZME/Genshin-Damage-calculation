from typing import Any
from artifact.base_artifact_set import BaseArtifactSet
from core.registry import register_artifact_set
from core.event import EventBus, EventType
from core.action.damage import DamageType
from core.effect.artifact.marechaussee_hunter import MarechausseeHunterEffect

@register_artifact_set("逐影猎人")
class MarechausseeHunter(BaseArtifactSet):
    

    def apply_2_set_effect(self, character: Any) -> None:
        EventBus.subscribe(EventType.BEFORE_DAMAGE_BONUS, self)

    def apply_4_set_effect(self, character: Any) -> None:
        EventBus.subscribe(EventType.AFTER_HEALTH_CHANGE, self)

    def handle_event(self, event):
        if event.event_type == EventType.BEFORE_DAMAGE_BONUS:
            if event.data["character"] == self.character and event.data["damage"].damage_type in [DamageType.NORMAL, DamageType.CHARGED]:
                event.data["damage"].panel["伤害加成"] += 15
                event.data["damage"].setDamageData("逐影猎人-伤害加成", 15)
        if event.event_type == EventType.AFTER_HEALTH_CHANGE:
            if event.data["character"] == self.character:
                MarechausseeHunterEffect(self.character).apply()
