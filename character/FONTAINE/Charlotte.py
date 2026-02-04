from character.FONTAINE.fontaine import Fontaine
from character.character import CharacterState
from core.BaseClass import (ChargedAttackSkill, ConstellationEffect, ElementalEnergy, 
                            EnergySkill, NormalAttackSkill, PlungingAttackSkill, SkillBase, TalentEffect,
                            Infusion)
from core.BaseObject import ArkheObject, baseObject
from core.Event import DamageEvent, ElementalSkillEvent, EventBus, EventHandler, EventType, GameEvent, HealEvent, NormalAttackEvent
from core.Logger import get_emulation_logger
from core.team import Team
from core.Tool import GetCurrentTime, summon_energy
from core.calculation.DamageCalculation import Damage, DamageType
from core.calculation.HealingCalculation import Healing, HealingType
from core.effect.BaseEffect import AttackBoostEffect, Effect

# 普通攻击类
class NormalAttack(NormalAttackSkill, Infusion):
    def __init__(self, lv, cd=0):
        super().__init__(lv=lv, cd=cd)
        Infusion.__init__(self)
        # 每段攻击帧数
        self.segment_frames = [13, 35, 41]  # 命中帧
        self.end_action_frame = 43     
        # 伤害倍率表(1-15级)
        self.damageMultipiler = {
            1: [49.85, 53.58, 57.32, 62.31, 66.05, 69.78, 74.77, 79.75, 84.74, 89.72, 94.71, 99.69, 105.92, 112.15, 118.38],  # 一段伤害
            2: [43.38, 46.63, 49.88, 54.22, 57.47, 60.73, 65.06, 69.4, 73.74, 78.08, 82.41, 86.75, 92.17, 97.59, 103.02],  # 二段伤害
            3: [64.6, 69.45, 74.29, 80.75, 85.6, 90.44, 96.9, 103.36, 109.82, 116.28, 122.74, 129.2, 137.28, 145.35, 153.43]   # 三段伤害
        }

    def _apply_segment_effect(self, target):
        damage = Damage(
            damageMultipiler=self.damageMultipiler[self.current_segment+1][self.lv-1],
            element=('冰', self.apply_infusion()),
            damageType=DamageType.NORMAL,
            name=f'普通攻击 第{self.current_segment+1}段'
        )
        
        damage_event = DamageEvent(self.caster, target, damage, GetCurrentTime())
        EventBus.publish(damage_event)

        normal_attack_event = NormalAttackEvent(
            self.caster, 
            frame=GetCurrentTime(), 
            before=False,
            damage=damage,
            segment=self.current_segment+1
        )
        EventBus.publish(normal_attack_event)

# 重击类
class ChargedAttack(ChargedAttackSkill):
    def __init__(self, lv, cd=0):
        super().__init__(lv=lv, total_frames= 79,cd=cd)
        # 命中帧和总帧数
        self.hit_frame = 67
        # 伤害倍率表(1-15级)
        self.damageMultipiler = [
            100.51, 108.05, 115.59, 125.64, 133.18, 140.72, 
            150.77, 160.82, 170.87, 180.92, 190.97, 201.02, 
            213.59, 226.15, 238.72
        ]
        self.element = ('冰', 1)
        # 始基力:芒性相关属性
        self.last_arkhe_time = -360  # 初始设为可触发
        self.arkhe_cooldown = 360  # 6秒冷却(360帧)
        self.arkhe_damage_multipliers = [
            11.17, 12.01, 12.84, 13.96, 14.8, 15.64, 16.75, 17.87, 18.99, 
            20.1, 21.22, 22.34, 23.73, 25.13, 26.52
        ]

    def _apply_attack(self, target):
        current_time = GetCurrentTime()
        # 调用基类方法处理基础重击
        super()._apply_attack(target)

        # 始基力:芒性效果
        if current_time - self.last_arkhe_time >= self.arkhe_cooldown:
            self.last_arkhe_time = current_time
            arkhe_damage = Damage(
                damageMultipiler=self.arkhe_damage_multipliers[self.lv-1],
                element=('冰', 1),
                damageType=DamageType.CHARGED,
                name='灵息之刺'
            )
            arkhe = ArkheObject(
                name='灵息之刺',
                character=self.caster,
                arkhe_type='芒性',
                damage=arkhe_damage,
                life_frame=1  # 立即触发
            )
            arkhe.apply()

