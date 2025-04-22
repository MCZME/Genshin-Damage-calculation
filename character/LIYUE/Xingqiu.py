from character.LIYUE.liyue import Liyue
from core.BaseClass import (ChargedAttackSkill, ConstellationEffect, ElementalEnergy,
                            EnergySkill, NormalAttackSkill, PlungingAttackSkill, SkillBase, TalentEffect)
from core.BaseObject import baseObject
from core.Event import ChargedAttackEvent, DamageEvent, EventBus, EventHandler, EventType, HealEvent
from core.Team import Team
from core.Tool import GetCurrentTime, summon_energy
from core.calculation.DamageCalculation import Damage, DamageType
from core.calculation.HealingCalculation import Healing, HealingType
from core.effect.BaseEffect import ResistanceDebuffEffect

class NormalAttack(NormalAttackSkill):
    def __init__(self, lv, cd=0):
        super().__init__(lv, cd)
        self.segment_frames = [10,22,25,29,39]
        self.end_action_frame = 37
        
        self.damageMultipiler = {
            1: [46.61, 50.41, 54.2, 59.62, 63.41, 67.75, 73.71, 79.67, 85.64, 92.14, 99.59, 108.36, 117.12, 125.88, 135.45],
            2: [47.64, 51.52, 55.4, 60.94, 64.82, 69.25, 75.34, 81.44, 87.53, 94.18, 101.8, 110.76, 119.71, 128.67, 138.44],
            3: [28.55, 30.88, 33.2, 36.52, 38.84, 41.5, 45.15, 48.8, 52.46, 56.44, 61.01, 66.37, 71.74, 77.11, 82.97],  # 每击两次
            4: [55.99, 60.54, 65.1, 71.61, 76.17, 81.38, 88.54, 95.7, 102.86, 110.67, 119.62, 130.15, 140.67, 151.2, 162.68],
            5: [35.86, 38.78, 41.7, 45.87, 48.79, 52.13, 56.71, 61.3, 65.89, 70.89, 76.62, 83.37, 90.11, 96.85, 104.21]  # 每击两次
        }

class ChargedAttack(ChargedAttackSkill):
    def __init__(self, lv, total_frames=32, cd=0):
        super().__init__(lv, total_frames, cd)
        self.hit_frames = [8, 20]  
        self.damageMultipiler = [
            [47.3, 51.15, 55.0, 60.5, 64.35, 68.75, 74.8, 80.85, 86.9, 93.5, 101.06, 109.96, 118.85, 127.74, 137.45],  # 第一段
            [56.16, 60.73, 65.3, 71.83, 76.4, 81.63, 88.81, 95.99, 103.17, 111.01, 119.99, 130.55, 141.11, 151.67, 163.18]  # 第二段
        ]

    def on_frame_update(self, target):
        if self.current_frame == self.hit_frames[0]:
            self._apply_attack(target, 0)
        elif self.current_frame == self.hit_frames[1]:
            self._apply_attack(target, 1)

    def _apply_attack(self, target, segment):
        """应用重击伤害"""
        event = ChargedAttackEvent(self.caster, frame=GetCurrentTime())
        EventBus.publish(event)

        damage = Damage(
            damageMultipiler=self.damageMultipiler[segment][self.lv-1],
            element=self.element,
            damageType=DamageType.CHARGED,
            name=f'重击第{segment+1}段'
        )
        damage_event = DamageEvent(self.caster, target, damage, GetCurrentTime())
        EventBus.publish(damage_event)

        event = ChargedAttackEvent(self.caster, frame=GetCurrentTime(), before=False)
        EventBus.publish(event)

class PlungingAttack(PlungingAttackSkill):
    ...

