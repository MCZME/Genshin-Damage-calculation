from core.Event import EventBus, EventHandler, EventType, ShieldEvent

class Shield:
    def __init__(self, base_multiplier):
        self.base_multiplier = base_multiplier
        self.shield_value = 0

    def set_source(self, source):
        self.source = source

    def set_base_value(self, base_value):
        self.base_value = base_value

class ShieldCalculation:
    def __init__(self, source, shield: Shield):
        self.source = source
        self.shield = shield

    def get_shield_strength_bonus(self):
        """获取护盾强效加成"""
        return self.source.attributePanel.get('护盾强效', 0) / 100

    def calculation(self):
        shield_value = self.shield.base_multiplier * (1 + self.get_shield_strength_bonus())
        self.shield.shield_value = shield_value

class ShieldCalculationEventHandler(EventHandler):
    def handle_event(self, event: ShieldEvent):
        if event.event_type == EventType.BEFORE_SHIELD_CREATION:
            calculation = ShieldCalculation(
                event.data['character'],
                event.data['shield']
            )

            calculation.calculation()
            
            # 发布护盾生成后事件
            after_event = ShieldEvent(
                source=event.data['character'],
                shield=event.data['shield'],
                frame=event.frame,
                before=False
            )
            EventBus.publish(after_event)
