from character.character import Character, CharacterState

from core.BaseClass import (ChargedAttackSkill, ConstellationEffect, ElementalEnergy, 
                            EnergySkill, Infusion, NormalAttackSkill, PlungingAttackSkill, SkillBase, TalentEffect)
from core.BaseObject import baseObject
from core.Event import ChargedAttackEvent, DamageEvent, ElementalSkillEvent, EventBus, EventHandler, EventType, NormalAttackEvent
from core.Logger import get_emulation_logger
from core.Team import Team
from core.Tool import GetCurrentTime
from core.calculation.DamageCalculation import Damage, DamageType
from core.effect.BaseEffect import Effect

class RiftObject(baseObject):
    """虚境裂隙对象"""
    def __init__(self):
        super().__init__("虚境裂隙", 20*60)
        self.repeatable = True

    def on_frame_update(self, target):
        ...
        
class NormalAttack(NormalAttackSkill,Infusion):
    def __init__(self, lv):
        super().__init__(lv)
        Infusion.__init__(self)
        # 普通模式配置
        self.normal_damage = {
            1:[54.52, 58.96, 63.4, 69.74, 74.18, 79.25, 86.22, 93.2, 100.17, 107.78, 115.39, 123, 130.6, 138.21, 145.82],
            2:[49.79, 53.85, 57.9, 63.69, 67.74, 72.38, 78.74, 85.11, 91.48, 98.43, 105.38, 112.33, 119.27, 126.22, 133.17],
            3:[[32.42, 35.06, 37.7, 41.47, 44.11, 47.13, 51.27, 55.42, 59.57, 64.09, 68.61, 73.14, 77.66, 82.19, 86.71],
             [32.42, 35.06, 37.7, 41.47, 44.11, 47.13, 51.27, 55.42, 59.57, 64.09, 68.61, 73.14, 77.66, 82.19, 86.71]],
            4:[60.8, 65.75, 70.7, 77.77, 82.72, 88.38, 96.15, 103.93, 111.71, 120.19, 128.67, 137.16, 145.64, 154.13, 162.61],
            5:[82.9, 89.65, 96.4, 106.04, 112.79, 120.5, 131.1, 141.71, 152.31, 163.88, 175.45, 187.02, 198.58, 210.15, 221.72]
        }
        self.normal_frames = [10, 10, [12, 14], 12, 15]
        self.normal_end_action_frame = 20
        
        # 七相一闪模式配置
        self.lunar_damage = {
            1:[132.82, 143.64, 154.45, 169.89, 180.7, 193.06, 210.05, 227.04, 244.03, 262.56, 281.09, 299.63, 318.16, 336.69, 355.23],
            2:[119.8, 129.55, 139.3, 153.23, 162.98, 174.13, 189.45, 204.77, 220.1, 236.81, 253.53, 270.25, 286.96, 303.68, 320.39],
            3:[[75.72, 81.89, 88.05, 96.86, 103.02, 110.06, 119.75, 129.43, 139.12, 149.69, 160.25, 170.82, 181.38, 191.95, 202.52],
             [75.72, 81.89, 88.05, 96.86, 103.02, 110.06, 119.75, 129.43, 139.12, 149.69, 160.25, 170.82, 181.38, 191.95, 202.52]],
            4:[[80.54, 87.09, 93.65, 103.02, 109.57, 117.06, 127.36, 137.67, 147.97, 159.21, 170.44, 181.68, 192.92, 204.16, 215.4],
             [80.54, 87.09, 93.65, 103.02, 109.57, 117.06, 127.36, 137.67, 147.97, 159.21, 170.44, 181.68, 192.92, 204.16, 215.4]],
            5:[196.62, 212.63, 228.63, 251.5, 267.5, 285.79, 310.94, 336.09, 361.24, 388.68, 416.11, 443.55, 470.98, 498.42, 525.86]
        }
        self.lunar_frames = [12, 12, [14, 16], [14, 16], 18]
        self.lunar_end_action_frame = 20

    def _reset_config(self):
        """根据当前模式重置配置"""
        if self.caster.mode == "正常模式":
            self.damageMultipiler = self.normal_damage
            self.segment_frames = self.normal_frames
            self.end_action_frame = self.normal_end_action_frame
            self.lv_param = self.lv
        else:  # lunar模式
            self.damageMultipiler = self.lunar_damage
            self.segment_frames = self.lunar_frames
            self.end_action_frame = self.lunar_end_action_frame
            self.lv_param = self.caster.Skill.lv

    def start(self, caster, n):

        self.caster = caster
        self._reset_config()
        self.current_mode = self.caster.mode

        return super().start(caster, n)
    
    def _apply_segment_effect(self,target, hit_index=0):
        segment = self.current_segment + 1
        # 获取伤害倍率（支持多段配置）
        multiplier = self.damageMultipiler[segment]
        if isinstance(multiplier[0], list):
            multiplier = multiplier[hit_index][self.lv_param-1]
        else:
            multiplier = multiplier[self.lv_param-1]
            
        if self.current_mode == "七相一闪":
            element = ('冰', self.apply_infusion())
            name = f'七相一闪 {segment}-{hit_index+1}'
        else:
            element = self.element
            name = f'普通攻击 {segment}-{hit_index+1}'

        # 发布伤害事件
        damage = Damage(multiplier, element, DamageType.NORMAL, name)
        damage_event = DamageEvent(self.caster,target,damage, frame=GetCurrentTime())
        EventBus.publish(damage_event)

        # 发布普通攻击事件（后段）
        normal_attack_event = NormalAttackEvent(self.caster, frame=GetCurrentTime(),before=False,
                                                damage=damage,segment=self.current_segment+1)
        EventBus.publish(normal_attack_event)

