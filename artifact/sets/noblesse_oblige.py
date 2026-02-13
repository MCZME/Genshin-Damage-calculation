from core.context import get_context
from typing import Any
from artifact.base_artifact_set import BaseArtifactSet
from core.registry import register_artifact_set
from core.event import EventType
from core.action.damage import DamageType

@register_artifact_set("昔日宗室之仪")
class NoblesseOblige(BaseArtifactSet):
    
    
    def apply_2_set_effect(self, character: Any) -> None:
        get_context().event_engine.subscribe(EventType.BEFORE_DAMAGE_BONUS, self)

    def apply_4_set_effect(self, character: Any) -> None:
        get_context().event_engine.subscribe(EventType.AFTER_BURST, self)

    def handle_event(self, event):
        if event.event_type == EventType.BEFORE_DAMAGE_BONUS:
            if event.data["character"] == self.character and event.data["damage"].damage_type == DamageType.BURST:
                event.data["damage"].panel["伤害加成"] += 20
                event.data["damage"].setDamageData("昔日宗室之仪-伤害加成", 20)
        if event.event_type == EventType.AFTER_BURST:
            if event.data["character"] == self.character:
                for c in Team.team:
                    effect = AttackBoostEffect(self.character, c, "昔日宗室之仪", 20, 12*60)
                    effect.apply()

