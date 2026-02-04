from typing import Any
from core.effect.common import TalentEffect, ConstellationEffect
from core.event import EventType, EventHandler, GameEvent
from core.action.healing import HealingType
from core.action.damage import Damage, DamageType
from core.effect.BaseEffect import AttackBoostEffect
from core.team import Team
from core.tool import GetCurrentTime
from character.FONTAINE.charlotte.entities import VerificationEffect, DamageEffect, HealEvent

class PassiveSkillEffect_1(TalentEffect):
    """天赋1：冲击力瞬间"""
    def __init__(self):
        super().__init__("冲击力瞬间")

class PassiveSkillEffect_2(TalentEffect):
    """天赋2：多样性调查"""
    def __init__(self):
        super().__init__("多样性调查")

    def update(self, target: Any):
        # 仅在模拟开始的第一帧执行一次
        if GetCurrentTime() == 1:
            a, b = 0, 0
            for char in Team.team:
                if getattr(char, 'association', '') == '枫丹':
                    a += 1
                else:
                    b += 1
            self.character.attribute_panel['治疗加成'] += a * 5
            self.character.attribute_panel['冰元素伤害加成'] += b * 5

class ConstellationEffect_1(ConstellationEffect, EventHandler):
    """命座1：以核实为约束"""
    def __init__(self):
        super().__init__("以核实为约束")

    def apply(self, character: Any):
        super().apply(character)
        self.character.event_engine.subscribe(EventType.AFTER_HEAL, self)

    def handle_event(self, event: GameEvent):
        # 使用 dataclass 属性访问
        healing = getattr(event, 'healing', None)
        if healing and healing.healing_type == HealingType.BURST and event.source == self.character:
            VerificationEffect(self.character, event.data['target']).apply()

class ConstellationEffect_2(ConstellationEffect, EventHandler):
    """命座2：以求真为职守"""
    def __init__(self):
        super().__init__("以求真为职守")

    def apply(self, character: Any):
        super().apply(character)
        self.character.event_engine.subscribe(EventType.AFTER_SKILL, self)

    def handle_event(self, event: GameEvent):
        if event.source == self.character:
            AttackBoostEffect(self.character, self.character, '以求真为职守', 10, 12 * 60).apply()

class ConstellationEffect_3(ConstellationEffect):
    def __init__(self):
        super().__init__("以独立为先决")
    def apply(self, character: Any):
        super().apply(character)
        if character.Burst: character.Burst.lv = min(character.Burst.lv + 3, 15)

class ConstellationEffect_4(ConstellationEffect, EventHandler):
    """命座4：以督促为责任"""
    def __init__(self):
        super().__init__("以督促为责任")
        self.last_attached_time = 0
        self.attached_interval = 20 * 60
        self.attached_count = 0

    def apply(self, character: Any):
        super().apply(character)
        self.character.event_engine.subscribe(EventType.BEFORE_DAMAGE_BONUS, self)
    
    def handle_event(self, event: GameEvent):
        if event.source == self.character:
            damage = event.data['damage']
            effect = next((e for e in damage.target.active_effects if isinstance(e, DamageEffect)), None)
            if effect and damage.damageType == DamageType.BURST:
                if self.attached_count < 5:
                    damage.panel['伤害加成'] += 10
                    self.attached_count += 1
                    if self.attached_count == 1: self.last_attached_time = event.frame
                elif event.frame - self.last_attached_time >= self.attached_interval:
                    self.attached_count = 0

class ConstellationEffect_5(ConstellationEffect):
    def __init__(self):
        super().__init__("以良知为原则")
    def apply(self, character: Any):
        super().apply(character)
        if character.Skill: character.Skill.lv = min(character.Skill.lv + 3, 15)

class ConstellationEffect_6(ConstellationEffect, EventHandler):
    """命座6：以有趣相关为要义"""
    def __init__(self):
        super().__init__("以有趣相关为要义")
        self.last_trigger_time = -6 * 60

    def apply(self, character: Any):
        super().apply(character)
        self.character.event_engine.subscribe(EventType.AFTER_DAMAGE, self)

    def handle_event(self, event: GameEvent):
        if (event.source == Team.current_character and 
            event.frame - self.last_trigger_time >= 6 * 60):
            damage = event.data['damage']
            effect = next((e for e in damage.target.active_effects if getattr(e, 'name', '') == '聚焦印象'), None)
            if effect and damage.damageType in [DamageType.NORMAL, DamageType.CHARGED]:
                self.last_trigger_time = event.frame
                self._trigger_coordination(damage.target)

    def _trigger_coordination(self, target):
        from core.action.damage import Damage, DamageType
        from core.action.healing import Healing, HealingType
        from core.event import DamageEvent, HealEvent
        
        co_dmg = Damage(180, ('冰', 1), DamageType.BURST, '命座6协同伤害')
        self.character.event_engine.publish(DamageEvent(self.character, target, co_dmg, GetCurrentTime()))
        
        heal = Healing(42, HealingType.BURST, '命座6治疗')
        heal.base_value = '攻击力'
        self.character.event_engine.publish(HealEvent(self.character, Team.current_character, heal, GetCurrentTime()))