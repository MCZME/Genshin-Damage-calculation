from core.context import get_context
from typing import Any
from artifact.base_artifact_set import BaseArtifactSet
from core.registry import register_artifact_set
from core.event import EventType, GameEvent
from core.action.damage import DamageType

@register_artifact_set("深廊终曲")
class FinaleOftheDeepGalleries(BaseArtifactSet):
    

    def apply_2_set_effect(self, character: Any) -> None:
        pass

    def apply_4_set_effect(self, character: Any) -> None:
        get_context().event_engine.subscribe(EventType.BEFORE_DAMAGE_BONUS, self)

    def handle_event(self, event:GameEvent):
        if event.data["character"] is not self.character:
            return
        
        damage = event.data["damage"]
        if damage.damage_type == DamageType.NORMAL and event.frame - self.last_normal_damage_time >= 6 *60:
            self.last_burst_damage_time = event.frame
            damage.panel["伤害加成"] += 60
            damage.setDamageData("深廊终曲-四件套伤害加成", 60)
        elif damage.damage_type == DamageType.BURST and event.frame - self.last_burst_damage_time >= 6 *60:
            self.last_normal_damage_time = event.frame
            damage.panel["伤害加成"] += 60
            damage.setDamageData("深廊终曲-四件套伤害加成", 60)

__all__ = [
    "FinaleOftheDeepGalleries",
    "ArtifactEffect",
    "GladiatorFinale",
    "ObsidianCodex",
    "ScrolloftheHeroOfCinderCity",
    "EmblemOfSeveredFate",
    "SongOfDaysPast",
    "Instructor",
    "NoblesseOblige",
    "MarechausseeHunter",
    "GoldenTroupe",
    "ViridescentVenerer",
    "DeepwoodMemories",
    "FlowerOfParadiseLost",
    "LongNightsOath"
]