# 下落攻击类
class PlungingAttack(PlungingAttackSkill):
    ...

# 元素战技类
class ElementalSkill(SkillBase):
    def __init__(self, lv):
        super().__init__(name="取景·冰点构图法", total_frames=42, cd=12*60, lv=lv,
                        element=('冰', 1))
        self.hold = False
        self.skill_frames = {
            '点按': {'命中帧': 31, '总帧数': 42},
            '长按': {'命中帧': 111, '总帧数': 132}
        }
        
        self.damageMultipiler = {
            '点按伤害': [67.2, 72.24, 77.28, 84, 89.04, 94.08, 100.8, 107.52, 114.24, 120.96, 127.68, 134.4, 142.8, 151.2, 159.6],
            '长按伤害': [139.2, 149.64, 160.08, 174, 184.44, 194.88, 208.8, 222.72, 236.64, 250.56, 264.48, 278.4, 295.8, 313.2, 330.6],
            '瞬时剪影伤害': [39.2, 42.14, 45.08, 49, 51.94, 54.88, 58.8, 62.72, 66.64, 70.56, 74.48, 78.4, 83.3, 88.2, 93.1],
            '聚焦印象伤害': [40.6, 43.65, 46.69, 50.75, 53.8, 56.84, 60.9, 64.96, 69.02, 73.08, 77.14, 81.2, 86.28, 91.35, 96.43]
        }

    def start(self, caster, hold=False):
        if not super().start(caster):
            return False
            
        self.hold = hold
        if hold:
            self._start_hold_skill()
        else:
            self._start_tap_skill()
            
        return True

    def _start_tap_skill(self):
        """点按模式初始化"""
        self.total_frames = self.skill_frames['点按']['总帧数']
        damage = Damage(
            self.damageMultipiler['点按伤害'][self.lv-1],
            element=('冰', 1),
            damageType=DamageType.SKILL,
            name=self.name + ' 点按伤害'
        )
        # 在命中帧触发伤害
        self.scheduled_damage = (damage, self.skill_frames['点按']['命中帧'])
        self.cd = 12*60
        self.cd_frame = 29

    def _start_hold_skill(self):
        """长按模式初始化"""
        self.total_frames = self.skill_frames['长按']['总帧数']
        damage = Damage(
            self.damageMultipiler['长按伤害'][self.lv-1],
            element=('冰', 1),
            damageType=DamageType.SKILL,
            name=self.name + ' 长按伤害'
        )
        # 在命中帧触发伤害
        self.scheduled_damage = (damage, self.skill_frames['长按']['命中帧'])
        self.cd = 18*60
        self.cd_frame = 110

    def on_frame_update(self, target):
        # 处理预定伤害
        if hasattr(self, 'scheduled_damage'):
            damage, trigger_frame = self.scheduled_damage
            if self.current_frame == trigger_frame:
                event = DamageEvent(self.caster, target, damage, GetCurrentTime())
                EventBus.publish(event)
                del self.scheduled_damage
                
                # 应用印记效果
                if self.hold:
                    DamageEffect('聚焦印象', self.caster, target, self.damageMultipiler['聚焦印象伤害'][self.lv-1], 1.5*60, 12*60).apply()
                    summon_energy(3, self.caster, ('冰', 2))
                else:
                    DamageEffect('瞬时剪影', self.caster, target, self.damageMultipiler['瞬时剪影伤害'][self.lv-1], 1.5*60, 6*60).apply()
                    summon_energy(5, self.caster, ('冰', 2))

