from typing import Any
from artifact.base_artifact_set import BaseArtifactSet
from core.registry import register_artifact_set
from core.event import EventBus, EventType, EventHandler, GameEvent
from core.action.damage import DamageType
import core.tool as T

@register_artifact_set("角斗士的终幕礼")
class GladiatorFinale(BaseArtifactSet):
    """角斗士的终幕礼"""
    def apply_2_set_effect(self, character: Any) -> None:
        # 攻击力提升18%
        attr_panel = getattr(character, "attribute_panel", getattr(character, "attributePanel", {}))
        attr_panel["攻击力%"] = attr_panel.get("攻击力%", 0.0) + 18

    def apply_4_set_effect(self, character: Any) -> None:
        self.character = character
        self.character.event_engine.subscribe(EventType.BEFORE_DAMAGE_BONUS, self)
    
    def handle_event(self, event: GameEvent) -> None:
        if event.event_type == EventType.BEFORE_DAMAGE_BONUS:
            damage = event.data["damage"]
            d_type = getattr(damage, "damage_type", getattr(damage, "damageType", None))
            # 注意：这里 getattr(event.source, "type", "") 只是模拟，实际应根据 Character 实现
            if d_type == DamageType.NORMAL and getattr(event.source, "type", "") in ["单手剑", "双手剑", "长柄武器"]:
                damage.panel["伤害加成"] += 35
                damage.setDamageData("角斗士的终幕礼", 35)