class ChargedAttack(ChargedAttackSkill):
    def __init__(self, lv):
        super().__init__(lv, total_frames=25, cd=0)
        
        # 普通模式配置
        self.normal_damage = [
            66.82, 72.26, 77.7, 85.47, 90.91, 
            97.13, 105.67, 114.22, 122.77, 132.09,
            141.41, 150.74, 160.06, 169.39, 178.71
        ]
        self.normal_hit_frame = [9,18]
        self.normal_total_frames = 25
        
        # 七相一闪模式配置
        self.lunar_damage = [
            44.55, 48.17, 51.8, 56.98, 60.61,
            64.75, 70.45, 76.15, 81.84, 88.06,
            94.28, 100.49, 106.71, 112.92, 119.14
        ]
        self.lunar_hit_frame = [9,18,20]
        self.lunar_total_frames = 30
        
        self.current_mode = None

    def _reset_config(self):
        """根据当前模式重置配置"""
        if self.caster.mode == "正常模式":
            self.damageMultipiler = self.normal_damage
            self.hit_frame  = self.normal_hit_frame
            self.total_frames = self.normal_total_frames
            self.element = ('物理', 0)
            self.lv_param = self.lv
        else:  # 七相一闪模式
            self.damageMultipiler = self.lunar_damage
            self.hit_frame  = self.lunar_hit_frame
            self.total_frames = self.lunar_total_frames
            self.element = ('冰', 1)
            self.lv_param = self.caster.Skill.lv

    def start(self, caster):
        if not super().start(caster):
            return False
            
        self._reset_config()
        self.current_mode = self.caster.mode

        return True
    
    def on_frame_update(self, target):
        if self.current_frame in self.hit_frame:
            self._apply_attack(target)

    def _apply_attack(self, target):
        """应用重击伤害"""
        event = ChargedAttackEvent(self.caster, frame=GetCurrentTime())
        EventBus.publish(event)

        damage = Damage(
            self.damageMultipiler[self.lv_param-1],
            self.element,
            DamageType.CHARGED,
            f'重击' if self.current_mode == "正常模式" else '七相一闪重击'
        )
        damage_event = DamageEvent(self.caster, target, damage, GetCurrentTime())
        EventBus.publish(damage_event)

        if self.caster.level >= 20 and self.current_frame == self.hit_frame[0] and self.current_mode == '七相一闪':
            self.caster.get_rift_count()

        event = ChargedAttackEvent(self.caster, frame=GetCurrentTime(), before=False)
        EventBus.publish(event)

