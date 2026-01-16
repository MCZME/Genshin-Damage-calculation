from character.INAZUMA.inazuma import Inazuma
from character.character import CharacterState
from core.BaseClass import ChargedAttackSkill, ConstellationEffect, ElementalEnergy, EnergySkill, NormalAttackSkill, PlungingAttackSkill, SkillBase, TalentEffect
from core.BaseObject import baseObject
from core.calculation.DamageCalculation import Damage, DamageType
from core.effect.BaseEffect import Effect, ElementalDamageBoostEffect, ElementalInfusionEffect
from core.Event import DamageEvent, ElementalSkillEvent, EventBus, EventHandler, EventType
from core.Logger import get_emulation_logger
from core.Team import Team
from core.Tool import GetCurrentTime, summon_energy

class NormalAttack(NormalAttackSkill):
    def __init__(self, lv):
        super().__init__(lv)
        self.segment_frames = [13, 14, 30, 29, 42]
        self.end_action_frame = 53
        self.damageMultiplier = {
            1: [44.98, 48.64, 52.3, 57.53, 61.19, 65.38, 71.13, 76.88, 82.63, 88.91, 96.1, 104.56, 113.02, 121.47, 130.7],
            2: [45.24, 48.92, 52.6, 57.86, 61.54, 65.75, 71.54, 77.32, 83.11, 89.42, 96.65, 105.16, 113.66, 122.17, 131.45],
            3: [25.8 + 30.96, 27.9 + 33.48, 30 + 36, 33 + 39.6, 35.1 + 42.12, 37.5 + 45, 40.8 + 48.96, 44.1 + 52.92, 
                47.4 + 56.88, 51 + 61.2, 55.13 + 66.15, 59.98 + 71.97, 64.83 + 77.79, 69.68 + 83.61, 74.97 + 89.96],
            4: [60.72, 65.66, 70.6, 77.66, 82.6, 88.25, 96.02, 103.78, 111.55, 120.02, 129.73, 141.14, 152.56, 163.98, 176.43],
            5: [25.37*3, 27.44*3, 29.5*3, 32.45*3, 34.52*3, 36.88*3, 40.12*3, 43.37*3, 46.61*3, 50.15*3, 54.21*3, 58.98*3, 
                63.75*3, 68.52*3, 73.72*3]
        }

class ChargedAttack(ChargedAttackSkill):
    def __init__(self, lv):
        super().__init__(lv, total_frames=30)
        self.hit_frame = 20
        self.damageMultiplier = [
            43 + 74.65, 46.5 + 80.72, 50 + 86.8, 55 + 95.48, 58.5 + 101.56,
            62.5 + 108.5, 68 + 118.05, 73.5 + 127.6, 79 + 137.14, 85 + 147.56,
            91.88 + 159.5, 99.96 + 173.53, 108.05 + 187.57, 116.13 + 201.6, 124.95 + 216.91
        ]

