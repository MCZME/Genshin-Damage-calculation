from core.base_entity import BaseEntity
from core.Event import EnergyChargeEvent, EventBus
from core.Logger import get_emulation_logger
from core.Tool import GetCurrentTime

class EnergyDropsObject(BaseEntity):
    def __init__(self, character, element_energy, life_frame=60, is_fixed=False, is_alone=False):
        if element_energy[1] == 2:
            name = "元素微粒"
        elif element_energy[1] == 6:
            name = "元素晶球"
        else:
            name = "元素能量"
        super().__init__(name, life_frame)
        self.character = character
        self.element_energy = element_energy
        self.is_fixed = is_fixed
        self.is_alone = is_alone
        self.repeatable = True
    
    def on_frame_update(self, target):
        pass

    def on_finish(self, target):
        get_emulation_logger().log_object(f'{self.character.name}的 {self.name} 存活时间结束')
        self.is_active = False
        energy_event = EnergyChargeEvent(self.character, self.element_energy, GetCurrentTime(),
                                        is_fixed=self.is_fixed, is_alone=self.is_alone)
        EventBus.publish(energy_event)
