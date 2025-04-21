import types
from character.NATLAN.natlan import Natlan
from character.character import CharacterState
from core.BaseClass import ChargedAttackSkill, ConstellationEffect, DashSkill, ElementalEnergy, NormalAttackSkill, SkillBase, TalentEffect
from core.effect.BaseEffect import AttackBoostEffect, DefenseDebuffEffect, Effect
from core.BaseObject import baseObject
from core.calculation.DamageCalculation import Damage, DamageType
from core.Event import ChargedAttackEvent, DamageEvent, ElementalSkillEvent, EventBus, EventHandler, EventType, GameEvent, NightSoulBlessingEvent, NormalAttackEvent
from core.Team import Team
from core.Tool import GetCurrentTime, summon_energy
from core.Logger import get_emulation_logger

class RingOfSearingRadianceObject(baseObject):
    def __init__(self, character, life_frame=0):
        super().__init__('焚曜之环', life_frame)
        self.character = character
        self.damage_multiplier = [128, 137.6, 147.2, 160, 169.6, 179.2, 192, 
                                  204.8, 217.6, 230.4, 243.2, 256, 272, 288, 304, ]

    def update(self, target):
        self.current_frame += 1
        self.on_frame_update(target)

    def on_frame_update(self, target):
        if self.current_frame % (2*60) == 0:
            if self.character.current_night_soul <= 0: 
                self.on_finish()
                return 
            self.character.consume_night_soul(3)
            damage = Damage(
                damageMultipiler=self.damage_multiplier[self.character.Skill.lv-1], 
                element=('火',1),
                damageType=DamageType.SKILL,
                name='焚曜之环'
            )
            damageEvent = DamageEvent(source=self.character, target=target, damage=damage, frame=GetCurrentTime())
            EventBus.publish(damageEvent)
    
        if self.character.constellation >= 2:
            effect = DefenseDebuffEffect(self.character,target, 20, 2,'灰烬的代价-焚曜之环')
            effect.apply()

    def on_finish(self):
        super().on_finish(None)

class ElementalSkill(SkillBase, EventHandler):
    def __init__(self, lv):
        super().__init__(name="诸火武装", total_frames=15, cd=15*60, lv=lv, 
                        element=('火', 1), interruptible=False)
        
        self.damageMultipiler ={'伤害':[74.4, 79.98, 85.56, 93, 98.58, 104.16, 111.6, 119.04, 
                                      126.48, 133.92, 141.36, 148.8, 158.1, 167.4, 176.7, ]}

        EventBus.subscribe(EventType.AFTER_CHARACTER_SWITCH, self)

    def start(self, caster, hold=False):
        if caster.Nightsoul_Blessing:
            if caster.mode == '驰轮车':
                caster.switch_to_mode('焚曜之环')
            else:
                caster.switch_to_mode('驰轮车')
            return False
        if not super().start(caster):
            return False
        # 初始化形态
        caster.gain_night_soul(self.caster.max_night_soul)
        initial_mode = '驰轮车' if hold else '焚曜之环'
        if caster.switch_to_mode(initial_mode):
            get_emulation_logger().log("INFO", f"进入夜魂加持状态，初始形态：{initial_mode}")
        return True

    def on_frame_update(self, target):
        if self.current_frame == 7:
            damage = Damage(damageMultipiler=self.damageMultipiler['伤害'][self.lv-1], 
                            element=('火',1), 
                            damageType=DamageType.SKILL,
                            name=self.name)
            damageEvent = DamageEvent(source=self.caster, target=target, damage=damage, frame=GetCurrentTime())
            EventBus.publish(damageEvent)
            summon_energy(5, self.caster, ('火', 2))
           
    def handle_event(self, event):
        if event.event_type == EventType.AFTER_CHARACTER_SWITCH:
            if event.data['old_character'] == self.caster:
                if self.caster.mode == '驰轮车':
                    self.caster.switch_to_mode('焚曜之环')
    def on_finish(self):
        super().on_finish()

    def on_interrupt(self):
        self.on_finish()

