from typing import Any, Optional
from core.effect.base import BaseEffect
from core.mechanics.aura import Element

class ShieldEffect(BaseEffect):
    """
    护盾效果载体。
    本身不具备逻辑，由 ShieldSystem 统一驱动吸收判定。
    """
    def __init__(self, owner: Any, name: str, element: Element, max_hp: float, duration: int):
        # 护盾通常是刷新模式 (REFRESH)
        super().__init__(owner, name, duration)
        self.element = element
        self.max_hp = max_hp
        self.current_hp = max_hp

    def on_apply(self):
        # 将自己挂载到角色的护盾列表
        if hasattr(self.owner, "shield_effects"):
            self.owner.shield_effects.append(self)

    def on_remove(self):
        if self.owner and hasattr(self.owner, "shield_effects"):
            if self in self.owner.shield_effects:
                self.owner.shield_effects.remove(self)

# 效果基类
class TalentEffect:
    """
    固有天赋效果基类。
    unlock_level: 解锁该天赋所需的角色等级 (通常为 20, 60)。
    """
    def __init__(self, name: str, unlock_level: int = 1):
        self.name = name
        self.unlock_level = unlock_level
        self.character = None
        self.is_active = False
        
    def apply(self, character: Any):
        self.character = character
        if self.character.level >= self.unlock_level:
            self.is_active = True
            self.on_apply()

    def on_apply(self):
        """子类在此实现具体的天赋激活逻辑"""
        pass

    def on_frame_update(self):
        if not self.is_active:
            return
        pass

class ConstellationEffect:
    """
    命座效果基类。
    unlock_constellation: 该效果对应的命座层级 (1-6)。
    """
    def __init__(self, name: str, unlock_constellation: int = 1):
        self.name = name
        self.unlock_constellation = unlock_constellation
        self.character = None
        self.is_active = False

    def apply(self, character: Any):
        """
        由 Character.apply_effects 调用。
        仅在角色已激活该命座层级时生效。
        """
        self.character = character
        if self.character.constellation_level >= self.unlock_constellation:
            self.is_active = True
            self.on_apply()

    def on_apply(self):
        """子类在此实现具体的命座激活逻辑"""
        pass

    def on_frame_update(self):
        if not self.is_active:
            return
        pass