class RainSwordObject(baseObject):
    def __init__(self, character, lifetime=15*60):
        super().__init__("雨帘剑", lifetime)
        self.character = character
        self.last_attack_time = 0
        self.attack_interval = 2*60

    def on_frame_update(self, target):
        current_time = GetCurrentTime()
        if current_time - self.last_attack_time >= self.attack_interval:
            self.last_attack_time = current_time
            damage = Damage(0, ('水', 1), DamageType.SKILL, '雨帘剑')
            target.apply_elemental_aura(damage)

    def on_finish(self, target):
        if self.character.level >= 20:
            heal = Healing(6, HealingType.PASSIVE, '雨帘剑')
            heal_event = HealEvent(
                self.character,
                Team.current_character,
                heal,
                GetCurrentTime()
            )
            EventBus.publish(heal_event)
        super().on_finish(target)

class ElementalSkill(SkillBase):
    def __init__(self, lv, total_frames=65, cd=21*60):
        super().__init__("古华剑·画雨笼山", total_frames, cd, lv, ('水', 0))
        self.hit_frames = [12, 31]
        self.cd_frame = 12
        
        self.damageMultipiler = [
            [168, 180.6, 193.2, 210, 222.6, 235.2, 252, 268.8, 285.6, 302.4, 319.2, 336, 357, 378, 399],  # 第一段
            [191.2, 205.54, 219.88, 239, 253.34, 267.68, 286.8, 305.92, 325.04, 344.16, 363.28, 382.4, 406.3, 430.2, 454.1]  # 第二段
        ]

    def on_frame_update(self, target):
        if self.current_frame == self.hit_frames[0]:
            self._apply_damage(target, 0)
        elif self.current_frame == self.hit_frames[1]:
            self._apply_damage(target, 1)
            summon_energy(5, self.caster,('水',2))
            # 生成雨帘剑
            rain_sword = RainSwordObject(self.caster)
            rain_sword.apply()

    def _apply_damage(self, target, segment):
        """应用技能伤害"""
        damage = Damage(
            damageMultipiler=self.damageMultipiler[segment][self.lv-1],
            element=self.element,
            damageType=DamageType.SKILL,
            name=f'古华剑·画雨笼山第{segment+1}段'
        )
        damage_event = DamageEvent(self.caster, target, damage, GetCurrentTime())
        EventBus.publish(damage_event)

class RainSwordStanceObject(baseObject,EventHandler):
    def __init__(self, character, lv):
        if character.constellation >= 2:
            life_frame = 18*60
        else:
            life_frame = 15*60
        super().__init__("虹剑势", life_frame)
        self.character = character
        self.lv = lv
        self.last_attach_time = 0
        self.last_attack_time = -50
        self.attack_interval = 1*60
        self.damageMultipiler = [
            54.27, 58.34, 62.41, 67.84, 71.91, 75.98, 81.41, 86.84, 92.26, 97.69, 
            103.12, 108.54, 115.33, 122.11, 128.9
        ]
        self.attack_active = False
        if character.constellation >= 6:
            self.sequence = [2,3,5]
        else:
            self.sequence = [2,3]
        self.sequence_pos = 0

    def apply(self):
        super().apply()
        EventBus.subscribe(EventType.BEFORE_NORMAL_ATTACK, self)
        EventBus.subscribe(EventType.AFTER_NORMAL_ATTACK, self)

    def on_finish(self, target):
        super().on_finish(target)
        EventBus.unsubscribe(EventType.BEFORE_NORMAL_ATTACK, self)
        EventBus.unsubscribe(EventType.AFTER_NORMAL_ATTACK, self)

    def on_frame_update(self, target):
        current_time = GetCurrentTime()
        if self.attack_active:
            if current_time - self.last_attack_time >= self.attack_interval:
                self.last_attack_time = current_time
                for _ in range(self.sequence[self.sequence_pos]):
                    damage = Damage(
                        self.damageMultipiler[self.lv-1],
                        ('水', 1),
                        DamageType.BURST,
                        '虹剑势·剑雨'
                    )
                    damage_event = DamageEvent(
                        self.character,
                        target,
                        damage,
                        current_time
                    )
                    EventBus.publish(damage_event)
                self.sequence_pos = (self.sequence_pos+1) % len(self.sequence)
                if self.character.constellation >= 2:
                    ResistanceDebuffEffect('天青现虹', self.character, target, ['水'],15,4*60).apply()
                if self.character.constellation >= 6:
                    summon_energy(1, self.character, ('无', 3),True,True,0)

        if current_time - self.last_attach_time >= 2*60:
            self.last_attach_time = current_time
            damage = Damage(0, ('水', 1), DamageType.SKILL, '雨帘剑')
            target.apply_elemental_aura(damage)

    def handle_event(self, event):
        """处理普通攻击事件"""
        if event.event_type == EventType.BEFORE_NORMAL_ATTACK:
            self.attack_active = True
        elif event.event_type == EventType.AFTER_NORMAL_ATTACK:
            self.attack_active = False

