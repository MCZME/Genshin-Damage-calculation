from typing import Any
from artifact.base_artifact_set import BaseArtifactSet
from core.registry import register_artifact_set
from core.event import EventType, GameEvent
from core.action.attack_tag_resolver import AttackTagResolver, AttackCategory

@register_artifact_set("黄金剧团")
class GoldenTroupeSet(BaseArtifactSet):
    """
    黄金剧团套装效果实现。
    2件套：元素战技造成的伤害提升20%。
    4件套：元素战技造成的伤害提升25%；此外，处于队伍后台时，元素战技造成的伤害进一步提升25%。
    """
    def __init__(self):
        super().__init__("黄金剧团")
        self.char = None

    def apply_2_set_effect(self, character: Any) -> None:
        # 直接注入静态加成 (审计化)
        character.add_modifier(source=self.name + " (2件套)", stat="元素战技伤害加成", value=20.0)

    def apply_4_set_effect(self, character: Any) -> None:
        self.char = character
        # 1. 注入基础 4件套加成
        character.add_modifier(source=self.name + " (4件套)", stat="元素战技伤害加成", value=25.0)
        
        # 2. 订阅计算事件，动态处理后台额外加成
        character.event_engine.subscribe(EventType.BEFORE_CALCULATE, self)

    def handle_event(self, event: GameEvent) -> None:
        """处理 4 件套的动态增伤判定。"""
        if event.event_type == EventType.BEFORE_CALCULATE:
            self._apply_off_field_bonus(event)

    def _apply_off_field_bonus(self, event: GameEvent) -> None:
        """
        判断角色是否处于后台，若是元素战技伤害则注入额外 25% 加成。
        """
        if not self.char or self.char.on_field:
            return
            
        dmg_ctx = event.data.get("damage_context")
        if not dmg_ctx:
            return
            
        # 判定是否为元素战技类伤害
        categories = AttackTagResolver.resolve_categories(
            dmg_ctx.config.attack_tag, dmg_ctx.config.extra_attack_tags
        )
        
        if AttackCategory.SKILL in categories:
            # 动态注入后台额外增伤
            dmg_ctx.add_modifier(source=self.name + " (4件套后台加成)", stat="伤害加成", value=25.0)