class PlungingAttack(PlungingAttackSkill):
    ...

class ElementalSkill(SkillBase):
    def __init__(self, lv):
        super().__init__(
            name="极恶技·闪",
            total_frames=30,  # 总帧数
            cd=9*60,         # 9秒冷却
            lv=lv,
            element=('冰', 1),
            interruptible=True
        )
        self.mode_duration = 12.5 * 60  # 七相一闪模式持续时间(帧)
        self.serpent_gain = 45  # 蛇之狡谋获取量
        
    def start(self, caster, hold=False):
        if not super().start(caster):
            return False
            
        # 获取蛇之狡谋
        caster.current_serpent_subtlety = min(
            caster.max_serpent_subtlety,
            caster.current_serpent_subtlety + self.serpent_gain
        )
        
        # 点按切换模式
        if not hold:
            caster.mode = "七相一闪"
            # 设置模式持续时间
            caster.mode_timer = self.mode_duration
        else:
            self.caster.get_rift_count()
            
        get_emulation_logger().log_skill_use(
            f"❄️ {caster.name} 使用{'长按' if hold else '点按'}极恶技·闪，" 
            f"获得{self.serpent_gain}点蛇之狡谋"
        )
        return True
        
    def on_frame_update(self, target):
        ...

    def on_finish(self):
        super().on_finish()
        get_emulation_logger().log_skill_use("❄️ 极恶技·闪完成")

class ElementalBurst(EnergySkill):
    def __init__(self, lv):
        super().__init__(
            name="极恶技·灭", 
            total_frames=60,  # 总帧数
            cd=15*60,        # 15秒冷却
            lv=lv,
            element=('冰', 1),
            interruptible=False
        )
        self.hit_frames = [15, 25, 35, 45, 55]  # 5段伤害帧
        self.final_hit_frame = 58  # 最终伤害帧
        self.min_serpent_cost = 50  # 最低消耗
        self.max_bonus_serpent = 12  # 最大加成点数
        
        # 技能伤害配置
        self.base_damage = [
            138.12, 148.48, 158.84, 172.65, 183.01,
            193.37, 207.18, 220.99, 234.8, 248.62,
            262.43, 276.24, 293.51, 310.77, 328.04
        ]
        self.final_damage = [
            230.2, 247.47, 264.73, 287.75, 305.02,
            322.28, 345.3, 368.32, 391.34, 414.36,
            437.38, 460.4, 489.18, 517.95, 546.73
        ]
        self.serpent_bonus = [
            16.63, 17.87, 19.12, 20.78, 22.03,
            23.28, 24.94, 26.6, 28.26, 29.93,
            31.59, 33.25, 35.33, 37.41, 39.49
        ]
    def start(self, caster):
        # 检查蛇之狡谋是否足够
        if caster.current_serpent_subtlety < self.min_serpent_cost:
            get_emulation_logger().log_error(f"{caster.name} 蛇之狡谋不足，无法释放元素爆发")
            return False
            
        # 计算额外加成点数(不超过max_bonus_serpent)
        extra_serpent = min(
            caster.current_serpent_subtlety - self.min_serpent_cost,
            self.max_bonus_serpent
        )
        self.bonus_multiplier = extra_serpent * self.serpent_bonus[self.lv-1]
        
        # 消耗所有蛇之狡谋
        caster.current_serpent_subtlety = 0
        
        if not super().start(caster):
            return False
            
        get_emulation_logger().log_skill_use(
            f"❄️ {caster.name} 释放极恶技·灭，"
            f"获得{self.bonus_multiplier*100:.1f}%伤害加成"
        )
        return True

    def on_frame_update(self, target):
        # 触发5段基础伤害
        if self.current_frame in self.hit_frames:
            damage = Damage(
                self.base_damage[self.lv-1] + self.bonus_multiplier,
                self.element,
                DamageType.BURST,
                f'极恶技·灭-斩击{self.hit_frames.index(self.current_frame)+1}'
            )
            damage.setDamageData('蛇之狡谋_加成', self.bonus_multiplier)
            EventBus.publish(DamageEvent(self.caster, target, damage, GetCurrentTime()))
        
        # 触发最终伤害
        if self.current_frame == self.final_hit_frame:
            damage = Damage(
                self.final_damage[self.lv-1] + self.bonus_multiplier,
                self.element,
                DamageType.BURST,
                '极恶技·灭-终结'
            )
            damage.setDamageData('蛇之狡谋_加成', self.bonus_multiplier)
            EventBus.publish(DamageEvent(self.caster, target, damage, GetCurrentTime()))

    def on_finish(self):
        super().on_finish()
        get_emulation_logger().log_skill_use("❄️ 极恶技·灭完成")