class FurnaceEffect(Effect, EventHandler):
    def __init__(self, character, consumed_will):
        super().__init__(character, duration=7 * 60 + 49)
        self.consumed_will = consumed_will
        self.name = '死生之炉'
        self.msg = f"""
        <p><span style="color: #faf8f0; font-size: 14pt;">{self.character.name} - {self.name}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">持续期间，玛薇卡的各种行为将不再消耗夜魂值，并提高玛薇卡的抗打断能力。
        同时，依据施放时的战意，提升坠日斩、「古名解放」时的普通攻击与重击造成的伤害。
        死生之炉状态将在玛薇卡退场时解除。</span></p>
        """
        
    def apply(self):
        super().apply()
        get_emulation_logger().log_effect('玛薇卡获得死生之炉')
        # 防止重复应用
        existing = next((e for e in self.character.active_effects 
                       if isinstance(e, FurnaceEffect)), None)
        if existing:
            existing.duration = self.duration  # 刷新持续时间
            return
        self.character.add_effect(self)
        EventBus.subscribe(EventType.BEFORE_NIGHT_SOUL_CHANGE, self)
        EventBus.subscribe(EventType.AFTER_CHARACTER_SWITCH, self)
        EventBus.subscribe(EventType.BEFORE_DAMAGE_MULTIPLIER, self)

        
    def remove(self):
        get_emulation_logger().log_effect('死生之炉结束')
        super().remove()
        EventBus.unsubscribe(EventType.BEFORE_NIGHT_SOUL_CHANGE, self)
        EventBus.unsubscribe(EventType.AFTER_CHARACTER_SWITCH, self)
        EventBus.unsubscribe(EventType.BEFORE_DAMAGE_MULTIPLIER, self)
    
    def handle_event(self, event: GameEvent):
        # 阻止夜魂消耗
        if event.event_type == EventType.BEFORE_NIGHT_SOUL_CHANGE:
            if event.data['character'] == self.character:
                event.cancelled = True
                
        # 角色切换时移除效果
        elif event.event_type == EventType.AFTER_CHARACTER_SWITCH:
            if event.data['old_character'] == self.character:
                self.duration = 0  # 立即结束效果
                
        # 伤害倍率提升
        elif event.event_type == EventType.BEFORE_DAMAGE_MULTIPLIER:
            if event.data['character'] == self.character and self.character.mode == '驰轮车':
                damage = event.data['damage']
                if damage.damageType == DamageType.NORMAL:
                    normal_bonus = self.character.Burst.damageMultipiler['驰轮车普通攻击伤害提升'][self.character.Burst.lv-1]
                    damage.damageMultipiler += self.consumed_will * normal_bonus
                    damage.setDamageData('死生之炉提升', self.consumed_will * normal_bonus)
                elif damage.damageType == DamageType.CHARGED:
                    heavy_bonus = self.character.Burst.damageMultipiler['驰轮车重击伤害提升'][self.character.Burst.lv-1]
                    damage.damageMultipiler += self.consumed_will * heavy_bonus
                    damage.setDamageData('死生之炉提升', self.consumed_will * heavy_bonus)

