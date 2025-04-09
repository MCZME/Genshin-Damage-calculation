from abc import ABC,abstractmethod
from setup.Event import DamageEvent, EventBus, EventType, GameEvent
from setup.Logger import get_emulation_logger
from setup.Team import Team
from setup.Tool import GetCurrentTime, summon_energy


class baseObject(ABC):
    def __init__(self,name, life_frame = 0):
        self.name = name

        self.current_frame = 0
        self.life_frame = life_frame

    def apply(self):
        Team.add_object(self)

    def update(self,target):
        self.current_frame += 1
        if self.current_frame >= self.life_frame:
            self.on_finish(target)
        self.on_frame_update(target)

    @abstractmethod
    def on_frame_update(self,target):
        ...

    def on_finish(self,target):
        print(f'{self.name} 存活时间结束')
        Team.remove_object(self)
           
class ArkheObject(baseObject):
    def __init__(self, name, character, arkhe_type, damage, life_frame=0):
        super().__init__(name+':'+arkhe_type, life_frame)
        self.character = character
        self.arkhe_type = arkhe_type
        self.damage = damage

    def on_finish(self, target):
        super().on_finish(target)
        event = DamageEvent(self.character, target, self.damage, GetCurrentTime())
        EventBus.publish(event)
        print(f'💫 {self.name}对{target.name}造成{self.damage.damage:.2f}点伤害')

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