class PlungingAttack(PlungingAttackSkill):
    def __init__(self, lv):
        super().__init__(lv, total_frames=60)
        self.damageMultiplier = {
            '下坠期间伤害': [81.83, 88.49, 95.16, 104.67, 111.33, 118.94, 129.41, 139.88, 150.35, 161.76, 173.18, 184.6, 196.02, 207.44, 218.86],
            '低空坠地冲击伤害': [163.63, 176.95, 190.27, 209.3, 222.62, 237.84, 258.77, 279.7, 300.63, 323.46, 346.29, 369.12, 391.96, 414.79, 437.62],
            '高空坠地冲击伤害': [204.39, 221.02, 237.66, 261.42, 278.06, 297.07, 323.21, 349.36, 375.5, 404.02, 432.54, 461.06, 489.57, 518.09, 546.61]
        }
        self.hit_frame = 40

    def _apply_during_damage(self, target):
        luanlan_effect = next((e for e in self.caster.active_effects if isinstance(e, LuanlanEffect)), None)
        if luanlan_effect:
            self.element = ('风', 0)
        super()._apply_during_damage(target)

    def _apply_impact_damage(self, target):
        """坠地冲击伤害"""
        luanlan_effect = next((e for e in self.caster.active_effects if isinstance(e, LuanlanEffect)), None)
        damage_type_key = '高空坠地冲击伤害' if self.height_type == '高空' else '低空坠地冲击伤害'
        
        # 检查是否有元素转化的乱岚拨止效果
        if luanlan_effect and luanlan_effect.swirled_element:
            # 附加200%攻击力的对应元素伤害
            extra_damage = Damage(
                200,
                (luanlan_effect.swirled_element,1),
                DamageType.PLUNGING,
                f'下落攻击·乱岚拨止-{self.height_type}元素附加'
            )
            EventBus.publish(DamageEvent(self.caster, target, extra_damage, GetCurrentTime()))

        # 基础下落攻击伤害
        damage = Damage(
            self.damageMultiplier[damage_type_key][self.lv - 1],
            ('风', 1) if luanlan_effect else ('物理',0),
            DamageType.PLUNGING,
            f'下落攻击·乱岚拨止-{self.height_type}' if luanlan_effect else f'下落攻击-{self.height_type}'
        )
        EventBus.publish(DamageEvent(self.caster, target, damage, GetCurrentTime()))
    
class ElementalSkill(SkillBase):
    def __init__(self, lv):
        super().__init__(name="千早振", total_frames=24, cd=6*60, lv=lv,
                        element=('风', 1), interruptible=True)
        self.hold = False  # 长按状态标识
        self.skill_frames = {
            '点按': [10, 24],
            '长按': [33, 58] 
        }
        
        # 伤害倍率参数
        self.damageMultiplier = {
            '点按伤害': [192, 206.4, 220.8, 240, 254.4, 268.8, 288, 307.2, 
                      326.4, 345.6, 364.8, 384, 408, 432, 456],
            '长按伤害': [260.8, 280.36, 299.92, 326, 345.56, 365.12, 391.2, 
                      417.28, 443.36, 469.44, 495.52, 521.6, 554.2, 586.8, 619.4]
        }

    def start(self, caster, hold=False):
        if not super().start(caster):
            return False
            
        self.hold = hold
        if hold:
            self._start_hold_skill()
        else:
            self._start_tap_skill()
        if caster.constellation >=1:
            self.cd = 0.9 * self.cd
        self._apply_luanlan_effect()
        return True

    def _start_tap_skill(self):
        """点按模式初始化"""
        self.total_frames = self.skill_frames['点按'][1]
        self.cd = 6 * 60
        self.cd_frame = 8
        self.v = 4.16
        self.hit_frame = self.skill_frames['点按'][0]
        self.element = ('风',1)
        self.energy_num = 3
        if self.caster.constellation >= 4:
            summon_energy(1, self.caster,('无',3),True,True,0)

    def _start_hold_skill(self):
        """长按模式初始化"""
        self.total_frames = self.skill_frames['长按'][1] 
        self.cd = 9 * 60
        self.cd_frame = 31
        self.v = 3.41
        self.hit_frame = self.skill_frames['长按'][0]
        self.element = ('风',2)
        self.energy_num = 4
        if self.caster.constellation >= 4:
            summon_energy(1, self.caster,('无',4),True,True,0)

    def _apply_luanlan_effect(self):
        """应用乱岚拨止效果"""
        if not self.caster:
            return
            
        effect = LuanlanEffect(
            caster=self.caster,
            duration=10 * 60,
        )
        effect.apply()

    def on_frame_update(self, target):
        if self.current_frame == self.hit_frame:
            name = '长按伤害' if self.hold else '点按伤害'
            damage = Damage(
                self.damageMultiplier[name][self.lv - 1],
                self.element,
                DamageType.SKILL,
                f'千早振-{name}'
            )
            EventBus.publish(DamageEvent(self.caster, target, damage, GetCurrentTime()))
            summon_energy(self.energy_num, self.caster,('风',2))
            
        self.caster.height += self.v
        self.caster.movement += self.v

    def on_finish(self):
        super().on_finish()
        self.caster._append_state(CharacterState.FALL)

    def on_interrupt(self):
        super().on_interrupt()

