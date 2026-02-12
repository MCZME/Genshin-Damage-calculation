from typing import Any
from core.effect.base import BaseEffect
from core.tool import get_current_time
from core.action.damage import Damage, DamageType
from core.mechanics.aura import Element

class ElementalInfusionEffect(BaseEffect):
    """
    元素附魔效果
    将普攻、重击、下落攻击的物理伤害转化为特定元素伤害。
    """
    def __init__(self, 
                 owner: Any, 
                 name: str, 
                 element_type: Element, 
                 duration: float, 
                 is_unoverridable: bool = False):
        super().__init__(owner, name, duration)
        self.element_type = element_type # 现在是 Element 枚举
        self.is_unoverridable = is_unoverridable
        self.apply_time = get_current_time() # 用于判定附魔优先级

    def should_apply_infusion(self, damage_type: DamageType) -> float:
        """
        判定是否应该应用附魔及附着强度。
        返回 U 值 (通常附魔产生的是 1U 附着)。
        """
        if damage_type in [DamageType.NORMAL, DamageType.CHARGED, DamageType.PLUNGING]:
            return 1.0
        return 0.0

class ElectroChargedEffect(BaseEffect):
    """
    [Legacy] 感电持续伤害效果
    注意：新的反应系统建议由 AuraManager 的 ec_timer 驱动。
    保留此类仅用于兼容某些特定角色的特殊感电增强逻辑。
    """
    def __init__(self, owner: Any, source_char: Any, damage: Damage):
        super().__init__(owner, "感电", duration=10*60)
        self.source_char = source_char
        self.damage = damage
        self.tick_timer = 0

    def update(self):
        super().update()
        self.tick_timer += 1
        if self.tick_timer % 60 == 0:
            # 这里的 tick 逻辑将来应与 ReactionSystem 整合
            pass

class BurningEffect(BaseEffect):
    """
    [Legacy] 燃烧持续伤害效果
    """
    def __init__(self, owner: Any, source_char: Any, damage: Damage):
        super().__init__(owner, "燃烧", duration=float('inf'))
        self.source_char = source_char
        self.damage = damage
        self.tick_timer = 0

    def update(self):
        super().update()
        self.tick_timer += 1
        if self.tick_timer % 15 == 0:
             # 这里的伤害发布逻辑
             pass
