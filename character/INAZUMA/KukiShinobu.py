from core.BaseClass import (ChargedAttackSkill, ConstellationEffect, ElementalEnergy, 
                            EnergySkill, NormalAttackSkill, PlungingAttackSkill, SkillBase, TalentEffect)
from character.INAZUMA.inazuma import Inazuma
from core.Event import ChargedAttackEvent, DamageEvent, EventBus, EventHandler, EventType, HealEvent, HurtEvent, ObjectEvent
from core.Logger import get_emulation_logger
from core.Team import Team
from core.Tool import GetCurrentTime
from core.calculation.DamageCalculation import Damage, DamageType
from core.BaseObject import baseObject
from core.calculation.HealingCalculation import Healing, HealingType

class NormalAttack(NormalAttackSkill):
    def __init__(self, lv):
        super().__init__(lv)
        self.hit_frames = [12, 20, 17, 51]
        self.end_action_frame = 34
        self.damage_values = {
            1:[48.76, 52.73, 56.7, 62.37, 66.34, 70.88, 77.11, 83.35, 89.59, 96.39, 103.19, 110, 116.8, 123.61, 130.41],
            2:[44.55, 48.17, 51.8, 56.98, 60.61, 64.75, 70.45, 76.15, 81.84, 88.06, 94.28, 100.49, 106.71, 112.92, 119.14],
            3:[59.34, 64.17, 69, 75.9, 80.73, 86.25, 93.84, 101.43, 109.02, 117.3, 125.58, 133.86, 142.14, 150.42, 158.7],
            4:[76.11, 82.31, 88.5, 97.35, 103.55, 110.63, 120.36, 130.1, 139.83, 150.45, 161.07, 171.69, 182.31, 192.93, 203.55]
        }

class ChargedAttack(ChargedAttackSkill):
    def __init__(self, lv):
        super().__init__(lv)
        self.hit_frame = [14, 25]
        self.total_frames = 35
        
        self.damageMultipiler = {
            1:[55.63, 60.16, 64.69, 71.16, 75.69, 80.86, 87.98, 95.09, 102.21, 109.97, 117.74, 125.5, 133.26, 141.02, 148.79],
            2:[66.77, 72.2, 77.63, 85.4, 90.83, 97.04, 105.58, 114.12, 122.66, 131.98, 141.29, 150.61, 159.93, 169.24, 178.56]
        }
        
    def on_frame_update(self, target):
        if self.current_frame in self.hit_frame:
            self._apply_attack(target)

    def _apply_attack(self, target):
        i = self.hit_frame.index(self.current_frame)
        event = ChargedAttackEvent(self.caster, frame=GetCurrentTime())
        EventBus.publish(event)

        damage = Damage(
            damageMultipiler=self.damageMultipiler[i][self.lv-1],
            element=self.element,
            damageType=DamageType.CHARGED,
            name=f'重击'
        )
        damage_event = DamageEvent(self.caster, target, damage, GetCurrentTime())
        EventBus.publish(damage_event)

        event = ChargedAttackEvent(self.caster, frame=GetCurrentTime(), before=False)
        EventBus.publish(event)

class PlungingAttack(PlungingAttackSkill):
    pass

class SanctifyingRingObject(baseObject):
    def __init__(self, character, skill_lv):
        super().__init__("越祓草轮", 12 * 60)
        self.character = character
        self.skill_lv = skill_lv
        self.last_trigger_time = 16
        self.interval = 1.5 * 60 
        
        # 技能参数
        self.damage_values = [25.24, 27.13, 29.03, 31.55, 33.44, 35.34, 37.86, 
                              40.38, 42.91, 45.43, 47.96, 50.48, 53.64, 56.79, 59.95]
        self.heal_values = [
            (3, 288.89), (3.23, 317.78), (3.45, 349.08), (3.75, 382.79), 
            (3.98, 418.91), (4.2, 457.43), (4.5, 498.37), (4.8, 541.71), 
            (5.1, 587.45), (5.4, 635.61), (5.7, 686.17), (6, 739.14), 
            (6.38, 794.52), (6.75, 852.31), (7.13, 912.5)
        ]

    def on_frame_update(self, target):
            
        if self.current_frame - self.last_trigger_time >= self.interval:
            self.last_trigger_time = self.current_frame
            self._apply_effect(target)

    def _apply_effect(self, target):
        # 造成伤害
        damage = Damage(
            damageMultipiler=self.damage_values[self.skill_lv-1],
            element=('雷', 1),
            damageType=DamageType.SKILL,
            name='越祓草轮伤害'
        )
        damage_event = DamageEvent(self.character, target, damage, GetCurrentTime())
        EventBus.publish(damage_event)

        # 治疗当前角色
        heal_multiplier = self.heal_values[self.skill_lv-1]
        healing = Healing(
            base_Multipiler=heal_multiplier,
            healing_type=HealingType.SKILL,
            name='越祓草轮治疗',
            MultiplierProvider='来源'
        )
        healing.base_value = '生命值'
        heal_event = HealEvent(
            source=self.character,
            target=Team.current_character,
            healing=healing,
            frame=GetCurrentTime()
        )
        EventBus.publish(heal_event)

