from core.context import get_context
from character.character import Character
from core.base_class import (ChargedAttackSkill, ConstellationEffect, ElementalEnergy, 
                            EnergySkill, Infusion, NormalAttackSkill, PlungingAttackSkill, SkillBase, TalentEffect)
from core.BaseObject import baseObject
from core.event import DamageEvent EventHandler, EventType
from core.logger import get_emulation_logger
from core.tool import GetCurrentTime
from core.systems.contract.damage import Damage, DamageType
from core.effect.BaseEffect import DamageBoostEffect

class NormalAttack(NormalAttackSkill,Infusion):
    def __init__(self, lv, cd=0):
        super().__init__(lv, cd)
        Infusion.__init__(self) 
        self.segment_frames = [11,21,34,41]
        self.damageMultipiler = {
            1: [37.6, 40.42, 43.24, 47.0, 49.82, 52.64, 56.4, 60.16, 63.92, 67.68, 71.44, 75.2, 79.9, 84.6, 89.3],  # 第一段攻击1-15级倍率
            2: [36.0, 38.7, 41.4, 45.0, 47.7, 50.4, 54.0, 57.6, 61.2, 64.8, 68.4, 72.0, 76.5, 81.0, 85.5],  # 第二段攻击1-15级倍率
            3: [44.8, 48.16, 51.52, 56.0, 59.36, 62.72, 67.2, 71.68, 76.16, 80.64, 85.12, 89.6, 95.2, 100.8, 106.4],  # 第三段攻击1-15级倍率
            4: [56.16, 60.37, 64.58, 70.2, 74.41, 78.62, 84.24, 89.86, 95.47, 101.09, 106.7, 112.32, 119.34, 126.36, 133.38]  # 第四段攻击1-15级倍率
        }
        self.end_action_frame = 40

    def _apply_segment_effect(self, target, hit_index=0):
        self.element = ('水', self.apply_infusion())
        super()._apply_segment_effect(target, hit_index)

class ChargedAttack(ChargedAttackSkill):
    def __init__(self, lv):
        super().__init__(lv, total_frames=105)
        self.damageMultipiler = [
            149.72, 160.95, 172.18, 187.15, 198.38, 
            209.61, 224.58, 239.55, 254.52, 269.5, 
            285.07, 305.43, 325.79, 346.15, 366.51
        ]
        self.element = ('水', 1)
        self.hit_frame = 66

class PlungingAttack(PlungingAttackSkill):
    ...

class PhantomObject(baseObject, Infusion):
    def __init__(self, character, explosion_damage):
        super().__init__("水中幻愿·虚影", 6*60)  # 6秒持续时间
        Infusion.__init__(self)
        self.character = character
        self.explosion_damage = explosion_damage
        self.last_hit_time = 0
        self.duration_damage_multiplier = [
            32, 34.4, 36.8, 40, 42.4, 44.8, 48, 51.2, 
            54.4, 57.6, 60.8, 64, 68, 72, 76
        ]
        self.explosion_damage_multiplier = [
            132.8, 142.76, 152.72, 166, 175.96, 185.92,
            199.2, 212.48, 225.76, 239.04, 252.32, 265.6,
            282.2, 298.8, 315.4
        ]

    def on_frame_update(self, target):
        if self.current_frame - self.last_hit_time >= 60:
            self.last_hit_time = self.current_frame
            duration_damage = Damage(
                self.duration_damage_multiplier[self.lv-1],
                ('水', self.apply_infusion()),
                DamageType.SKILL,
                '水中幻愿·持续伤害'
            )
            damage_event = DamageEvent(
                self.character, 
                target, 
                duration_damage, 
                get_current_time()
            )
            get_context().event_engine.publish(damage_event)

    def on_finish(self, target):
        super().on_finish(target)
        explosion_damage = Damage(
                self.explosion_damage_multiplier[self.lv-1],
                ('水',1),
                DamageType.SKILL,
                '水中幻愿·爆裂伤害'
            )
        damage_event = DamageEvent(
            self.character,
            target,
            explosion_damage,
            get_current_time()
        )
        get_context().event_engine.publish(damage_event)

class ElementalSkill(SkillBase):
    def __init__(self, lv):
        super().__init__("水中幻愿", 28, 12*60, lv, ('水', 1))
        self.cd_frame = 24

    def start(self, caster):
        if not super().start(caster):
            return False
        get_emulation_logger().log_skill_use(f"💧 {caster.name} 发动水中幻愿")
        return True

    def on_frame_update(self, target):
        if self.current_frame == 0:  # 技能开始时创建虚影
            phantom = PhantomObject(self.caster)
            phantom.apply()