class DamageEffect(Effect):
    """伤害效果"""
    def __init__(self, name, caster, target, damage_mult, interval, duration):
        super().__init__(caster, duration)
        self.name = name
        self.damage_mult = damage_mult
        self.interval = interval
        self.last_trigger_time = 0
        self.target = target
        self.infusion = Infusion([1,0], 12*60, 6)

    def apply(self):
        exisiting = next((e for e in self.target.effects if isinstance(e, DamageEffect) and e.name == self.name), None)
        if exisiting:
            exisiting.duration = self.duration
            return
        super().apply()
        self.target.add_effect(self)
        get_emulation_logger().log_effect(f"{self.target.name}获得了{self.name}效果")

    def update(self):
        super().update(None)
        if GetCurrentTime() - self.last_trigger_time >= self.interval:
            self.last_trigger_time = GetCurrentTime()
            damage = Damage(
                self.damage_mult,
                element=('冰', self.infusion.apply_infusion()),
                damageType=DamageType.SKILL,
                name=self.name
            )
            EventBus.publish(DamageEvent(self.character, self.target, damage, GetCurrentTime()))
    
class ElementalBurst(EnergySkill):
    def __init__(self, lv):
        super().__init__(name="定格·全方位确证", total_frames=68, cd= 20*60,
                        lv=lv, element=('冰', 1))
        self.hit_frame = 53  # 命中帧
        
        # 技能伤害倍率(1-15级)
        self.damage_multipliers = [
            77.62, 83.44, 89.26, 97.02, 102.84, 108.66, 
            116.42, 124.19, 131.95, 139.71, 147.47, 155.23, 
            164.93, 174.64, 184.34
        ]
        
        # 初始治疗倍率(攻击力% + 固定值)
        self.heal_multipliers = [
            (256.57, 1608.49), (275.82, 1769.36), (295.06, 1943.63), 
            (320.72, 2131.32), (339.96, 2332.41), (359.2, 2546.9), 
            (384.86, 2774.8), (410.52, 3016.11), (436.17, 3270.82), 
            (461.83, 3538.94), (487.49, 3820.46), (513.15, 4115.39), 
            (545.22, 4423.73), (577.29, 4745.47), (609.36, 5080.62)
        ]
        
        # 持续治疗倍率(攻击力% + 固定值)
        self.field_heal_multipliers = [
            (9.22, 57.45), (9.91, 63.19), (10.6, 69.42), 
            (11.52, 76.12), (12.21, 83.3), (12.9, 90.96), 
            (13.82, 99.1), (14.75, 107.72), (15.67, 116.82), 
            (16.59, 126.39), (17.51, 136.45), (18.43, 146.98), 
            (19.58, 157.99), (20.74, 169.48), (21.89, 181.45)
        ]
        
        # 相机伤害倍率(1-15级)
        self.camera_damage_multipliers = [
            6.47, 6.95, 7.44, 8.09, 8.57, 9.06, 
            9.7, 10.35, 11, 11.64, 12.29, 12.94, 
            13.74, 14.55, 15.36
        ]

    def _create_initial_damage(self,target):
        damage = Damage(
            self.damage_multipliers[self.lv-1],
            element=('冰', 2),
            damageType=DamageType.BURST,
            name=self.name + ' 初始伤害'
        )
        EventBus.publish(DamageEvent(self.caster, target, damage, GetCurrentTime()))
        healing = Healing(
            self.heal_multipliers[self.lv-1][0],
            healing_type=HealingType.BURST,
            name=f'{self.name}·施放治疗'
        )
        healing.base_value = '攻击力'
        EventBus.publish(HealEvent(
            source=self.caster,
            target=Team.current_character,  # 治疗当前场上角色
            healing=healing,
            frame=GetCurrentTime()
        ))

    def _create_field(self):
        """创建临事场域"""
        field = FieldObject(
            character=self.caster,
            camera_damage=self.camera_damage_multipliers[self.lv-1],
            field_heal=self.field_heal_multipliers[self.lv-1]
        )
        field.apply()

    def on_frame_update(self, target):
        # 在命中帧触发初始效果
        if self.current_frame == self.hit_frame:
            self._create_initial_damage(target)
            self._create_field()

