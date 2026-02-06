from typing import Any
from artifact.base_artifact_set import BaseArtifactSet
from core.registry import register_artifact_set
from core.event import EventBus, EventType
from core.effect.artifact.songs_of_days_past import ThirstEffect

@register_artifact_set("昔时之歌")
class SongOfDaysPast(BaseArtifactSet):
    

    def apply_2_set_effect(self, character: Any) -> None:
        # 治疗加成提高15%
        character.attribute_panel["治疗加成"] += 15

    def apply_4_set_effect(self, character: Any) -> None:
        EventBus.subscribe(EventType.AFTER_HEAL, self)
    
    def handle_event(self, event):
        if event.event_type == EventType.AFTER_HEAL and event.data["character"] == self.character:
            # 查找或创建渴盼效果
            thirst = next((e for e in self.character.active_effects 
                          if isinstance(e, ThirstEffect)), None)
            if not thirst:
                thirst = ThirstEffect(self.character)
                thirst.apply()
            # 记录治疗量
            thirst.add_heal(event.data["healing"].final_value)