class ElementalSkill(SkillBase):
    def __init__(self, lv):
        super().__init__(
            name="越祓雷草之轮",
            total_frames=50,  
            cd=15 * 60,
            lv=lv,
            element=('雷', 1),
            interruptible=False
        )
        self.hit_frame = 11 
        self.damageMultipiler = [75.71, 81.39, 87.07, 94.64, 100.32, 106, 113.57, 121.14, 
                              128.71, 136.28, 143.85, 151.42, 160.89, 170.35, 179.82]
        self.cd_frame = 7

    def on_frame_update(self, target):
        if self.current_frame == self.hit_frame:
            damage = Damage(
                damageMultipiler=self.damageMultipiler[self.lv-1],
                element=('雷', 1),
                damageType=DamageType.SKILL,
                name='越祓雷草之轮'
            )
            damage_event = DamageEvent(self.caster, target, damage, GetCurrentTime())
            EventBus.publish(damage_event)
            if self.caster.currentHP / self.caster.maxHP > 0.2:
                EventBus.publish(HurtEvent(self.caster, self.caster, 0.3 * self.caster.currentHP, GetCurrentTime()))
        elif self.current_frame == 23:
            SanctifyingRingObject(self.caster, self.lv).apply()

    def on_interrupt(self):
        super().on_interrupt()

    def on_finish(self):
        super().on_finish()

class PurificationFieldObject(baseObject):
    def __init__(self, character, skill_lv):
        # 根据生命值决定持续时间和段数
        if character.currentHP / character.maxHP <= 0.5:
            self.duration = 3.5 * 60
        else:
            self.duration = 2 * 60
            
        super().__init__("御咏鸣神结界", self.duration)
        self.character = character
        self.skill_lv = skill_lv
        self.last_trigger_time = 0
        self.interval = 0.3 * 60
        
        # 伤害参数 (生命值百分比)
        self.damage_multipliers = [
            (3.6, 25.23), (3.88, 27.13), (4.15, 29.02), (4.51, 31.54),
            (4.78, 33.43), (5.05, 35.33), (5.41, 37.85), (5.77, 40.37),
            (6.13, 42.9), (6.49, 45.42), (6.85, 47.94), (7.21, 50.47),
            (7.66, 53.62), (8.11, 56.78), (8.56, 59.93)
        ]

    def on_frame_update(self, target):
        if (self.current_frame - self.last_trigger_time >= self.interval):
            self.last_trigger_time = self.current_frame
            self._apply_damage(target)

    def _apply_damage(self, target):
        hp_multiplier, base_damage = self.damage_multipliers[self.skill_lv-1]
        
        damage = Damage(
            damageMultipiler=hp_multiplier,
            element=('雷', 1),
            damageType=DamageType.BURST,
            name='御咏鸣神刈山祭'
        )
        damage.setBaseValue('生命值')
        damage_event = DamageEvent(self.character, target, damage, GetCurrentTime())
        EventBus.publish(damage_event)

class ElementalBurst(EnergySkill):
    def __init__(self, lv):
        super().__init__(
            name="御咏鸣神刈山祭",
            total_frames=62,
            cd=15 * 60,
            lv=lv,
            element=('雷', 1),
            energy_cost=60,
            interruptible=False
        )
        self.hit_frame = 50

    def on_frame_update(self, target):
        if self.current_frame == self.hit_frame:
            field = PurificationFieldObject(self.caster, self.lv)
            field.apply()

class PassiveSkillEffect_1(TalentEffect,EventHandler):
    def __init__(self):
        super().__init__('破笼之志')
        self.is_active = False

    def apply(self, character):
       super().apply(character)

       EventBus.subscribe(EventType.AFTER_HEALTH_CHANGE, self)

    def handle_event(self, event):
        if event.event_type == EventType.AFTER_HEALTH_CHANGE:
            if event.data['character'] == self.character:
                if self.character.currentHP / self.character.maxHP <= 0.5 and not self.is_active:
                    self.is_active = True
                    self.character.attributePanel['治疗加成'] += 15
                elif self.character.currentHP / self.character.maxHP > 0.5 and self.is_active:
                    self.is_active = False
                    self.character.attributePanel['治疗加成'] -= 15

class PassiveSkillEffect_2(TalentEffect):
    def __init__(self):
        super().__init__('安心之所')

    def apply(self, character):
        super().apply(character)


class ConstellationEffect_1(ConstellationEffect):
    pass

class ConstellationEffect_2(ConstellationEffect):
    pass

class ConstellationEffect_3(ConstellationEffect):
    pass

class ConstellationEffect_4(ConstellationEffect):
    pass

class ConstellationEffect_5(ConstellationEffect):
    pass

class ConstellationEffect_6(ConstellationEffect):
    pass

class KukiShinobu(Inazuma):
    ID = 51
    def __init__(self, level=1, skill_params=..., constellation=0):
        super().__init__(KukiShinobu.ID, level, skill_params, constellation)

    def _init_character(self):
        super()._init_character()
        self.elemental_energy = ElementalEnergy(self, ('雷', 60))
        self.NormalAttack = NormalAttack(self.skill_params[0])
        self.ChargedAttack = ChargedAttack(self.skill_params[0])
        self.Skill = ElementalSkill(self.skill_params[1])
        self.Burst = ElementalBurst(self.skill_params[2])
        self.talent1 = PassiveSkillEffect_1()
        self.talent2 = PassiveSkillEffect_2()
        self.constellation_effects[0] = ConstellationEffect_1()
        self.constellation_effects[1] = ConstellationEffect_2()
        self.constellation_effects[2] = ConstellationEffect_3()
        self.constellation_effects[3] = ConstellationEffect_4()
        self.constellation_effects[4] = ConstellationEffect_5()
        self.constellation_effects[5] = ConstellationEffect_6()

kukiShinobu_table = {
    'id': KukiShinobu.ID,
    'name': '久岐忍',
    'type': '单手剑',
    'element': '雷',
    'rarity': 4,
    'association': '稻妻',
    'normalAttack': {'攻击次数': 4},
    'chargedAttack': {},
    # 'plungingAttack': {'攻击距离': ['高空', '低空']},
    'skill': {},
    'burst': {}
}
