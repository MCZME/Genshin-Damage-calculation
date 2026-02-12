from core.context import get_context
from typing import Any
from core.entities.base_entity import BaseEntity
from core.event import EnergyChargeEvent
from core.logger import get_emulation_logger
import core.tool as T

class EnergyDropsObject(BaseEntity):
    """能量球/微粒实体。"""
    def __init__(self, character: Any, element_energy: Any, life_frame: int = 60, 
                 is_fixed: bool = False, is_alone: bool = False, **kwargs: Any):
        if element_energy[1] == 2:
            name = "元素微粒"
        elif element_energy[1] == 6:
            name = "元素晶球"
        else:
            name = "元素能量"
        super().__init__(name, life_frame, **kwargs)
        self.character = character
        self.element_energy = element_energy
        self.is_fixed = is_fixed
        self.is_alone = is_alone
    
    def on_frame_update(self, target: Any) -> None:
        pass

    def on_finish(self, target: Any) -> None:
        get_emulation_logger().log_object(f"{self.character.name}的 {self.name} 存活时间结束")
        energy_event = EnergyChargeEvent(self.character, self.element_energy, T.get_current_time(),
                                        is_fixed=self.is_fixed, is_alone=self.is_alone)
        if self.event_engine:
            self.event_engine.publish(energy_event)
        else:
            get_context().event_engine.publish(energy_event) # 回退