class ElementalBurst(EnergySkill):
    def __init__(self, lv, total_frames=32, cd=20*60):
        super().__init__("古华剑·裁雨留虹", total_frames, cd, lv, ('水', 0))
        self.hit_frame = 18

    def on_frame_update(self, target):
        if self.current_frame == self.hit_frame:
            # 生成虹剑势
            rain_sword_stance = RainSwordStanceObject(self.caster, self.lv)
            rain_sword_stance.apply()

class PassiveSkillEffect_1(TalentEffect):
    def __init__(self):
        super().__init__("生水要诀")

class PassiveSkillEffect_2(TalentEffect):
    def __init__(self):
        super().__init__("虚实工笔")

    def apply(self, character):
        super().apply(character)
        self.character.attributePanel['水元素伤害加成'] += 20

class ConstellationEffect_1(ConstellationEffect):
    def __init__(self):
        super().__init__("重帘留香")

class ConstellationEffect_2(ConstellationEffect):
    def __init__(self):
        super().__init__("天青现虹")

class ConstellationEffect_3(ConstellationEffect):
    def __init__(self):
        super().__init__("织诗成锦")

    def apply(self, character):
        super().apply(character)
        self.character.Burst.lv = min(15, self.character.Burst.lv+3)

class ConstellationEffect_4(ConstellationEffect,EventHandler):
    def __init__(self):
        super().__init__("孤舟斩蛟")

    def apply(self, character):
        super().apply(character)
        EventBus.subscribe(EventType.BEFORE_INDEPENDENT_DAMAGE, self)

    def handle_event(self, event):
        if event.data['character'] != self.character:
            return
        if event.data['damage'].damageType == DamageType.SKILL and event.data['damage'].name[:8] == '古华剑·画雨笼山':
            event.data['damage'].panel['独立伤害加成'] = 150
            event.data['damage'].setDamageData('孤舟斩蛟_独立伤害加成', 150)

class ConstellationEffect_5(ConstellationEffect):
    def __init__(self):
        super().__init__("雨深闭门")

    def apply(self, character):
        super().apply(character)
        self.character.Skill.lv = min(15, self.character.Skill.lv+3)

class ConstellationEffect_6(ConstellationEffect):
    def __init__(self):
        super().__init__("万文集此")

class XingQiu(Liyue):
    ID = 13
    def __init__(self, level=1, skill_params=..., constellation=0):
        super().__init__(XingQiu.ID, level, skill_params, constellation)

    def _init_character(self):
        super()._init_character()
        self.elemental_energy = ElementalEnergy(self, ('水', 80))
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

xingqiu_table = {
    'id': XingQiu.ID,
    'name': '行秋',
    'type': '单手剑',
    'element': '水',
    'rarity': 4,
    'association': '璃月',
    'normalAttack': {'攻击次数': 5},
    'chargedAttack': {},
    # 'plungingAttack': {'攻击距离': ['高空', '低空']},
    'skill': {},
    'burst': {}
}
