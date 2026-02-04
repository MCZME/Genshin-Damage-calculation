from core.base_entity import BaseEntity
from core.Event import DamageEvent, EventBus
from core.Tool import GetCurrentTime

class ArkheObject(BaseEntity):
    def __init__(self, name, character, arkhe_type, damage, life_frame=0):
        super().__init__(name+':'+arkhe_type, life_frame)
        self.character = character
        self.arkhe_type = arkhe_type
        self.damage = damage

    def on_finish(self, target):
        super().on_finish(target)
        self.damage.setDamageData('始基力', self.arkhe_type)
        event = DamageEvent(self.character, target, self.damage, GetCurrentTime())
        EventBus.publish(event)

    def on_frame_update(self, target):
        ...
