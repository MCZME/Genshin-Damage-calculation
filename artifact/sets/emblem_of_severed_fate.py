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

@register_artifact_set("绝缘之旗印")
class EmblemOfSeveredFate(BaseArtifactSet):
    

    def apply_2_set_effect(self, character: Any) -> None:
        # 元素充能效率提高20%
        character.attribute_panel["元素充能效率"] += 20

    def apply_4_set_effect(self, character: Any) -> None:
        EventBus.subscribe(EventType.BEFORE_DAMAGE_BONUS, self)
    
    def handle_event(self, event):
        if event.event_type == EventType.BEFORE_DAMAGE_BONUS:
            if event.data["damage"].damage_type == DamageType.BURST and event.data["damage"].source == self.character:
                # 基于元素充能效率的25%提升伤害，最多75%
                er = self.character.attribute_panel["元素充能效率"]
                bonus = min(er * 0.25, 75)
                event.data["damage"].panel["伤害加成"] += bonus
                event.data["damage"].data["绝缘之旗印_伤害加成"] = bonus
