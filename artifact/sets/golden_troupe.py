from typing import Any
from artifact.base_artifact_set import BaseArtifactSet
from core.registry import register_artifact_set
from core.event import EventType, EventHandler, GameEvent
from core.systems.contract.damage import DamageType
import core.tool as T

@register_artifact_set("黄金剧团")
class GoldenTroupe(BaseArtifactSet):
    """黄金剧团"""
    def __init__(self):
        super().__init__("黄金剧团")
        self.character = None
        self.four_set = False
        self.last_on_field_time = -9999

    def apply_2_set_effect(self, character: Any) -> None:
        pass

    def apply_4_set_effect(self, character: Any) -> None:
        self.character = character
        self.four_set = True
        self.character.event_engine.subscribe(EventType.BEFORE_DAMAGE_BONUS, self)
        self.character.event_engine.subscribe(EventType.AFTER_CHARACTER_SWITCH, self)

    def handle_event(self, event: GameEvent) -> None:
        if event.event_type == EventType.BEFORE_DAMAGE_BONUS:
            if event.data["character"] == self.character:
                damage = event.data["damage"]
                
                if damage.damage_type == DamageType.SKILL:
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
