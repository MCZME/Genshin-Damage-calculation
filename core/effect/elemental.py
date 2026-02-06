from typing import Any
from core.effect.base import BaseEffect
from core.event import DamageEvent
from core.tool import GetCurrentTime
from core.action.damage import Damage, DamageType

class ElementalInfusionEffect(BaseEffect):
    """元素附魔效果"""
    def __init__(self, owner: Any, name: str, element_type: str, duration: float, is_unoverridable: bool = False):
        super().__init__(owner, name, duration)
        self.element_type = element_type
        self.is_unoverridable = is_unoverridable
        self.last_trigger_time = 0

    def should_apply_infusion(self, damage_type: DamageType) -> int:
        """返回附着强度等级，0表示不生效"""
        # 默认对普攻、重击、下落攻击生效，强度为 1
        if damage_type in [DamageType.NORMAL, DamageType.CHARGED, DamageType.PLUNGING]:
            return 1
        return 0

    def on_apply(self):
        pass

class ElectroChargedEffect(BaseEffect):
    """感电效果"""
    def __init__(self, owner: Any, source_char: Any, damage: Damage):
        super().__init__(owner, "感电", duration=10)
        self.source_char = source_char
        self.damage = damage
        self.tick_timer = 0

    def on_tick(self, target: Any):
        self.tick_timer += 1
        if self.tick_timer % 60 == 0:
            if hasattr(self.owner, 'aura') and self.owner.aura.has_elements(['雷', '水']):
                self.source_char.event_engine.publish(
                    DamageEvent(self.source_char, self.owner, self.damage, GetCurrentTime())
                )
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
        if self.tick_timer % 15 == 0:
             self.source_char.event_engine.publish(
                DamageEvent(self.source_char, self.owner, self.damage, GetCurrentTime())
            )