class LuanlanEffect(Effect,EventHandler):
    """乱岚拨止效果"""
    def __init__(self, caster, duration):
        super().__init__(caster, duration)
        self.name = "乱岚拨止"
        self.swirled_element = None  # 记录转化元素
        self.element_applied = False  # 标记是否已应用元素转化
        self.msg = f"""
        <p><span style="color: #faf8f0; font-size: 14pt;">{self.character.name} - {self.name}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">下落攻击造成的伤害将转化为风元素伤害</span></p>
        """
        
    def apply(self):
        super().apply()
        get_emulation_logger().log_effect(f"🍃 {self.character.name}获得乱岚拨止效果！")
        self.character.add_effect(self)

        EventBus.subscribe(EventType.AFTER_FALLING, self)
        if self.character.level >= 20:
            EventBus.subscribe(EventType.BEFORE_SWIRL, self)
        
    def remove(self):
        get_emulation_logger().log_effect("🍃 乱岚拨止效果消失")
        EventBus.unsubscribe(EventType.AFTER_FALLING, self)
        if self.character.level >= 20:
            EventBus.unsubscribe(EventType.BEFORE_SWIRL, self)
        self.character.falling_speed = 5
        super().remove()

    def update(self, target):
        super().update(target)
        if self.duration >= self.max_duration - 20:
            self.character.falling_speed = 1
        else:
            self.character.falling_speed = 2

    def handle_event(self, event):
        if event.event_type == EventType.AFTER_FALLING and event.data['character'] == self.character:
            self.remove()
            
        elif (event.event_type == EventType.BEFORE_SWIRL and 
              not self.element_applied and
              event.data['elementalReaction'].source == self.character and
              event.data['elementalReaction'].damage.damageType == DamageType.SKILL):
            # 处理元素转化
            element = event.data['elementalReaction'].target_element
            if element[0] in ['水', '火', '冰', '雷']:
                self.swirled_element = element
                self.element_applied = True
                get_emulation_logger().log_effect(f"🌀 乱岚拨止转化{self.swirled_element[0]}元素!")

class ElementalBurst(EnergySkill):
    def __init__(self, lv):
        super().__init__(name="万叶之一刀", total_frames=92, cd=15*60, lv=lv,
                        element=('风', 2), interruptible=False)
        self.hit_frame = 82
        self.slash_damage = [262.4, 282.08, 301.76, 328, 347.68, 367.36, 
                           393.6, 419.84, 446.08, 472.32, 498.56, 524.8, 
                           557.6, 590.4, 623.2]
        self.dot_damage = [120, 129, 138, 150, 159, 168, 180, 192, 204, 
                          216, 228, 240, 255, 270, 285]
        self.swirl_damage = [36, 38.7, 41.4, 45, 47.7, 50.4, 54, 57.6, 
                            61.2, 64.8, 68.4, 72, 76.5, 81, 85.5]
        self.scheduled_damage = None

    def start(self, caster):
        if not super().start(caster):
            return False
            
        field = KazuhaSlashField(
            character=self.caster,
            duration=8*60,
            dot_damage=self.dot_damage[self.lv-1],
            swirl_damage=self.swirl_damage[self.lv-1]
        )
        field.apply()
        
        return True

    def on_frame_update(self, target):
        if self.current_frame == self.hit_frame:
            damage = Damage(
                self.slash_damage[self.lv-1],
                element=self.element,
                damageType=DamageType.BURST,
                name=self.name + ' 斩击伤害'
            )
            EventBus.publish(DamageEvent(self.caster, target, damage, GetCurrentTime()))

