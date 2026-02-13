from core.context import get_context
from typing import Any
from artifact.base_artifact_set import BaseArtifactSet
from core.registry import register_artifact_set
from core.event import EventType
import core.tool as T

@register_artifact_set("黑曜秘典")
class ObsidianCodex(BaseArtifactSet):
    

    def apply_2_set_effect(self, character: Any) -> None:
        # 装备者处于夜魂加持状态，并且在场上时，造成的伤害提高15%。
        get_context().event_engine.subscribe(EventType.AFTER_NIGHTSOUL_BLESSING, self)
        get_context().event_engine.subscribe(EventType.BEFORE_NIGHTSOUL_BLESSING, self)

    def apply_4_set_effect(self, character: Any) -> None:
        get_context().event_engine.subscribe(EventType.AFTER_NIGHT_SOUL_CHANGE, self)

    def handle_event(self, event):
        if event.event_type == EventType.BEFORE_NIGHTSOUL_BLESSING:
            attribute_data = event.data["character"].attribute_data
            attribute_data["伤害加成"] += 15
        elif event.event_type == EventType.AFTER_NIGHTSOUL_BLESSING:
            attribute_data = event.data["character"].attribute_data
            attribute_data["伤害加成"] -= 15
        elif event.event_type == EventType.AFTER_NIGHT_SOUL_CHANGE:
            # 检查是否是当前角色且夜魂值减少
            if (event.data["character"] == self.character and 
                event.data["amount"] < 0 and
                T.get_current_time() - self.last_trigger_time >= 60 and
                event.cancelled == False):  # 1秒冷却
                
                # 使用CritRateBoostEffect应用暴击率提升效果
                effect = CritRateBoostEffect(self.character, "黑曜秘典", 40, 6 * 60)
                effect.apply()
                self.last_trigger_time = T.get_current_time()

