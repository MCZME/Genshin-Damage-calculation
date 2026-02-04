from core.base_entity import BaseEntity
from core.Event import DamageEvent, ElementalReactionEvent, EventBus, EventType, GameEvent
from core.Logger import get_emulation_logger
from core.Team import Team
from core.Tool import GetCurrentTime, summon_energy
from core.elementalReaction.ElementalReaction import ElementalReaction

class LightningBladeObject(BaseEntity):
    def __init__(self):
        super().__init__("强能之雷", float('inf'))
        self.cooldown = 5 * 60  # 5秒冷却(单位:帧)
        self.last_trigger_time = 0  # 上次触发时间
        
    def apply(self):
        super().apply()
        # 注册事件监听
        EventBus.subscribe(EventType.AFTER_OVERLOAD, self)
        EventBus.subscribe(EventType.AFTER_SUPERCONDUCT, self)
        EventBus.subscribe(EventType.AFTER_ELECTRO_CHARGED, self)
        EventBus.subscribe(EventType.AFTER_QUICKEN, self)
        EventBus.subscribe(EventType.AFTER_AGGRAVATE, self)
        EventBus.subscribe(EventType.AFTER_HYPERBLOOM, self)

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
        summon_energy(1, Team.current_character, ('雷', 2))
        get_emulation_logger().log_effect('🔋 触发强能之雷，获得一个雷元素微粒')

class DendroCoreObject(BaseEntity):
    active = []
    last_bloom_time = 0
    bloom_count = -30
    def __init__(self, source, target, damage):
        super().__init__("草原核", 6*60)
        self.damage = damage
        self.damage.source = source
        self.damage.target = target
        self.repeatable = True

    def apply(self):
        super().apply()
        DendroCoreObject.active.append(self)
        get_emulation_logger().log_object(f'🌿 产生一个草原核')
        if len(DendroCoreObject.active) > 5:
            DendroCoreObject.active[0].on_finish(None)
            DendroCoreObject.active.pop(0)
            DendroCoreObject.active.append(self)

    def apply_element(self, damage):
        if self.is_active:
            if damage.element[0] in ['火', '雷']:
                e = ElementalReaction(damage)
                e.set_reaction_elements(damage.element[0], '原')
                EventBus.publish(ElementalReactionEvent(e, GetCurrentTime()))
                self.is_active = False
                DendroCoreObject.active.remove(self)
        
    def on_finish(self, target):
        super().on_finish(target)
        if GetCurrentTime() - DendroCoreObject.last_bloom_time > 0.5*60:
            DendroCoreObject.bloom_count = 0
        if DendroCoreObject.bloom_count < 2:
            DendroCoreObject.bloom_count += 1
            event = DamageEvent(self.damage.source, self.damage.target, self.damage, GetCurrentTime())
            EventBus.publish(event)
            DendroCoreObject.active.remove(self)
            DendroCoreObject.last_bloom_time = GetCurrentTime()

    def on_frame_update(self, target):
        return super().on_frame_update(target)
