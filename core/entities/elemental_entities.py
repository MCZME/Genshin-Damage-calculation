from core.entities.base_entity import BaseEntity
from core.event import DamageEvent, ElementalReactionEvent, EventType, GameEvent, EventHandler
from core.logger import get_emulation_logger
from core.tool import GetCurrentTime, summon_energy
from core.action.reaction import ElementalReaction

class LightningBladeObject(BaseEntity, EventHandler):
    """强能之雷 (雷共鸣)"""
    def __init__(self):
        super().__init__("强能之雷", float('inf'))
        self.cooldown = 5 * 60
        self.last_trigger_time = 0
        
    def apply(self):
        super().apply()
        if self.event_engine:
            self.event_engine.subscribe(EventType.AFTER_OVERLOAD, self)
            self.event_engine.subscribe(EventType.AFTER_SUPERCONDUCT, self)
            self.event_engine.subscribe(EventType.AFTER_ELECTRO_CHARGED, self)
            self.event_engine.subscribe(EventType.AFTER_QUICKEN, self)
            self.event_engine.subscribe(EventType.AFTER_AGGRAVATE, self)
            self.event_engine.subscribe(EventType.AFTER_HYPERBLOOM, self)

    def on_finish(self, target):
        super().on_finish(target)
        if self.event_engine:
            # 清除所有订阅
            pass 

    def on_frame_update(self, target): pass

    def handle_event(self, event: GameEvent):
        if event.frame - self.last_trigger_time < self.cooldown:
            return
        self.last_trigger_time = event.frame
        from core.context import get_context
        ctx = get_context()
        if ctx.team and ctx.team.current_character:
            summon_energy(1, ctx.team.current_character, ('雷', 2))
            get_emulation_logger().log_effect('🔋 触发强能之雷，产生雷微粒')

class DendroCoreObject(BaseEntity):
    """草原核"""
    active = []
    def __init__(self, source, target, damage):
        super().__init__("草原核", 6*60)
        self.damage = damage
        self.damage.source = source
        self.damage.target = target

    def apply(self):
        super().apply()
        DendroCoreObject.active.append(self)
        if len(DendroCoreObject.active) > 5:
            DendroCoreObject.active[0].on_finish(None)
            DendroCoreObject.active.pop(0)

    def on_finish(self, target):
        super().on_finish(target)
        # 触发爆炸伤害逻辑 (此处简化)
        if self in DendroCoreObject.active:
            DendroCoreObject.active.remove(self)