class ElementalBurst(SkillBase, EventHandler):
    def __init__(self, lv, caster=None):
        super().__init__(name="燔天之时", total_frames=141, cd=18*60, lv=lv, caster=caster,
                        element=('火', 1))
        self.damageMultipiler = {
            '坠日斩':[444.8, 478.16, 511.52, 556, 589.36, 622.72, 667.2, 711.68, 
                   756.16, 800.64, 845.12, 889.6, 945.2, 1000.8, 1056.4, ],
            '坠日斩伤害提升':[1.6,1.72,1.84,2,2.12,2.24,2.4,2.56,2.72,2.88,3.04,3.2,3.4,3.6,3.8],
            '驰轮车普通攻击伤害提升':[0.26,0.28,0.3,0.33,0.35,0.37,0.41,0.44,0.47,0.51,0.55,0.58,0.62,0.65,0.69],
            '驰轮车重击伤害提升':[0.52,0.56,0.6,0.66,0.7,0.75,0.82,0.88,0.95,1.02,1.09,1.16,1.24,1.31,1.38]
        }
        # 战意系统属性
        self.max_battle_will = 200
        self.battle_will = 200
        self.last_will_gain_time = -99  # 最后获得战意的时间戳

        # 控制标志
        self.ttt = 0 # 控制日志打印
        
        # 订阅事件
        EventBus.subscribe(EventType.AFTER_NORMAL_ATTACK, self)
        EventBus.subscribe(EventType.AFTER_NIGHT_SOUL_CHANGE, self)

    def start(self, caster):
        if self.battle_will < 50:
            get_emulation_logger().log_error("战意不足，无法施放元素爆发")
            return False
        if not super().start(caster):
            return False
        
        # 消耗所有战意
        self.consumed_will = self.battle_will
        self.battle_will = 0
        self.caster.gain_night_soul(10)
        self.caster.switch_to_mode('驰轮车')
        
        return True

    # 坠日斩
    def _perform_plunge_attack(self,target):
        damage = Damage(damageMultipiler=self.damageMultipiler['坠日斩'][self.lv-1]+self.consumed_will*self.damageMultipiler['坠日斩伤害提升'][self.lv-1],
                        element=('火',1), damageType=DamageType.BURST,
                        name="坠日斩")
        damage.setDamageData('死生之炉提升', self.consumed_will*self.damageMultipiler['坠日斩伤害提升'][self.lv-1])
        damage.setDamageData('夜魂伤害', True)
        damage.setDamageData('不可覆盖', True)
        damageEvent = DamageEvent(source=self.caster, target=target, damage=damage, frame=GetCurrentTime())
        EventBus.publish(damageEvent)

    def handle_event(self, event: GameEvent):
        # 普通攻击获得战意
        if event.event_type == EventType.AFTER_NORMAL_ATTACK:
            if event.frame - self.last_will_gain_time >= 6:
                self.gain_battle_will(1.5)
                self.last_will_gain_time = event.frame
        elif event.event_type == EventType.AFTER_NIGHT_SOUL_CHANGE:
            if event.data['amount'] < 0:
                self.gain_battle_will(-event.data['amount'])

    def on_frame_update(self, target):
        if self.current_frame == 106:
            # 创建并应用死生之炉效果
            furnace_effect = FurnaceEffect(self.caster, self.consumed_will)
            furnace_effect.apply()
            self._perform_plunge_attack(target)

    def on_finish(self):
        super().on_finish()

    def on_interrupt(self):
        self.on_finish()

    def gain_battle_will(self, amount):
        self.battle_will = min(self.max_battle_will, self.battle_will + amount)
        if self.ttt % 60 == 0:
            get_emulation_logger().log("INFO", f"获得战意：{self.battle_will:.2f}")
        self.ttt += 1

