from typing import Any
from core.effect.base import BaseEffect
from core.event import DamageEvent
from core.tool import GetCurrentTime
from core.action.damage import Damage

class ElementalInfusionEffect(BaseEffect):
    """元素附魔效果"""
    def __init__(self, owner: Any, name: str, element_type: str, duration: float):
        super().__init__(owner, name, duration)
        self.element_type = element_type
        # 内部附着冷却逻辑保持 (此处稍作简化)
        self.last_trigger_time = 0

    def on_apply(self):
        # 附魔通常不直接修改面板，而是在伤害发布阶段被查询
        pass

class ElectroChargedEffect(BaseEffect):
    """感电效果"""
    def __init__(self, owner: Any, source_char: Any, damage: Damage):
        super().__init__(owner, "感电", duration=10) # 这是一个占位持续时间
        self.source_char = source_char
        self.damage = damage
        self.tick_timer = 0

    def on_tick(self, target: Any):
        # 每 60 帧触发一次伤害
        self.tick_timer += 1
        if self.tick_timer % 60 == 0:
            # 检查持有者身上是否还有雷水共存
            if hasattr(self.owner, 'aura') and self.owner.aura.has_elements(['雷', '水']):
                # 发布感电伤害
                self.source_char.event_engine.publish(
                    DamageEvent(self.source_char, self.owner, self.damage, GetCurrentTime())
                )
                # 扣除元素量逻辑...
            else:
                self.remove()

class BurningEffect(BaseEffect):
    """燃烧效果"""
    def __init__(self, owner: Any, source_char: Any, damage: Damage):
        super().__init__(owner, "燃烧", duration=float('inf'))
        self.source_char = source_char
        self.damage = damage
        self.tick_timer = 0

    def on_tick(self, target: Any):
        self.tick_timer += 1
        if self.tick_timer % 15 == 0: # 0.25秒一跳
             self.source_char.event_engine.publish(
                DamageEvent(self.source_char, self.owner, self.damage, GetCurrentTime())
            )
             # 检查草/燃元素是否耗尽逻辑...
