from typing import Any
from artifact.base_artifact_set import BaseArtifactSet
from core.registry import register_artifact_set
from core.event import EventBus, EventType, EventHandler, GameEvent
from core.action.damage import DamageType
import core.tool as T

@register_artifact_set("黄金剧团")
class GoldenTroupe(BaseArtifactSet):
    """黄金剧团"""
    def __init__(self):
        super().__init__("黄金剧团")

    def apply_2_set_effect(self, character: Any) -> None:
    
    def apply_4_set_effect(self, character: Any) -> None:

    def handle_event(self, event: GameEvent) -> None:
        if event.event_type == EventType.BEFORE_DAMAGE_BONUS:
            if event.data["character"] == self.character:
                damage = event.data["damage"]
                d_type = getattr(damage, "damage_type", getattr(damage, "damageType", None))
                if d_type == DamageType.SKILL:
                    # 两件套 20%
                    damage.panel["伤害加成"] += 20
                    damage.setDamageData("黄金剧团-两件套", 20)
                    if self.four_set:
                        # 四件套基础 25%
                        damage.panel["伤害加成"] += 25
                        damage.setDamageData("黄金剧团-四件套", 25)
                        # 处于后台或登场不到 2 秒再加 25%
                        if not self.character.on_field or (event.frame - self.last_on_field_time < 2*60):
                            damage.panel["伤害加成"] += 25
                            damage.setDamageData("黄金剧团-后台", 25)

        elif event.event_type == EventType.AFTER_CHARACTER_SWITCH:
            if event.data["new_character"] == self.character:
                self.last_on_field_time = event.frame