class MavuikaNormalAttackSkill(NormalAttackSkill):
    def __init__(self,lv):
        super().__init__(lv)
        self.element_sequence = [1, 0, 0]  # 火元素附着序列 (1,0,0循环)
        self.sequence_index = 0            # 当前序列位置
        self.last_sequence_state = None    # 记录上次形态用于重置
        # 普通形态的帧数和倍率
        self.normal_segment_frames = [38,40,50,48]
        self.normal_damageMultipiler = {
            1:[80.04,86.55,93.06,102.37,108.88,116.33,126.57,136.8,147.07,158.21,169.38],
            2:[36.48*2,39.45*2,42.42*2,46.66*2,49.63*2,53.02*2,57.69*2,62.36*2,67.02*2,72.11*2,77.2*2],
            3:[33.22*3,35.93*3,38.63*3,42.49*3,45.2*3,48.29*3,52.54*3,56.79*3,61.04*3,65.67*3,70.31*3],
            4:[116.19,125.65,135.11,148.62,158.08,168.89,183.75,198.61,213.47,229.68,245.9]
        }
        # 驰轮车形态的帧数和倍率
        self.chariot_segment_frames = [30, 35, 40, 45, 50]  # 5段攻击帧数
        self.chariot_damageMultipiler = {
            1:[57.26,61.93,66.59,73.25,77.91,83.23,90.56,97.88,105.21,113.2,121.19,129.18,137.17],
            2:[59.13,63.95,68.76,75.63,80.45,85.95,93.51,101.08,108.64,116.89,125.14,133.39,141.64],
            3:[69.99,75.68,81.38,89.52,95.21,101.72,110.68,119.63,128.58,138.35,148.11,157.88,167.64],
            4:[69.7,75.38,81.05,89.16,94.83,101.31,110.23,119.15,128.06,137.79,147.51,157.24,166.97],
            5:[91,98.41,105.82,116.4,123.81,132.27,143.91,155.55,167.19,179.89,192.59,205.29,217.99]
        }

    def start(self, caster, n):
        # 根据形态切换数据
        if caster.mode == '驰轮车':
            self.segment_frames = self.chariot_segment_frames
            self.damageMultipiler = self.chariot_damageMultipiler
            self.max_segments = 5  # 驰轮车5段
        else:
            self.segment_frames = self.normal_segment_frames
            self.damageMultipiler = self.normal_damageMultipiler
            self.max_segments = 4  # 普通4段

        if not super().start(caster, n):
            return False
        return True
    
    def _on_segment_end(self, target):
        # 驰轮车状态下消耗夜魂
        if self.caster.mode == '驰轮车':
            if not self.caster.consume_night_soul(1):
                get_emulation_logger().log_error("夜魂不足，攻击中断")
                self.current_segment = self.max_segments  # 强制结束攻击
                return True
        
        return super()._on_segment_end(target)

    def _apply_segment_effect(self, target):
        # --------------------------
        # 火元素序列控制逻辑
        # --------------------------
        if self.caster.mode == '驰轮车':
            self.lv = self.caster.skill_params[1]
            # 形态切换时重置序列
            if self.last_sequence_state != '驰轮车':
                self.sequence_index = 0
                self.last_sequence_state = '驰轮车'

            # 获取当前元素量并推进序列
            element_value = self.element_sequence[self.sequence_index % 3]
            element = ('火', element_value)
            
            # 推进序列索引(只在驰轮车形态下)
            self.sequence_index += 1
        else:
            self.lv = self.caster.skill_params[0]
            element = self.element  # 普通形态使用物理伤害
            # 切换回普通形态时重置状态记录
            self.last_sequence_state = '普通'

        # --------------------------
        # 伤害计算与事件发布
        # --------------------------
        base_multiplier = self.damageMultipiler[self.current_segment+1][self.lv-1]

        damage = Damage(
            damageMultipiler=base_multiplier,
            element=element,
            damageType=DamageType.NORMAL,
            name="驰轮车" if self.caster.mode == '驰轮车' else "普通攻击",
        )
        damage_event = DamageEvent(self.caster, target, damage, GetCurrentTime())
        EventBus.publish(damage_event)

        # 发布普通攻击后事件（保持原有逻辑）
        normal_attack_event = NormalAttackEvent(self.caster, GetCurrentTime(),False, self.current_segment+1)
        EventBus.publish(normal_attack_event)