class KazuhaSlashField(baseObject, EventHandler):
    """流风秋野领域"""
    def __init__(self, character, duration, dot_damage, swirl_damage):
        super().__init__("流风秋野", duration)
        self.character = character
        self.dot_damage = dot_damage
        self.swirl_damage = swirl_damage
        self.swirled_element = None
        self.is_swirled = False
        self.dot_interval = 2*60
        self.last_dot_time = 29
        self.current_character = None
        
    def apply(self):
        super().apply()
        EventBus.subscribe(EventType.AFTER_DAMAGE, self)
        if self.character.constellation >= 2:
            EventBus.subscribe(EventType.AFTER_CHARACTER_SWITCH, self)
            self.character.attributePanel['元素精通'] += 200
            self.current_character = self.character
        
    def on_frame_update(self, target):
        if self.current_frame - self.last_dot_time >= self.dot_interval:
            self.last_dot_time = self.current_frame
            damage = Damage(
                self.dot_damage,
                element=('风', 1),
                damageType=DamageType.BURST,
                name="流风秋野-持续伤害"
            )
            EventBus.publish(DamageEvent(self.character, target, damage, GetCurrentTime()))
            if self.swirled_element:
                # 附加元素转化伤害
                swirl_damage = Damage(
                    self.swirl_damage,
                    element=(self.swirled_element, 1),
                    damageType=DamageType.BURST,
                    name=f"流风秋野-{self.swirled_element}附加伤害"
                )
                EventBus.publish(DamageEvent(self.character, target, swirl_damage, GetCurrentTime()))
    
    def handle_event(self, event):
        """处理元素转化"""
        if (event.event_type == EventType.AFTER_DAMAGE and not self.swirled_element and
            event.data['character'] == self.character and
            event.data['damage'].name == '万叶之一刀 斩击伤害' and
            not self.is_swirled):
            if event.data['damage'].reaction_data:
                self.swirled_element = event.data['damage'].reaction_data['目标元素']
                self.is_swirled = True
                get_emulation_logger().log_effect(f"🌀 流风秋野转化为{self.swirled_element}元素!")
        elif event.event_type == EventType.AFTER_CHARACTER_SWITCH:
            if event.data['new_character'] != self.character:
                self.current_character = event.data['new_character']
                self.current_character.attributePanel['元素精通'] += 200
                if event.data['old_character'] != self.character:
                    event.data['old_character'].attributePanel['元素精通'] -= 200
    
    def on_finish(self, target):
        super().on_finish(target)
        EventBus.unsubscribe(EventType.AFTER_DAMAGE, self)
        if self.character.constellation >= 2:
            EventBus.unsubscribe(EventType.AFTER_CHARACTER_SWITCH, self)
            self.character.attributePanel['元素精通'] -= 200
            if self.current_character != self.character:
                self.current_character.attributePanel['元素精通'] -= 200

class PassiveSkillEffect_1(TalentEffect):
    """相闻之剑法"""
    def __init__(self):
        super().__init__('相闻之剑法')

class PassiveSkillEffect_2(TalentEffect, EventHandler):
    """风物之诗咏"""
    def __init__(self):
        super().__init__('风物之诗咏')
        
    def apply(self,character):
        super().apply(character)
        EventBus.subscribe(EventType.AFTER_SWIRL, self)
        
    def handle_event(self, event):
        """处理扩散反应事件"""
        if (event.event_type == EventType.AFTER_SWIRL and 
            event.data['elementalReaction'].source == self.character):
            
            swirled_element = event.data['elementalReaction'].target_element
            
            bonus = self.character.attributePanel['元素精通'] * 0.04
            
            for teammate in Team.team:
                effect = ElementalDamageBonusEffect(
                    character=self.character,
                    target=teammate,
                    element=swirled_element,
                    bonus=bonus,
                    duration=8*60
                )
                effect.apply()

class ElementalDamageBonusEffect(ElementalDamageBoostEffect):
    """元素伤害加成效果"""
    def __init__(self, character,target, element, bonus, duration):
        super().__init__(character, target, '风物之诗咏-'+element, element, bonus, duration)

class ConstellationEffect_1(ConstellationEffect,EventHandler):
    """千山红遍"""
    def __init__(self):
        super().__init__('千山红遍')

    def apply(self, character):
        super().apply(character)
        EventBus.subscribe(EventType.AFTER_BURST, self)

    def handle_event(self, event):
        if (event.event_type == EventType.AFTER_BURST and event.data['character'] == self.character):
            self.character.Skill.cd_timer = 0

