from typing import Any
from artifact.base_artifact_set import BaseArtifactSet
from core.registry import register_artifact_set
from core.event import EventType, GameEvent
from core.action.damage import DamageType

@register_artifact_set("角斗士的终幕礼")
class GladiatorFinale(BaseArtifactSet):
    """角斗士的终幕礼"""
    def apply_2_set_effect(self, character: Any) -> None:
        """两件套：攻击力提高18%。"""
        character.attribute_panel["攻击力%"] = character.attribute_panel.get("攻击力%", 0.0) + 18

    def apply_4_set_effect(self, character: Any) -> None:
        """四件套：普通攻击造成的伤害提高35%。"""
        self.character = character
        self.character.event_engine.subscribe(EventType.BEFORE_DAMAGE_BONUS, self)
    
    def handle_event(self, event: GameEvent) -> None:
        if event.event_type == EventType.BEFORE_DAMAGE_BONUS:
            damage = event.data["damage"]
            # 严格使用 damage_type 和 character.type
            if damage.damage_type == DamageType.NORMAL and getattr(self.character, "type", "") in ["单手剑", "双手剑", "长柄武器"]:
                damage.panel["伤害加成"] += 35
                damage.setDamageData("角斗士的终幕礼", 35)