class MavuikaChargedAttackSkill(ChargedAttackSkill):
    def __init__(self, lv):
        super().__init__(lv)
        # 驰轮车形态参数
        self.spin_interval = 40  # 每次旋转伤害间隔帧数
        self.spin_count = 0             # 当前旋转次数
        self.spin_total = 8             # 总旋转次数
        self.finish_damage_frame = 80   # 终结伤害帧数

        # 火元素附着序列控制
        self.element_sequence = [1, 0, 0]  # 旋转伤害附着序列
        self.sequence_index = 0           # 当前序列位置
        self.last_mode_state = None      # 记录上次形态

        # 伤害倍率配置
        self.damageMultipiler = [  
            193.84,209.62,225.4,247.94,263.72,281.75,306.54,331.34,356.13,383.18,410.23
        ]
        self.chariot_multiplier = {
            '驰轮车重击循环伤害':[98.9,106.95,115,126.5,134.55,143.75,156.4,160.05,181.7,195.5,209.3,223.1,236.9],
            '驰轮车重击终结伤害':[137.6,148.8,160,176,187.2,200,217.6,235.2,252.8,272,291.2,310.4,329.6]
        }

    def start(self, caster):
        if not super().start(caster):
            return False
        
        # 检查夜魂值
        if caster.mode == '驰轮车' and caster.current_night_soul < 2:
            get_emulation_logger().log_error("夜魂不足，无法发动驰轮车重击")
            return False
        caster.consume_night_soul(2)
        # 根据形态初始化参数
        if caster.mode == '驰轮车':
            self.total_frames = self.spin_interval * self.spin_total + self.finish_damage_frame + 1
            self.spin_count = 0
            self.sequence_index = 0
            get_emulation_logger().log("INFO", "进入驰轮车重击-焰轮旋舞")
        else:
            # 普通重击参数
            self.total_frames = 45  # 默认45帧

        return True

    def on_frame_update(self, target):
        # 普通重击逻辑
        if self.caster.mode != '驰轮车':
            return super().on_frame_update(target)

        # 驰轮车重击逻辑
        # 旋转阶段
        if self.spin_count < self.spin_total:
            if self.current_frame % self.spin_interval == 0:
                self._apply_spin_damage(target)
                self.spin_count += 1
                # 每次旋转消耗夜魂
                self.caster.consume_night_soul(2)
        # 终结伤害阶段
        elif self.current_frame == self.spin_total * self.spin_interval + self.finish_damage_frame:
            self._apply_finish_damage(target)
            return True

        return False

    def _apply_spin_damage(self, target):
        """应用旋转伤害"""
        event = ChargedAttackEvent(self.caster, GetCurrentTime())
        EventBus.publish(event)
        # 获取当前元素量
        element_value = self.element_sequence[self.sequence_index % 3]
        element = ('火', element_value)
        self.sequence_index += 1

        base_multiplier = self.chariot_multiplier['驰轮车重击循环伤害'][self.lv-1]

        damage = Damage(
            base_multiplier,
            element=element,
            damageType=DamageType.CHARGED,
            name='驰轮车重击'
        )
        damage.setDamageData("夜魂伤害",True)
        damage.setDamageData('不可覆盖',True)
        damage_event = DamageEvent(self.caster, target, damage, GetCurrentTime())
        EventBus.publish(damage_event)

        event = ChargedAttackEvent(self.caster, GetCurrentTime(), before=False)
        EventBus.publish(event)

    def _apply_finish_damage(self, target):
        """应用终结伤害"""
        base_multiplier = self.chariot_multiplier['驰轮车重击终结伤害'][self.lv-1]
        damage = Damage(
            base_multiplier,
            element=('火', 1),  
            damageType=DamageType.CHARGED,
            name='驰轮车重击终结'
        )
        damage.setDamageData("夜魂伤害",True)
        damage.setDamageData('不可覆盖',True)
        damage_event = DamageEvent(self.caster, target, damage, GetCurrentTime())
        EventBus.publish(damage_event)

    def on_finish(self):
        super().on_finish()
        if self.caster.mode == '驰轮车':
            get_emulation_logger().log("INFO", "焰轮旋舞结束")

    def on_interrupt(self):
        super().on_interrupt()
        if self.caster.mode == '驰轮车':
            get_emulation_logger().log_error("焰轮旋舞被打断！")