class DecayEffect(Effect, EventHandler):
    """凋尽效果"""
    def __init__(self, character, lv):
        super().__init__(character, 10)
        self.name = "凋尽"
        self.lv = lv
        self.trigger_count = 0
        self.max_triggers = 10
        self.rift_count = 0  # 汲取的虚境裂隙数量

        self.lunar_bonus = [
            [3.5, 6.6, 8.8, 11], [4, 7.2, 9.6, 12], [4.5, 7.8, 10.4, 13],
            [5, 8.4, 11.2, 14], [5.5, 9, 12, 15], [6, 9.6, 12.8, 16],
            [6.5, 10.2, 13.6, 17], [7, 10.8, 14.4, 18], [7.5, 11.4, 15.2, 19],
            [8, 12, 16, 20], [8.5, 12.6, 16.8, 21], [9, 13.2, 17.6, 22],
            [9.5, 13.8, 18.4, 23], [10, 14.4, 19.2, 24], [10.5, 15, 20, 25]
        ]

        self.msg = """凋尽效果：普通攻击造成的伤害提高"""
        
    def apply(self):
        existing = next((e for e in self.current_character.active_effects 
                       if isinstance(e, DecayEffect)), None)
        if existing:
            existing.duration = self.duration
            existing.trigger_count = 0
            if self.character.level >= 20:
                existing.rift_count = min(3, existing.rift_count + self.character.get_rift_count())
            return
        super().apply()
        self.character.add_effect(self)
        if self.character.level >= 20:
            self.rift_count = min(3, self.rift_count + self.character.get_rift_count())
        get_emulation_logger().log_effect(f"{self.character.name}获得凋尽效果")
        EventBus.subscribe(EventType.BEFORE_DAMAGE_MULTIPLIER,self)
        
    def remove(self):
        super().remove()
        get_emulation_logger().log_effect(f"{self.character.name}的凋尽效果结束")

    def handle_event(self, event):
        if event.data['character'] == self.character:
            damage = event.data['damage']
            if damage.damageType == DamageType.NORMAL:
                damage.panel['伤害倍率'] += self.lunar_bonus[self.lv-1][self.rift_count]
                damage.setDamageData('凋尽_倍率加成', self.lunar_bonus[self.lv-1][self.rift_count])
                self.trigger_count += 1

    def update(self, target):
        if self.trigger_count == self.max_triggers:
            self.remove()
        if self.character.mode == '正常模式':
            self.remove()

