from typing import Any
from core.base_entity import BaseEntity
from core.event import DamageEvent, HealEvent
from core.logger import get_emulation_logger
from core.tool import GetCurrentTime
from core.action.damage import Damage, DamageType
from core.action.healing import Healing, HealingType
from core.mechanics.infusion import Infusion
from core.team import Team

class DamageEffect:
    """持续伤害效果 (瞬时剪影/聚焦印象)"""
    def __init__(self, name: str, caster: Any, target: Any, damage_mult: float, interval: int, duration: int):
        self.name = name
        self.caster = caster
        self.target = target
        self.damage_mult = damage_mult
        self.interval = interval
        self.duration = duration
        self.is_active = True
        self.last_trigger_time = 0
        self.infusion = Infusion([1, 0], 12 * 60, 6)

    def apply(self):
        existing = next((e for e in self.target.active_effects if getattr(e, 'name', None) == self.name), None)
        if existing:
            existing.duration = self.duration
            return
        self.target.add_effect(self)
        get_emulation_logger().log_effect(f"{self.target.name} 获得了 {self.name} 效果")

    def update(self, target: Any):
        self.duration -= 1
        if self.duration <= 0:
            self.is_active = False
            return

        current_time = GetCurrentTime()
        if current_time - self.last_trigger_time >= self.interval:
            self.last_trigger_time = current_time
            damage = Damage(
                damage_multiplier=self.damage_mult,
                element=('冰', self.infusion.apply_infusion()),
                damage_type=DamageType.SKILL,
                name=self.name
            )
            # 使用局部引擎发布，自动冒泡
            self.caster.event_engine.publish(DamageEvent(self.caster, self.target, damage, current_time))

class VerificationEffect:
    """核实印记效果"""
    def __init__(self, character: Any, target: Any):
        self.name = '核实'
        self.character = character
        self.target = target
        self.duration = 6 * 60
        self.is_active = True
        self.last_heal_time = 0
        self.heal_interval = 2 * 60

    def apply(self):
        existing = next((e for e in self.target.active_effects if getattr(e, 'name', None) == self.name), None)
        if existing:
            existing.duration = self.duration
            return
        self.target.add_effect(self)
        get_emulation_logger().log_effect(f'{self.character.name}为{self.target.name}创建了{self.name}印记')

    def update(self, target: Any):
        self.duration -= 1
        if self.duration <= 0:
            self.is_active = False
            return

        current_time = GetCurrentTime()
        if current_time - self.last_heal_time >= self.heal_interval:
            self.last_heal_time = current_time
            healing = Healing(
                80,
                healing_type=HealingType.PASSIVE,
                name=f'{self.name}·持续治疗'
            )
            healing.base_value = '攻击力'
            self.character.event_engine.publish(HealEvent(
                source=self.character,
                target=self.target,
                healing=healing,
                frame=current_time
            ))

class FieldObject(BaseEntity):
    """大招生成的临事场域"""
    def __init__(self, character, camera_damage, field_heal):
        super().__init__('临事场域', life_frame=4 * 60)
        self.character = character
        self.attack_interval = 0.4 * 60
        self.heal_interval = 0.5 * 60
        self.camera_damage = camera_damage
        self.field_heal = field_heal
        self.last_attack_time = 0
        self.last_heal_time = 0
        self.infusion = Infusion([1, 0, 0, 0], 4 * 60, 2)

    def apply(self):
        super().apply()
        get_emulation_logger().log_object(f'{self.character.name}创建了{self.name}')

    def on_frame_update(self, target):
        current_time = GetCurrentTime()
        
        # 周期性相机攻击
        if current_time - self.last_attack_time >= self.attack_interval:
            self.last_attack_time = current_time
            self._apply_camera_attack(target)
            
        # 周期性治疗
        if current_time - self.last_heal_time >= self.heal_interval:
            self.last_heal_time = current_time
            self._apply_heal(target)

    def _apply_camera_attack(self, target):
        damage = Damage(
            damage_multiplier=self.camera_damage,
            element=('冰', self.infusion.apply_infusion()),
            damage_type=DamageType.BURST,
            name=f'{self.name}·温亨廷先生攻击'
        )
        self.event_engine.publish(DamageEvent(self.character, target, damage, GetCurrentTime()))

    def _apply_heal(self, target):
        healing = Healing(
            base_multiplier=self.field_heal,
            healing_type=HealingType.BURST,
            name=f'{self.name}·持续治疗'
        )
        healing.base_value = '攻击力'
        # 治疗当前场上角色
        self.event_engine.publish(HealEvent(
            source=self.character,
            target=Team.current_character,
            healing=healing,
            frame=GetCurrentTime()
        ))