class MavuikaDashSkill(DashSkill):
    def __init__(self):
        super().__init__(22, 4.5, interruptible = False)
        self.hit_frame = 20
        self.damageMultipiler =[80.84, 87.42, 94, 103.4, 109.98, 117.5, 127.84, 
                                138.18, 148.52, 159.8, 171.08, 182.36, 193.64, 204.92, 216.2]

    def start(self, caster):
        if not super().start(caster):
            return False

        if self.caster.mode == '驰轮车':
            self.total_frames = 24
            self.v = 5
        else:
            self.total_frames = 22
            self.v = 4.5
        return True
    
    def on_frame_update(self, target):
        if self.current_frame == self.hit_frame and self.caster.mode == '驰轮车':
            damage = Damage(
                self.damageMultipiler[self.caster.Skill.lv - 1],
                element=('火', 1),
                damageType=DamageType.NORMAL,
                name='驰轮车冲刺伤害'
            )
            damage.setDamageData("夜魂伤害",True)
            damage_event = DamageEvent(self.caster, target, damage, GetCurrentTime())
            EventBus.publish(damage_event)
            self.caster.consume_night_soul(10)
        super().on_frame_update(target)

class TwoPhaseDamageBoostEffect(Effect, EventHandler):
    def __init__(self, source, initial_boost, fixed_duration, decay_duration):
        super().__init__(source)
        self.name = "「基扬戈兹」"
        self.current_boost = initial_boost
        self.max_boost = initial_boost
        self.fixed_duration = fixed_duration
        self.decay_duration = decay_duration
        self.total_duration = fixed_duration + decay_duration
        self.decay_rate = self.max_boost / decay_duration
        self.current_holder = None
        EventBus.subscribe(EventType.AFTER_CHARACTER_SWITCH, self)

    def apply(self):
        super().apply()
        self.current_holder = self.character
        self._apply_boost()
        get_emulation_logger().log_effect(f"「基扬戈兹」生效！初始加成：{self.current_boost*100:.1f}%")

    def handle_event(self, event):
        if event.event_type == EventType.AFTER_CHARACTER_SWITCH and self in event.data['old_character'].active_effects:
            new_char = event.data['new_character']
            self._transfer_effect(new_char)

    def _transfer_effect(self, new_char):
        self._remove_boost()
        self.current_holder = new_char
        new_char.active_effects.append(self)
        self._apply_boost()
        get_emulation_logger().log_effect(f"「基扬戈兹」转移至{new_char.name}")

    def _apply_boost(self):
        if self.current_holder:
            self.current_holder.attributePanel['伤害加成'] += self.current_boost * 100
            self.msg = f"""
            <p><span style="color: #faf8f0; font-size: 14pt;">{self.character.name} - {self.name}</span></p>
            <p><span style="color: #c0e4e6; font-size: 12pt;">获得{self.current_boost * 100:.2f}%伤害加成</span></p>
        """

    def _remove_boost(self):
        if self.current_holder:
            self.current_holder.attributePanel['伤害加成'] -= self.current_boost * 100

    def update(self):
        if self.total_duration > 0:
            # 先移除当前加成
            self._remove_boost()
            
            # 计算新加成值
            if self.total_duration <= self.decay_duration:
                self.current_boost = max(0, self.current_boost - self.decay_rate)
                
            # 重新应用新值
            self._apply_boost()
            
            self.total_duration -= 1
        else:
            self.remove()
            get_emulation_logger().log_effect("「基扬戈兹」效果结束！")
            