class SpecialElementalBurst(EnergySkill):
    """七相一闪模式下的特殊元素爆发"""
    def __init__(self, lv):
        super().__init__(
            name="极恶技·尽",
            total_frames=60,  # 总帧数
            cd=15*60,        # 15秒冷却
            lv=lv,
            element=('冰', 1),
            interruptible=False
        )

    def start(self, caster):
        if not super().start(caster):
            return False
            
        DecayEffect(caster, self.lv).apply()
        
        get_emulation_logger().log_skill_use(
            f"❄️ {caster.name} 释放极恶技·尽，获得凋尽效果"
        )
        return True

    def on_frame_update(self, target):
        ...

    def on_finish(self):
        super().on_finish()
        get_emulation_logger().log_skill_use("❄️ 极恶技·尽完成")

class PassiveSkillEffect_1(TalentEffect, EventHandler):
    def __init__(self):
        super().__init__('理外之理')
        self.last_tigger_time = -2.5 * 60

    def apply(self, character):
        super().apply(character)

        EventBus.subscribe(EventType.AFTER_FREEZE, self)
        EventBus.subscribe(EventType.AFTER_SUPERCONDUCT, self)
        EventBus.subscribe(EventType.AFTER_SWIRL, self)
        EventBus.subscribe(EventType.AFTER_CRYSTALLIZE, self)

    def summon_rift(self, frame):
        rift = [o for o in Team.active_objects  if o.name == '虚境裂隙']
        if len(rift) < 3:
            RiftObject().apply()
        else:
            sorted_rift = sorted(rift, key=lambda x: x.current_frame)
            sorted_rift[0].current_frame = 0
        self.last_tigger_time = frame

    def handle_event(self, event):
        if event.frame - self.last_tigger_time > 2.5 *60:
            if event.event_type in [EventType.AFTER_FREEZE, EventType.AFTER_SUPERCONDUCT]:
                self.summon_rift(event.frame)
            elif event.event_type in [EventType.AFTER_SWIRL,EventType.AFTER_CRYSTALLIZE]:
                r = event.data['elementalReaction']
                if r.target_element == '冰':
                    self.summon_rift(event.frame)

class PassiveSkillEffect_2(TalentEffect, EventHandler):
    def __init__(self):
        super().__init__('万流归寂')

    def apply(self, character):
        super().apply(character)

        EventBus.subscribe(EventType.AFTER_DAMAGE, self)

    def handle_event(self, event):
        if event.data['character'] is self.character:
            return
        element = event.data['character'].element
        if element in ['水', '冰'] and event.data['damage'].element[0] == element:
            DeathsCrossingEffect(self.character).apply(event.data['character'].name)

class DeathsCrossingEffect(Effect, EventHandler):
    def __init__(self,character):
        super().__init__(character, 20*60)
        self.name = '死河渡断'
        self.stacks = {}
        self.multipiler = {'普通攻击':[110,120,170],
                           '元素爆发':[105,115,160]}
        self.msg = f"""
        <p><span style="color: #faf8f0; font-size: 14pt;">{self.character.name} - {self.name}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">每层死河渡断效果会使丝柯克在七相一闪模式下时进行的普通攻击造成原本110%/120%/170%的伤害，
        且施放的元素爆发极恶技·灭造成原本105%/115%/160的伤害。</span></p>
        """

    def apply(self,name):
        existing = next((e for e in self.character.active_effects if e.name == self.name), None)
        if existing:
            existing.stacks[name]  = 20*60
            return
        super().apply()
        self.character.add_effect(self)
        get_emulation_logger().log_effect(f'☄ {self.character.name}获得{self.name}效果')
        EventBus.subscribe(EventType.BEFORE_INDEPENDENT_DAMAGE,self)

    def remove(self):
        super().remove()
        get_emulation_logger().log_effect(f'☄ {self.character.name}移除{self.name}效果')
        EventBus.unsubscribe(EventType.BEFORE_INDEPENDENT_DAMAGE,self)

    def handle_event(self, event):
        if event.data['character'] is not self.character:
            return
        damage = event.data['damage']
        if self.character.mode == '七相一闪' and damage.damageType == DamageType.NORMAL:
            damage.panel['独立伤害加成'] += self.multipiler['普通攻击'][len(list(self.stacks))-1]
            damage.setDamageData('死河渡断_独立伤害加成',self.multipiler['普通攻击'][len(list(self.stacks))-1])
        elif damage.damageType == DamageType.BURST:
            damage.panel['独立伤害加成'] += self.multipiler['元素爆发'][len(list(self.stacks))-1]
            damage.setDamageData('死河渡断_独立伤害加成',self.multipiler['元素爆发'][len(list(self.stacks))-1])

    def update(self, target):
        if self.stacks:
            self.duration = min(self.stacks.values())
            for i in self.stacks.keys():
                if self.stacks[i] > 0:
                    self.stacks[i] -= 1
                else:
                    self.stacks.pop(i)
        else:
            self.remove()

