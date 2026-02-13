from core.context import get_context
from typing import Any
from artifact.base_artifact_set import BaseArtifactSet
from core.registry import register_artifact_set
from core.event import EventType
from core.action.damage import DamageType
from core.effect.artifact.nighttime_whispers import LuminescenceEffect

@register_artifact_set("长夜之誓")
class LongNightsOath(BaseArtifactSet):
    

    def apply_2_set_effect(self, character: Any) -> None:
        # 下落攻击伤害提升25%
        get_context().event_engine.subscribe(EventType.BEFORE_DAMAGE_BONUS, self)

    def apply_4_set_effect(self, character: Any) -> None:
        get_context().event_engine.subscribe(EventType.AFTER_DAMAGE, self)

    def handle_event(self, event):
        if event.event_type == EventType.BEFORE_DAMAGE_BONUS and event.data["character"] == self.character:
            if event.data["damage"].damage_type == DamageType.PLUNGING:
                event.data["damage"].panel["伤害加成"] += 25
                event.data["damage"].setDamageData("长夜之誓-两件套伤害加成", 25)
        
        elif event.event_type == EventType.AFTER_DAMAGE:
            if event.data["character"] == self.character:
                damage_type = event.data["damage"].damage_type
                if damage_type in [DamageType.PLUNGING, DamageType.CHARGED, DamageType.SKILL]:
                    current_time = event.frame
                    if current_time - self.last_tigger_time >= 60:
                        # 根据攻击类型获得不同层数
                        if damage_type == DamageType.PLUNGING:
                            effect = LuminescenceEffect(self.character, damage_type, 1)
                            effect.apply()
                        else: # CHARGED or SKILL
                            effect = LuminescenceEffect(self.character, damage_type, 2)
                            effect.apply()