# 临事场域物体类
class FieldObject(baseObject):
    def __init__(self, character, 
                 camera_damage, field_heal):
        super().__init__('临事场域', life_frame=4*60)
        self.character = character
        self.attack_interval = 0.4 * 60
        self.heal_interval = 0.5 * 60
        self.camera_damage = camera_damage
        self.field_heal = field_heal
        self.last_attack_time = 0
        self.last_heal_time = 0

        self.infusion = Infusion([1,0,0,0], 4*60, 2)

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
            self._apply_heal(self.field_heal, "持续治疗")

    def _apply_camera_attack(self, target):
        """应用相机攻击"""
        damage = Damage(
            self.camera_damage,
            element=('冰', self.infusion.apply_infusion()),
            damageType=DamageType.BURST,
            name=f'{self.name}·温亨廷先生攻击'
        )
        EventBus.publish(DamageEvent(self.character, target, damage, GetCurrentTime()))

    def _apply_heal(self, heal_multiplier, heal_name):
        """应用治疗效果"""
        healing = Healing(
            heal_multiplier,
            healing_type=HealingType.BURST,
            name=f'{self.name}·{heal_name}'
        )
        healing.base_value = '攻击力'
        EventBus.publish(HealEvent(
            source=self.character,
            target=Team.current_character,  # 治疗当前场上角色
            healing=healing,
            frame=GetCurrentTime()
        ))

class PassiveSkillEffect_1(TalentEffect):
    def __init__(self):
        super().__init__("冲击力瞬间")

class PassiveSkillEffect_2(TalentEffect):
    def __init__(self):
        super().__init__("多样性调查")

    def apply(self, character):
        super().apply(character)

    def update(self, target):
        if GetCurrentTime() == 1:
            a,b = 0,0
            for character in Team.team:
                if character.association == '枫丹':
                    a += 1
                else:
                    b += 1
            self.character.attributePanel['治疗加成'] += a*5
            self.character.attributePanel['冰元素伤害加成'] += b*5
            get_emulation_logger().log_object(f'{self.character.name} 多样性调查 生效，获得 {a*5}治疗加成，{b*5}冰元素伤害加成')

class VerificationEffect(Effect):
    def __init__(self, character, current_character):
        super().__init__(character, 6*60)
        self.name = '核实'
        self.current_character = current_character
        self.last_heal_time = 0
        self.heal_interval = 2 * 60
        self.msg =  """每2秒为角色恢复生命值，回复量相当于夏洛蒂攻击力的80%，该效果持续6秒。"""

    def apply(self):
        exisiting = next((e for e in self.character.active_effects if isinstance(e, VerificationEffect)), None)
        if exisiting:
            exisiting.duration = self.duration
            return
        super().apply()
        self.current_character.add_effect(self)
        get_emulation_logger().log_effect(f'{self.character.name}为{self.current_character.name}创建了{self.name}印记')

    def update(self, target):
        super().update(target)

        if GetCurrentTime() - self.last_heal_time >= self.heal_interval:
            self.last_heal_time = GetCurrentTime()
            healing = Healing(
                80,
                healing_type=HealingType.PASSIVE,
                name=f'{self.name}·持续治疗'
            )
            healing.base_value = '攻击力'
            EventBus.publish(HealEvent(
                source=self.character,
                target=self.current_character,
                healing=healing,
                frame=GetCurrentTime()
            ))

class ConstellationEffect_1(ConstellationEffect, EventHandler):
    def __init__(self):
        super().__init__("以核实为约束")

    def apply(self, character):
        super().apply(character)
        EventBus.subscribe(EventType.AFTER_HEAL, self)

    def handle_event(self, event):
        healing = event.data['healing']
        if healing.healing_type == HealingType.BURST and event.data['character'] == self.character:
            VerificationEffect(self.character, event.data['target']).apply()

class ConstellationEffect_2(ConstellationEffect, EventHandler):
    def __init__(self):
        super().__init__("以求真为职守")

    def apply(self, character):
        super().apply(character)
        EventBus.subscribe(EventType.AFTER_SKILL, self)

    def handle_event(self, event):
        if event.data['character'] == self.character:
            AttackBoostEffect(self.character, self.character, '以求真为职守-攻击力提升', 10, 12*60).apply()

class ConstellationEffect_3(ConstellationEffect):
    def __init__(self):
        super().__init__("以独立为先决")

    def apply(self, character):
        super().apply(character)
        self.character.Burst.lv = min(self.character.Burst.lv + 3, 15)