class ConstellationEffect_2(ConstellationEffect):
    """山岚残芯"""
    def __init__(self):
        super().__init__('山岚残芯')

    def apply(self, character):
        super().apply(character)

class ConstellationEffect_3(ConstellationEffect):
    """枫袖奇谭"""
    def __init__(self):
        super().__init__('枫袖奇谭')

    def apply(self, character):
        super().apply(character)
        self.character.Skill.lv = min(15, self.character.Skill.lv+3)

class ConstellationEffect_4(ConstellationEffect):
    """大空幻法
        todo:处于滑翔状态下时，每秒为枫原万叶恢复2点元素能量
    """
    def __init__(self):
        super().__init__('大空幻法')

    def apply(self, character):
        super().apply(character)

class ConstellationEffect_5(ConstellationEffect):
    """万世之集"""
    def __init__(self):
        super().__init__('万世之集')
    
    def apply(self, character):
        super().apply(character)
        self.character.Burst.lv = min(15, self.character.Burst.lv+3)

class ConstellationEffect_6(ConstellationEffect, EventHandler):
    """血赤叶红"""
    def __init__(self):
        super().__init__('血赤叶红')

    def apply(self, character):
        super().apply(character)
        EventBus.subscribe(EventType.AFTER_SKILL, self)
        EventBus.subscribe(EventType.AFTER_BURST, self)

    def handle_event(self, event):
        if (event.event_type in [EventType.AFTER_SKILL, EventType.AFTER_BURST] and 
            event.data['character'] == self.character):
            CrimsonMomijiEffect(self.character).apply()

class CrimsonMomijiEffect(ElementalInfusionEffect,EventHandler):
    """血赤叶红效果"""
    def __init__(self, character):
        super().__init__(character, character, '血赤叶红-风元素附魔', '风', 5*60, True)

    def apply(self):
        super().apply()
        EventBus.subscribe(EventType.BEFORE_DAMAGE_BONUS, self)

    def remove(self):
        super().remove()
        EventBus.unsubscribe(EventType.BEFORE_DAMAGE_BONUS, self)

    def handle_event(self, event):
        if (event.event_type == EventType.BEFORE_DAMAGE_BONUS and 
            event.data['character'] == self.character and
            event.data['damage'].damageType in [DamageType.NORMAL,DamageType.CHARGED,DamageType.PLUNGING]):
            event.data['damage'].panel['伤害加成'] += 0.2 * self.character.attributePanel['元素精通']
            event.data['damage'].setDamageData('血赤叶红_伤害加成', 0.2 * self.character.attributePanel['元素精通'])

class KaedeharaKazuha(Inazuma):
    ID = 33
    def __init__(self, level=1, skill_params=..., constellation=0):
        super().__init__(KaedeharaKazuha.ID, level, skill_params, constellation)

    def _init_character(self):
        super()._init_character()
        self.elemental_energy = ElementalEnergy(self,('风',60))
        self.NormalAttack = NormalAttack(self.skill_params[0])
        self.ChargedAttack = ChargedAttack(self.skill_params[0])
        self.PlungingAttack = PlungingAttack(self.skill_params[0])
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

    def elemental_skill(self,hold):
        self._elemental_skill_impl(hold)
    
    def _elemental_skill_impl(self,hold):
        if self.Skill.start(self, hold):
            self._append_state(CharacterState.SKILL)
            skillEvent = ElementalSkillEvent(self,GetCurrentTime())
            EventBus.publish(skillEvent)

Kaedehara_Kazuha_table = {
    'id': KaedeharaKazuha.ID,
    'name': '枫原万叶',
    'type': '单手剑',
    'element': '风',
    'rarity': 5,
    'association':'稻妻',
    'normalAttack': {'攻击次数': 5},
    'chargedAttack': {},
    'plungingAttack': {'攻击距离':['高空', '低空']},
    'skill': {'释放时间':['长按','点按']},
    'burst': {}
}
