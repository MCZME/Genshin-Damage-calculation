from core.systems.utils import AttributeCalculator
from core.systems.base_system import GameSystem
from core.context import EventEngine
from core.event import EventType, ShieldEvent
from core.action.shield import Shield

# ---------------------------------------------------------
# Shield Calculation Helper
# ---------------------------------------------------------
class ShieldCalculation:
    def __init__(self, source, shield: Shield):
        self.source = source
        self.shield = shield

    def get_shield_strength_bonus(self):
        """获取护盾强效加成"""
        return AttributeCalculator.get_shield_strength_bonus(self.source)

    def calculation(self):
        shield_value = self.shield.base_multiplier * (1 + self.get_shield_strength_bonus())
        self.shield.shield_value = shield_value

# ---------------------------------------------------------
# Shield System
# ---------------------------------------------------------
class ShieldSystem(GameSystem):
    def register_events(self, engine: EventEngine):
        engine.subscribe(EventType.BEFORE_SHIELD_CREATION, self)

    def handle_event(self, event: ShieldEvent):
        if event.event_type == EventType.BEFORE_SHIELD_CREATION:
            self._handle_shield_creation(event)

    def _handle_shield_creation(self, event: ShieldEvent):
        calculation = ShieldCalculation(
            event.data['character'],
            event.data['shield']
        )

        calculation.calculation()
        
        from core.logger import get_emulation_logger
        get_emulation_logger().log_shield(
            event.data['character'],
            event.data['shield'].name,
            event.data['shield'].shield_value
        )
        
        # 发布护盾生成后事件
        after_event = ShieldEvent(
            source=event.data['character'],
            shield=event.data['shield'],
            frame=event.frame,
            before=False
        )
        self.engine.publish(after_event)
