from core.base_entity import BaseEntity
from core.event import EventBus, EventHandler, EventType
from core.logger import get_emulation_logger

class ShatteredIceObject(BaseObject, EventHandler):
    """粉碎之冰效果"""
    def __init__(self):
        super().__init__("粉碎之冰", float('inf'))

    def apply(self):
        super().apply()
        get_emulation_logger().log_object(f'❄ 创建粉碎之冰')
        EventBus.subscribe(EventType.BEFORE_CRITICAL, self)

    def on_finish(self, target):
        super().on_finish(target)
        EventBus.unsubscribe(EventType.BEFORE_CRITICAL, self)

    def on_frame_update(self, target):
        ...

    def handle_event(self, event):
        target = event.data['damage'].target
        ice = next((a for a in target.aura.elementalAura if a['element'] in ['冰', '冻']), None)

        if ice:
            event.data['damage'].panel['暴击率'] += 15
            event.data['damage'].setDamageData('粉碎之冰', 15)

class ShieldObject(BaseEntity):
    """护盾效果基类"""
    def __init__(self, character, name, element_type, shield_value, duration):
        super().__init__(name, duration)
        self.character = character
        self.element_type = element_type
        self.shield_value = shield_value
        self.max_shield_value = shield_value  # 记录最大护盾值
        
    def apply(self):
        super().apply()
        get_emulation_logger().log_effect(f"{self.character.name}获得{self.name}护盾，{self.element_type}元素护盾量为{self.shield_value:.2f}")
        
    def on_finish(self, target):
        super().on_finish(target)

    def on_frame_update(self, target):
        ...
