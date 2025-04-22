from abc import ABC,abstractmethod
from core.Event import DamageEvent, ElementalReactionEvent, EnergyChargeEvent, EventBus, EventType, GameEvent, ObjectEvent
from core.Logger import get_emulation_logger
from core.Team import Team
from core.Tool import GetCurrentTime, summon_energy
from core.elementalReaction.ElementalReaction import ElementalReaction


class baseObject(ABC):
    def __init__(self,name, life_frame = 0):
        self.name = name
        self.is_active = False
        self.current_frame = 0
        self.life_frame = life_frame

    def apply(self):
        Team.add_object(self)
        self.is_active = True
        EventBus.publish(ObjectEvent(self, GetCurrentTime()))

    def update(self,target):
        self.current_frame += 1
        if self.current_frame >= self.life_frame:
            self.on_finish(target)
        self.on_frame_update(target)

    @abstractmethod
    def on_frame_update(self,target):
        ...

    def on_finish(self,target):
        get_emulation_logger().log_object(f'{self.name} 存活时间结束')
        self.is_active = False
        EventBus.publish(ObjectEvent(self, GetCurrentTime(),False))
           
class ArkheObject(baseObject):
    def __init__(self, name, character, arkhe_type, damage, life_frame=0):
        super().__init__(name+':'+arkhe_type, life_frame)
        self.character = character
        self.arkhe_type = arkhe_type
        self.damage = damage

    def on_finish(self, target):
        super().on_finish(target)
        self.damage.setDamageData('始基力',self.arkhe_type)
        event = DamageEvent(self.character, target, self.damage, GetCurrentTime())
        EventBus.publish(event)

    def on_frame_update(self, target):
        ...

class LightningBladeObject(baseObject):
    def __init__(self):
        super().__init__("强能之雷", float('inf'))
        self.cooldown = 5 * 60  # 5秒冷却(单位:帧)
        self.last_trigger_time = 0  # 上次触发时间
        
    def apply(self):
        super().apply()
        # 注册事件监听
        EventBus.subscribe(EventType.AFTER_OVERLOAD, self)
        EventBus.subscribe(EventType.AFTER_SUPERCONDUCT, self)

    def on_finish(self, target):
        super().on_finish(target)
        EventBus.unsubscribe(EventType.AFTER_OVERLOAD, self)
        EventBus.unsubscribe(EventType.AFTER_SUPERCONDUCT, self)

    def on_frame_update(self, target):
        pass

    def handle_event(self, event: GameEvent):
        """处理元素反应事件"""
        current_time = event.frame
        
        # 检查冷却
        if current_time - self.last_trigger_time < self.cooldown:
            return
            
        # 恢复2点能量
        self.last_trigger_time = current_time
        
        # 创建能量恢复事件
        summon_energy(1,Team.current_character,('雷',2))
        get_emulation_logger().log_effect('🔋 触发强能之雷，获得一个雷元素微粒')

class EnergyDropsObject(baseObject):
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
    
    def on_frame_update(self, target):
        pass

    def on_finish(self, target):
        get_emulation_logger().log_object(f'{self.character.name}的 {self.name} 存活时间结束')
        self.is_active = False
        energy_event = EnergyChargeEvent(self.character, self.element_energy, GetCurrentTime(),
                                        is_fixed=self.is_fixed, is_alone=self.is_alone)
        EventBus.publish(energy_event)

class DendroCoreObject(baseObject):
    active = []
    last_bloom_time = 0
    bloom_count = -30
    def __init__(self, source, target,damage):
        super().__init__("草原核", 6*60)
        self.damage = damage
        self.damage.source = source
        self.damage.target = target

    def apply(self):
        super().apply()
        DendroCoreObject.active.append(self)
        get_emulation_logger().log_object(f'🌿 产生一个草原核')
        if len(DendroCoreObject.active) > 5:
            DendroCoreObject.active[0].on_finish(None)
            DendroCoreObject.active.pop(0)

    def apply_element(self, damage):
        if self.is_active:
            if damage.element[0] in ['火','雷']:
                e = ElementalReaction(damage)
                e.set_reaction_elements(damage.element[0], '原')
                EventBus.publish(ElementalReactionEvent(e, GetCurrentTime()))
                self.is_active = False
        
    def on_finish(self, target):
        super().on_finish(target)
        if GetCurrentTime() - DendroCoreObject.last_bloom_time > 0.5*60:
            DendroCoreObject.bloom_count = 0
            DendroCoreObject.last_bloom_time = GetCurrentTime()
        if DendroCoreObject.bloom_count < 2:
            DendroCoreObject.bloom_count += 1
            event = DamageEvent(self.damage.source, self.damage.target, self.damage, GetCurrentTime())
            EventBus.publish(event)

    def on_frame_update(self, target):
        return super().on_frame_update(target)