class BubbleObject(baseObject, EventHandler):
    def __init__(self, character, burst_damage, damage_bonus, bonus_duration):
        super().__init__("星命定轨·泡影", 8*60)  # 8秒持续时间
        self.character = character
        self.burst_damage = burst_damage
        self.damage_bonus = damage_bonus
        self.bonus_duration = bonus_duration
        self.is_burst = False

    def apply(self):
        super().apply()
        get_context().event_engine.subscribe(EventType.AFTER_DAMAGE, self)

    def handle_event(self, event):
        if  not self.is_burst:
            # 当泡影目标受到伤害时触发星异效果
            effect = DamageBoostEffect(
                self.character,
                event.data['character'],
                "星异",
                self.damage_bonus,
                self.bonus_duration
            )
            effect.apply()
            
            # 立即破裂泡影并造成额外伤害
            self.is_burst = True
            damage_event = DamageEvent(
                self.character,
                event.data['target'],
                self.burst_damage,
                get_current_time()
            )
            get_context().event_engine.publish(damage_event)
            get_emulation_logger().log_effect("✨ 泡影破裂，触发星异效果")
            self.on_finish(event.data['target'])

    def on_finish(self, target):
        super().on_finish(target)
        get_context().event_engine.unsubscribe(EventType.AFTER_DAMAGE, self)
        if not self.is_burst:
            # 泡影自然结束时造成伤害
            damage_event = DamageEvent(
                self.character,
                target,
                self.burst_damage,
                get_current_time()
            )
            get_context().event_engine.publish(damage_event)
            get_emulation_logger().log_effect(f"✨ {target.name} 的泡影自然破裂")

class ElementalBurst(EnergySkill):
    def __init__(self, lv):
        super().__init__("星命定轨", 121, 15*60, lv, ('水', 1))
        self.burst_damage_multiplier = [
            442.4, 475.58, 508.76, 553, 586.18,
            619.36, 663.6, 707.84, 752.08, 796.32,
            840.56, 884.8, 940.1, 995.4, 1050.7
        ]
        self.damage_bonus = [
            42, 44, 46, 48, 50,
            52, 54, 56, 58, 60,
            60, 60, 60, 60, 60
        ]
        self.bonus_duration = [
            4*60, 4*60, 4*60, 4.5*60, 4.5*60,
            4.5*60, 5*60, 5*60, 5*60, 5*60,
            5*60, 5*60, 5*60, 5*60, 5*60
        ]
        self.hit_frame = 108

    def start(self, caster):
        if not super().start(caster):
            return False
        get_emulation_logger().log_skill_use(f"✨ {caster.name} 发动星命定轨")
        return True

    def on_frame_update(self, target):
        if self.current_frame == self.hit_frame:  # 在108帧创建泡影
            burst_damage = Damage(
                self.burst_damage_multiplier[self.lv-1],
                self.element,
                DamageType.BURST,
                '星命定轨·泡影破裂'
            )
            bubble = BubbleObject(
                self.caster,
                burst_damage,
                self.damage_bonus[self.lv-1],
                self.bonus_duration[self.lv-1]
            )
            bubble.apply()

class PassiveSkillEffect_1(TalentEffect):
    def __init__(self):
        super().__init__('「老太婆来抓我啊！」')

class PassiveSkillEffect_2(TalentEffect):
    def __init__(self):
        super().__init__('「托付于命运吧！」')
    
    def apply(self, character):
        super().apply(character)
        self.ee = self.character.attributePanel['元素充能效率'] * 0.2
        self.character.attributePanel['水元素伤害加成'] += self.ee

    def update(self, target):
        self.character.attributePanel['水元素伤害加成'] -= self.ee
        self.ee = self.character.attributePanel['元素充能效率'] * 0.2
        self.character.attributePanel['水元素伤害加成'] += self.ee

class ConstellationEffect_1(ConstellationEffect):
    def __init__(self):
        super().__init__('沉没的预言')

class ConstellationEffect_2(ConstellationEffect):
    ...

class ConstellationEffect_3(ConstellationEffect):
    ...

class ConstellationEffect_4(ConstellationEffect):
    ...

class ConstellationEffect_5(ConstellationEffect):
    ...

class ConstellationEffect_6(ConstellationEffect):
    ...

# 命座未实现
class Mona(Character):
    ID = 27
    
    def __init__(self, level=1, skill_params=[1,1,1], constellation=0):
        super().__init__(Mona.ID, level, skill_params, constellation)

    def _init_character(self):
        super()._init_character()
        self.elemental_energy = ElementalEnergy(self, ('水', 60))
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

MONA_table = {
    'id': Mona.ID,
    'name': '莫娜',
    'type': '法器',
    'element': '水',
    'rarity': 5,
    'association': '蒙德',
    'normalAttack': {'攻击次数': 4},
    'chargedAttack': {},
    # 'plungingAttack': {'攻击距离': ['高空','低空']},
    'skill': {},
    'burst': {}
}