class PassiveSkillEffect_2(TalentEffect, EventHandler):
    def __init__(self):
        super().__init__('「基扬戈兹」')
        
    def apply(self, character):
        super().apply(character)
        EventBus.subscribe(EventType.BEFORE_BURST, self)
    
    def handle_event(self, event):
        if event.event_type == EventType.BEFORE_BURST and event.data['character'] == self.character:
            consumed_will = self.character.Burst.consumed_will
            initial_boost = min(consumed_will * 0.002, 0.4)  # 每0.2% 最高40%
            
            effect = TwoPhaseDamageBoostEffect(
                source=self.character,
                initial_boost=initial_boost,
                fixed_duration=143,  
                decay_duration=20*60
            )
            effect.apply()

class PassiveSkillEffect_1(TalentEffect, EventHandler):
    def __init__(self):
        super().__init__('炎花献礼')
        self.boost_amount = 30  # 30%攻击力提升

    def apply(self, character):
        super().apply(character)
        EventBus.subscribe(EventType.NightsoulBurst, self)
    
    def handle_event(self, event):
        if event.event_type == EventType.NightsoulBurst:
            get_emulation_logger().log_effect(f"炎花献礼：玛薇卡攻击力提升{self.boost_amount}%")
            effect = AttackBoostEffect(self.character, self.character, self.name, self.boost_amount, 10*60)
            effect.apply()

class ConstellationEffect_1(ConstellationEffect):
    def __init__(self):
        super().__init__('夜主的授记')
        self.boost_amount = 40  # 40%攻击力提升
    
    def apply(self, character):
        super().apply(character)
        # 提升夜魂值上限
        character.max_night_soul = 120
        
        # 添加战意效率提升和攻击力提升
        def f(self, amount):
            self.battle_will = min(self.max_battle_will, self.battle_will + amount*1.25)
            if self.ttt % 60 == 0:
                get_emulation_logger().log("INFO", f"获得战意：{self.battle_will:.2f}")
            self.ttt += 1
            effect = AttackBoostEffect(self.caster, self.caster, '夜主的授记', 40, 8*60)
            effect.apply()
        character.Burst.gain_battle_will = types.MethodType(f, character.Burst)
   
class ConstellationEffect_2(ConstellationEffect, EventHandler):
    def __init__(self):
        super().__init__('灰烬的代价')
    
    def apply(self, character):
        super().apply(character)
        EventBus.subscribe(EventType.BEFORE_NIGHTSOUL_BLESSING, self)
        EventBus.subscribe(EventType.AFTER_NIGHTSOUL_BLESSING, self)
        EventBus.subscribe(EventType.BEFORE_DAMAGE_MULTIPLIER, self)

    def handle_event(self, event):
        if event.data['character'] != self.character:
            return
        if event.event_type == EventType.BEFORE_NIGHTSOUL_BLESSING:
            self.character.attributePanel['攻击力'] += 200
        elif event.event_type == EventType.AFTER_NIGHTSOUL_BLESSING:
            self.character.attributePanel['攻击力'] -= 200
        elif event.event_type == EventType.BEFORE_DAMAGE_MULTIPLIER:
            if self.character.mode != '驰轮车':
                return
            damage = event.data['damage']
            if damage.damageType == DamageType.NORMAL:
                damage.damageMultipiler += 60
                damage.setDamageData('灰烬的代价', 60)
            elif damage.damageType == DamageType.CHARGED:
                damage.damageMultipiler += 90
                damage.setDamageData('灰烬的代价', 90)
            elif damage.damageType == DamageType.BURST:
                damage.damageMultipiler += 120
                damage.setDamageData('灰烬的代价', 120)

