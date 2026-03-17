from typing import Any, Dict, List
from core.effect.base import BaseEffect
from core.mechanics.aura import Element


class ShieldEffect(BaseEffect):
    """
    护盾效果载体。
    本身不具备逻辑，由 ShieldSystem 统一驱动吸收判定。
    """

    def __init__(
        self, owner: Any, name: str, element: Element, max_hp: float, duration: int
    ):
        # 护盾通常是刷新模式 (REFRESH)
        super().__init__(owner, name, duration)
        self.element = element
        self.max_hp = max_hp
        self.current_hp = max_hp

    def on_apply(self):
        if hasattr(self.owner, "shield_effects"):
            self.owner.shield_effects.append(self)

    def on_remove(self):
        if self.owner and hasattr(self.owner, "shield_effects"):
            if self in self.owner.shield_effects:
                self.owner.shield_effects.remove(self)


class StatModifierEffect(BaseEffect):
    """
    通用属性修改效果。
    在生效期间通过 add_modifier 修改 owner 的属性，支持审计追踪。
    """

    def __init__(self, owner: Any, name: str, stats: Dict[str, float], duration: float):
        super().__init__(owner, name, duration)
        self.stats = stats
        self.modifier_records: List[Any] = []

    def on_apply(self):
        if not hasattr(self.owner, "add_modifier"):
            return
        for key, value in self.stats.items():
            modifier = self.owner.add_modifier(self.name, key, value, "ADD")
            self.modifier_records.append(modifier)

    def on_remove(self):
        if not hasattr(self.owner, "remove_modifier"):
            return
        for modifier in self.modifier_records:
            self.owner.remove_modifier(modifier)
        self.modifier_records.clear()


class ResistanceDebuffEffect(StatModifierEffect):
    """
    抗性削减效果 (如超导、钟离减抗)。
    """

    def __init__(
        self, owner: Any, name: str, elements: List[str], amount: float, duration: float
    ):
        # 构造属性字典：{"物理元素抗性": -40.0, ...}
        stats = {f"{el}元素抗性": -amount for el in elements}
        super().__init__(owner, name, stats, duration)


# 固有天赋与命座基类
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
        if self.character and self.character.level >= self.unlock_level:
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
        if self.character and self.character.constellation_level >= self.unlock_constellation:
            self.is_active = True
            self.on_apply()

    def on_apply(self):
        """子类在此实现具体的命座激活逻辑"""
        pass

    def on_frame_update(self):
        if not self.is_active:
            return
        pass