class ConstellationEffect_4(ConstellationEffect, EventHandler):
    def __init__(self):
        super().__init__("以督促为责任")
        self.last_attached_time = 0
        self.attached_interval = 20*60
        self.attached_count = 0
        self.max_attached_count = 5

    def apply(self, character):
        super().apply(character)
        EventBus.subscribe(EventType.BEFORE_DAMAGE_BONUS, self)
    
    def handle_event(self, event):
        if event.data['character'] == self.character:
            damage = event.data['damage']
            effect = next((e for e in damage.target.effects if isinstance(e, DamageEffect)), None)

            if (effect and damage.damageType == DamageType.BURST):
                if self.attached_count < self.max_attached_count:
                    damage.panel['伤害加成'] += 10
                    summon_energy(1, self.character, ('无', 2), True, True, 0)
                    self.attached_count += 1
                    get_emulation_logger().log_effect(f'{self.character.name} 以督促为责任 生效，{damage.target.name}受到的伤害增加10%')
                    if self.attached_count == 1:
                        self.last_attached_time = event.frame
                elif event.frame - self.last_attached_time >= self.attached_interval:
                    self.attached_count = 0

class ConstellationEffect_5(ConstellationEffect):
    def __init__(self):
        super().__init__("以良知为原则")

    def apply(self, character):
        super().apply(character)
        self.character.Skill.lv = min(self.character.Skill.lv + 3, 15)

class ConstellationEffect_6(ConstellationEffect, EventHandler):
    def __init__(self):
        super().__init__("以有趣相关为要义")
        self.last_time = -6*60
        self.interval = 6*60
    
    def apply(self, character):
        super().apply(character)
        EventBus.subscribe(EventType.AFTER_DAMAGE, self)

    def handle_event(self, event):
        if (event.data['character'] == Team.current_character and 
            event.frame - self.last_time >= self.interval):
            damage = event.data['damage']
            effect = next((e for e in damage.target.effects if isinstance(e, DamageEffect) and e.name == '聚焦印象'), None)
            if effect and damage.damageType in [DamageType.NORMAL, DamageType.CHARGED]:
                self.last_time = event.frame
                coordination_damage = Damage(
                    180,
                    ('冰', 1),
                    damageType=DamageType.BURST,
                    name='以有趣相关为要义·协同伤害'
                )
                EventBus.publish(DamageEvent(self.character, damage.target, coordination_damage, GetCurrentTime()))
                healing = Healing(
                    42,
                    HealingType.BURST,
                    name='以有趣相关为要义·治疗'
                )
                healing.base_value = '攻击力'
                EventBus.publish(HealEvent(self.character, Team.current_character, healing, GetCurrentTime()))

class CHARLOTTE(Fontaine):
    ID = 74
    def __init__(self, level=1, skill_params=None, constellation=0):
        super().__init__(CHARLOTTE.ID, level, skill_params, constellation)
        
    def _init_character(self):
        super()._init_character()
        self.arkhe = "芒性"
        self.elemental_energy = ElementalEnergy(self, ('冰', 80))
        self.NormalAttack = NormalAttack(self.skill_params[0])
        self.ChargedAttack = ChargedAttack(self.skill_params[0])
        # self.PlungingAttack = PlungingAttack()
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

    def _elemental_skill_impl(self, hold=False):
        if self.Skill.start(self, hold):
            self._append_state(CharacterState.SKILL)
            skillEvent = ElementalSkillEvent(self,GetCurrentTime())
            EventBus.publish(skillEvent)
    
    def elemental_skill(self, hold=False):
        self._elemental_skill_impl(hold)

# 角色表
Charlotte_table = {
    'id': CHARLOTTE.ID,
    'name': '夏洛蒂',
    'type': '法器',
    'element': '冰',
    'rarity': 4,
    'association': '枫丹',
    'normalAttack': {'攻击次数': 3},
    'chargedAttack': {},
    # 'plungingAttack': {'攻击距离': ['高空', '低空']},
    'skill': {'释放时间':['长按','点按']},
    'burst': {}
}
