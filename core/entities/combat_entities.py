from typing import Any
from core.entities.base_entity import BaseEntity
from core.event import EventHandler, EventType, GameEvent
from core.logger import get_emulation_logger

class ShatteredIceObject(BaseEntity, EventHandler):
    """粉碎之冰效果 (冰共鸣)。"""
    def __init__(self, **kwargs: Any):
        super().__init__("粉碎之冰", float("inf"), **kwargs)

    def apply(self) -> None:
        super().apply()
        get_emulation_logger().log_object("❄️ 创建粉碎之冰")
        if self.event_engine:
            self.event_engine.subscribe(EventType.BEFORE_CRITICAL, self)

    def on_finish(self, target: Any) -> None:
        if self.event_engine:
            self.event_engine.unsubscribe(EventType.BEFORE_CRITICAL, self)

    def handle_event(self, event: GameEvent) -> None:
        damage = event.data["damage"]
        target = damage.target
        # 检查目标是否有冰/冻附着
        if hasattr(target, "aura") and target.aura.has_elements(["冰", "冻"]):
            # 统一使用新的属性加成逻辑
            damage.panel["暴击率"] += 15
            damage.setDamageData("粉碎之冰", 15)

class ShieldObject(BaseEntity):
    """护盾实体。"""
    def __init__(self, character: Any, name: str, element_type: str, 
                 shield_value: float, duration: float, **kwargs: Any):
        super().__init__(name, duration, **kwargs)
        self.character = character
        self.element_type = element_type
        self.shield_value = shield_value
        self.max_shield_value = shield_value
        
    def apply(self) -> None:
        super().apply()
        get_emulation_logger().log_effect(f"{self.character.name} 获得 {self.name} 护盾")