# todo
# 命座3，4，5，6
# 驰轮车下的元素附着 冷却重置逻辑未实现
class MAVUIKA(Natlan):
    ID = 92
    def __init__(self,level,skill_params,constellation=0):
        super().__init__(MAVUIKA.ID,level,skill_params,constellation)

    def _init_character(self):
        super()._init_character()
        self.elemental_energy = ElementalEnergy(self,('火',0))
        self.NormalAttack = MavuikaNormalAttackSkill(self.skill_params[0])
        self.ChargedAttack = MavuikaChargedAttackSkill(self.skill_params[0])
        self.Dash = MavuikaDashSkill()
        self.Skill = ElementalSkill(self.skill_params[1])
        self.Burst = ElementalBurst(self.skill_params[2],caster=self)
        self.talent1 = PassiveSkillEffect_1()
        self.talent2 = PassiveSkillEffect_2()
        self.mode = '正常模式'  # 初始模式
        self.constellation_effects[0] = ConstellationEffect_1()
        self.constellation_effects[1] = ConstellationEffect_2()

    def update(self, target):
        if  self.mode != '正常模式':
            if self.mode == '焚曜之环':
                self.consume_night_soul(5/60)
            elif self.mode == '驰轮车':
                self.consume_night_soul(9/60)
            self.time_accumulator += 1
            if self.time_accumulator >= 60:
                self.time_accumulator -= 60
                get_emulation_logger().log("INFO", f"夜魂剩余：{self.current_night_soul:.2f}")

        super().update(target)

    def elemental_skill(self,hold=False):
        self._elemental_skill_impl(hold)

    def _elemental_skill_impl(self,hold=False):
        # 已处于技能状态时切换形态
        if self.Skill.start(self,hold):
            self._append_state(CharacterState.SKILL)
            skillEvent = ElementalSkillEvent(self, frame=GetCurrentTime())
            EventBus.publish(skillEvent)

    def chargeNightsoulBlessing(self):
        if self.Nightsoul_Blessing:
            self.after_nightsoulBlessingevent = NightSoulBlessingEvent(self, frame=GetCurrentTime(), before=False)
            EventBus.publish(self.after_nightsoulBlessingevent)
            self.Nightsoul_Blessing = False
            self.switch_to_mode('正常模式')
            get_emulation_logger().log("INFO", f"{self.name} 夜魂加持结束")
        else:
            self.before_nightsoulBlessingevent = NightSoulBlessingEvent(self, frame=GetCurrentTime())
            EventBus.publish(self.before_nightsoulBlessingevent)
            self.Nightsoul_Blessing = True
            get_emulation_logger().log("INFO", "夜魂加持")
    
    def switch_to_mode(self, new_mode):
        """安全切换形态的方法"""
        # 只能在夜魂加持状态下切换战斗形态
        if not self.Nightsoul_Blessing and new_mode != '正常模式':
            return False
            
        # 验证形态有效性
        if new_mode not in ['正常模式', '焚曜之环', '驰轮车']:
            return False
            
        if self.mode == new_mode:
            return False
            
        # 执行形态切换
        self.mode = new_mode
        
        if self.mode == '焚曜之环':
            ring = RingOfSearingRadianceObject(self)
            ring.apply()
        else:
            ring = next((o for o in Team.active_objects if isinstance(o, RingOfSearingRadianceObject)), None)
            if ring:
                ring.on_finish()

        # 切换为正常模式时自动结束加持
        if new_mode == '正常模式' and self.Nightsoul_Blessing:
            self.chargeNightsoulBlessing()
            
        return True
    
    def gain_night_soul(self, amount):
       if not self.Nightsoul_Blessing:
           self.gain_NightSoulBlessing()
       super().gain_night_soul(amount)

    def consume_night_soul(self, amount):
        super().consume_night_soul(amount)
        if self.current_night_soul <= 0:
            self.romve_NightSoulBlessing()
            self.switch_to_mode('正常模式')

mavuika_table = {
    'id': MAVUIKA.ID,
    'name': '玛薇卡',
    'type': '双手剑',
    'rarity': 5,
    'element': '火',
    'association': '纳塔',
    'normalAttack':{'攻击次数':5},
    'chargedAttack':{},
    'skill':{'释放时间':['长按','点按']},
    'burst':{},
    'dash':{},
}