class PassiveSkillEffect_3(TalentEffect):
    def __init__(self):
        super().__init__('诸武相授')
    
    def update(self, target):
        if GetCurrentTime() == 1:
            s = set()
            for char in Team.team:
                if char.element in ['水', '冰']:
                    s.add(char.element)
            if len(s) == 2:
                for char in Team.team:
                    char.Skill.lv = min(15, char.Skill.lv + 1)
                get_emulation_logger().log_effect(f'☄ {self.name}触发')

class ConstellationEffect_1(ConstellationEffect):
    ...

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

class Skirk(Character):
    ID = 100
    def __init__(self, level=1, skill_params=..., constellation=0):
        super().__init__(Skirk.ID, level, skill_params, constellation)

    def _init_character(self):
        super()._init_character()
        self.association = '极恶骑'
        self.elemental_energy = ElementalEnergy(self,('冰',0))
        self.NormalAttack = NormalAttack(self.skill_params[0])
        self.ChargedAttack = ChargedAttack(self.skill_params[0])
        self.Skill = ElementalSkill(self.skill_params[1])
        self.normal_Burst = ElementalBurst(self.skill_params[2])
        self.Special_Burst = SpecialElementalBurst(self.skill_params[2])
        self.Burst = self.normal_Burst
        self.talent1 = PassiveSkillEffect_1()
        self.talent2 = PassiveSkillEffect_2()
        self.talent3 = PassiveSkillEffect_3()
        # self.constellation_effects[0] = ConstellationEffect_1()
        # self.constellation_effects[1] = ConstellationEffect_2()
        # self.constellation_effects[2] = ConstellationEffect_3()
        # self.constellation_effects[3] = ConstellationEffect_4()
        # self.constellation_effects[4] = ConstellationEffect_5()
        # self.constellation_effects[5] = ConstellationEffect_6()
        self.current_serpent_subtlety = 0 
        self.max_serpent_subtlety = 100
        self.mode = "正常模式" #  "正常模式"  or "七相一闪"

    def _elemental_burst_impl(self):
        if self.mode == "七相一闪":
            self.Burst = self.Special_Burst
        else:
            self.Burst = self.normal_Burst
        super()._elemental_burst_impl()

    def elemental_skill(self, hold= True):
        self._elemental_skill_impl(hold)

    def _elemental_skill_impl(self,hold):
        if self.Skill.start(self,hold):
            self._append_state(CharacterState.SKILL)
            skillEvent = ElementalSkillEvent(self,GetCurrentTime())
            EventBus.publish(skillEvent)

    def update(self, target):
        super().update(target)
        self.talent3.update(target)

    def get_rift_count(self):
        rift_count = 0
        for obj in Team.active_objects:
            if obj.name == "虚境裂隙":
                rift_count += 1
                obj.on_finish(None)
                self.current_serpent_subtlety += 8
        
        return rift_count

skirk_table = {
    'id': Skirk.ID,
    'name': '丝柯克',
    'type': '单手剑',
    'rarity': 5,
    'element': '冰',
    'association': '极恶骑',
    'normalAttack':{'攻击次数':5},
    'chargedAttack':{},
    # 'plungingAttack': {'攻击距离':['高空', '低空']},
    'skill': {'释放时间':['长按','点按']},
    'burst': {}
}
