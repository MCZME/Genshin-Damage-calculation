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

@register_artifact_set("深廊终曲")
class FinaleOftheDeepGalleries(BaseArtifactSet):
    

    def apply_2_set_effect(self, character: Any) -> None:

    def apply_4_set_effect(self, character: Any) -> None:
        EventBus.subscribe(EventType.BEFORE_DAMAGE_BONUS, self)

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
