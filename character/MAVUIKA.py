from character.character import Character, CharacterState
from setup.BaseClass import Effect, HeavyAttackSkill, NormalAttackSkill, SkillBase, SkillSate
from setup.DamageCalculation import Damage, DamageType
from setup.Event import DamageEvent, ElementalSkillEvent, EventBus, EventHandler, EventType, GameEvent, HeavyAttackEvent, NightSoulBlessingEvent, NightSoulConsumptionEvent, NormalAttackEvent
from setup.Tool import GetCurrentTime

class ElementalSkill(SkillBase,EventHandler):
    def __init__(self, lv):
        super().__init__(name="诸火武装", total_frames=60*12.4, cd=15*60, lv=lv, 
                        element=('火', 1), interruptible=False, state=SkillSate.OffField)
        
        self.night_soul_consumed = 0
        self.attack_interval = 0 # 神环攻击计时器
        self.ttt = False

        self.damageMultipiler ={'焚曜之环':[128,137.6,147.2,160,169.6,179.2,192,204.8,217.6,230.4,243.2,256,272],
                                '伤害':[74.4,79.98,85.56,93,98.58,104.16,111.6,119.04,126.48,133.92,141.36,148.8,158.1]}
        
        # 订阅角色切换事件
        EventBus.subscribe(EventType.CHARACTER_SWITCH, self)

    def start(self, caster, hold=False):
        if not super().start(caster):
            return False
        # 初始化形态
        caster.gain_night_soul(80)
        initial_mode = '驰轮车' if hold else '焚曜之环'
        if caster.switch_to_mode(initial_mode):  # 新增角色方法
            print(f"🔥 进入夜魂加持状态，初始形态：{initial_mode}")
            self.ttt = True
            return True
        return False

    def handle_event(self, event: GameEvent):
        """处理角色切换事件"""
        if event.event_type == EventType.CHARACTER_SWITCH:
            # 当玛薇卡被切出时自动转为焚曜之环
            if event.data['old_character'] == self.caster and self.caster is not None:
                print("🔄 角色切换，变为焚曜之环形态")
                self.caster.mode = '焚曜之环'  # 直接设置形态
                self.attack_interval = 0  # 重置攻击计时器

    def update(self, target):
        self.current_frame += 1
        if self.on_frame_update(target):
            return True
        return False

    def on_frame_update(self, target):
        if self.current_frame == 1 and self.ttt:
            damage = Damage(damageMultipiler=self.damageMultipiler['伤害'][self.lv-1], element=('火',1), damageType=DamageType.SKILL)
            damageEvent = DamageEvent(source=self.caster, target=target, damage=damage, frame=GetCurrentTime())
            EventBus.publish(damageEvent)
            self.ttt = False
            print(f"🔥 玛薇卡释放元素战技，造成伤害：{damage.damage}")
        if self.caster.mode == '正常模式':
            return True
        return False
    
    def handle_sacred_ring(self, target):
        """焚曜之环攻击逻辑（每2秒攻击一次）"""
        self.attack_interval += 1
        if self.attack_interval >= 120:
            self.attack_interval = 0
            if not self.caster.consume_night_soul(3): 
                self.on_finish()
                return

            damage = Damage(damageMultipiler=self.damageMultipiler['焚曜之环'][self.lv-1], element=('火',1), damageType=DamageType.SKILL)
            damageEvent = DamageEvent(source=self.caster, target=target, damage=damage, frame=GetCurrentTime())
            EventBus.publish(damageEvent)
            print(f"🔥 焚曜之环造成伤害：{damage.damage:.2f}")
            
    def on_finish(self):
        super().on_finish()
        self.caster.chargeNightsoulBlessing()
        self.caster.mode = '正常模式'
        print("🌙 夜魂加持结束")

    def on_interrupt(self):
        self.on_finish()

class FurnaceEffect(Effect, EventHandler):
    def __init__(self, character, consumed_will, burst_instance):
        super().__init__(character)
        self.consumed_will = consumed_will
        self.burst = burst_instance  # 持有元素爆发实例引用
        self.duration = 7 * 60
        
    def apply(self):
        print(f'玛薇卡获得死生之炉')
        # 订阅事件
        EventBus.subscribe(EventType.BEFORE_NIGHT_SOUL_CONSUMPTION, self)
        EventBus.subscribe(EventType.CHARACTER_SWITCH, self)
        
    def remove(self):
        print(f'死生之炉结束')
        # 取消订阅
        EventBus.unsubscribe(EventType.BEFORE_NIGHT_SOUL_CONSUMPTION, self)
        EventBus.unsubscribe(EventType.CHARACTER_SWITCH, self)

    
    def handle_event(self, event: GameEvent):
        # 阻止夜魂消耗
        if event.event_type == EventType.BEFORE_NIGHT_SOUL_CONSUMPTION:
            if event.data['character'] == self.character:
                event.cancelled = True
                
        # 角色切换时移除效果
        if event.event_type == EventType.CHARACTER_SWITCH:
            if event.data['old_character'] == self.character:
                self.duration = 0  # 立即结束效果

class ElementalBurst(SkillBase, EventHandler):
    def __init__(self, lv):
        super().__init__(name="燔天之时", total_frames=60*2.375, cd=18*60, lv=lv,
                        element=('火', 1), state=SkillSate.OnField)
        self.damageMultipiler = {
            '坠日斩':[444.8,478.16,511.52,556,589.36,622.72,667.2,711.68,756.16,800.64,845.12,889.6,945.2],
            '坠日斩伤害提升':[1.6,1.72,1.84,2,2.12,2.24,2.4,2.56,2.72,2.88,3.04,3.2,3.4],
            '驰轮车普通攻击伤害提升':[0.26,0.28,0.3,0.33,0.35,0.37,0.41,0.44,0.47,0.51,0.55,0.58,0.62],
            '驰轮车重击伤害提升':[0.52,0.56,0.6,0.66,0.7,0.75,0.82,0.88,0.95,1.02,1.09,1.16,1.24]
        }
        # 战意系统属性
        self.max_battle_will = 200
        self.battle_will = 100
        self.last_will_gain_time = 0  # 最后获得战意的时间戳

        # 控制标志
        self.ttt = 0 # 控制日志打印
        
        # 订阅事件
        EventBus.subscribe(EventType.AFTER_NORMAL_ATTACK, self)
        EventBus.subscribe(EventType.AFTER_NIGHT_SOUL_CONSUMPTION, self)

    def start(self, caster):
        if self.battle_will < 50:
            print("❌ 战意不足，无法施放元素爆发")
            return False
        if not super().start(caster):
            return False
        
        # 消耗所有战意
        self.consumed_will = self.battle_will
        self.battle_will = 0
        
        return True

    # 坠日斩
    def _perform_plunge_attack(self,target):
        damage = Damage(damageMultipiler=self.damageMultipiler['坠日斩'][self.lv-1]+self.consumed_will*self.damageMultipiler['坠日斩伤害提升'][self.lv-1],
                        element=('火',1), damageType=DamageType.BURST)
        damageEvent = DamageEvent(source=self.caster, target=target, damage=damage, frame=GetCurrentTime())
        EventBus.publish(damageEvent)
        print(f"🔥 坠日斩造成{damage.damage:.2f}点火元素伤害")

    def handle_event(self, event: GameEvent):
        # 普通攻击获得战意
        if event.event_type == EventType.AFTER_NORMAL_ATTACK:
            if event.frame - self.last_will_gain_time >= 6:
                self.gain_battle_will(1.5)
                self.last_will_gain_time = event.frame
        elif event.event_type == EventType.AFTER_NIGHT_SOUL_CONSUMPTION:
            self.gain_battle_will(event.data['amount'])

    def update(self, target):
        self.current_frame += 1
        if self.current_frame == int(self.total_frames):
            # 恢复夜魂值并切换形态
            self.caster.gain_night_soul(10)
            self.caster.switch_to_mode('驰轮车')
             # 创建并应用死生之炉效果
            furnace_effect = FurnaceEffect(self.caster, self.consumed_will, self)
            self.caster.add_effect(furnace_effect)
            self._perform_plunge_attack(target)
        elif self.current_frame > self.total_frames:
            self.on_finish()
            return True
        return False

    def on_frame_update(self, target):
        return super().on_frame_update(target)

    def on_finish(self):
        super().on_finish()

    def on_interrupt(self):
        self.on_finish()

    def gain_battle_will(self, amount):
        self.battle_will = min(self.max_battle_will, self.battle_will + amount)
        if self.ttt % 60 == 0:
            print(f"🔥 获得战意：{self.battle_will:.2f}")
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
                print("⚠️ 夜魂不足，攻击中断")
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
        
        # 检测死生之炉效果
        furnace_bonus = 0
        for effect in self.caster.active_effects:
            if isinstance(effect, FurnaceEffect):
                normal_bonus = effect.burst.damageMultipiler['驰轮车普通攻击伤害提升'][self.lv-1]
                furnace_bonus = effect.consumed_will * normal_bonus
                break

        total_multiplier = base_multiplier + furnace_bonus
        damage = Damage(
            damageMultipiler=total_multiplier,
            element=element,
            damageType=DamageType.NORMAL
        )
        damage_event = DamageEvent(self.caster, target, damage, GetCurrentTime())
        EventBus.publish(damage_event)

        # 输出带序列状态的日志
        if self.caster.mode == '驰轮车':
            seq_pos = (self.sequence_index-1) % 3 + 1  # 显示1-based位置
            gauge_info = f"🔥(量{element[1]} 序列{seq_pos}/3)"
            print(f"🎯 驰轮车第{self.current_segment+1}段 {gauge_info} 造成 {damage.damage:.2f} 伤害")
        else:
            print(f"🎯 普通攻击造成 {damage.damage:.2f} 物理伤害")

        # 发布普通攻击后事件（保持原有逻辑）
        normal_attack_event = NormalAttackEvent(self.caster, GetCurrentTime(),False)
        EventBus.publish(normal_attack_event)

class MavuikaHeavyAttackSkill(HeavyAttackSkill):
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
        if caster.mode == '驰轮车' and not caster.consume_night_soul(2):
            print("⚠️ 夜魂不足，无法发动驰轮车重击")
            return False

        # 根据形态初始化参数
        if caster.mode == '驰轮车':
            self.total_frames = self.spin_interval * self.spin_total + self.finish_damage_frame + 1
            self.spin_count = 0
            self.sequence_index = 0
            print("🌀 进入驰轮车重击-焰轮旋舞")
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
                if not self.caster.consume_night_soul(2):
                    print("⚠️ 夜魂不足，重击中断")
                    self.on_interrupt()
                    return True
        # 终结伤害阶段
        elif self.current_frame == self.spin_total * self.spin_interval + self.finish_damage_frame:
            self._apply_finish_damage(target)
            return True

        return False

    def _apply_spin_damage(self, target):
        """应用旋转伤害"""
        event = HeavyAttackEvent(self.caster, GetCurrentTime())
        EventBus.publish(event)
        # 获取当前元素量
        element_value = self.element_sequence[self.sequence_index % 3]
        element = ('火', element_value)
        self.sequence_index += 1

        base_multiplier = self.chariot_multiplier['驰轮车重击循环伤害'][self.lv-1]
        
        # 检测死生之炉效果
        furnace_bonus = 0
        for effect in self.caster.active_effects:
            if isinstance(effect, FurnaceEffect):
                heavy_bonus = effect.burst.damageMultipiler['驰轮车重击伤害提升'][self.lv-1]
                furnace_bonus = effect.consumed_will * heavy_bonus
                break

        total_multiplier = base_multiplier + furnace_bonus
        damage = Damage(
            total_multiplier,
            element=element,
            damageType=DamageType.HEAVY
        )
        damage_event = DamageEvent(self.caster, target, damage, GetCurrentTime())
        EventBus.publish(damage_event)
        print(f"🌀 焰轮旋舞第{self.spin_count+1}段 {element} 造成 {damage.damage:.2f} 火伤")

        event = HeavyAttackEvent(self.caster, GetCurrentTime(), before=False)
        EventBus.publish(event)

    def _apply_finish_damage(self, target):
        """应用终结伤害"""
        base_multiplier = self.chariot_multiplier['驰轮车重击终结伤害'][self.lv-1]
        
        # 检测死生之炉效果
        furnace_bonus = 0
        for effect in self.caster.active_effects:
            if isinstance(effect, FurnaceEffect):
                heavy_bonus = effect.burst.damageMultipiler['驰轮车重击伤害提升'][self.lv-1]
                furnace_bonus = effect.consumed_will * heavy_bonus
                break

        total_multiplier = base_multiplier + furnace_bonus
        damage = Damage(
            total_multiplier,
            element=('火', 1),  
            damageType=DamageType.HEAVY
        )
        damage_event = DamageEvent(self.caster, target, damage, GetCurrentTime())
        EventBus.publish(damage_event)
        print(f"💥 焰轮终结 造成 {damage.damage:.2f} 火伤")

    def on_finish(self):
        super().on_finish()
        if self.caster.mode == '驰轮车':
            print("🎇 焰轮旋舞结束")

    def on_interrupt(self):
        super().on_interrupt()
        if self.caster.mode == '驰轮车':
            print("💢 焰轮旋舞被打断！")

# todo: 
# 1. 天赋实现
# 2. 命座实现
class MAVUIKA(Character):
    ID = 92
    def __init__(self,level,skill_params):
        super().__init__(MAVUIKA.ID,level,skill_params)
        self.NormalAttack = MavuikaNormalAttackSkill(skill_params[0])
        self.HeavyAttack = MavuikaHeavyAttackSkill(skill_params[0])
        self.Skill = ElementalSkill(skill_params[1])
        self.Burst = ElementalBurst(skill_params[2])

    def _init_character(self):
        super()._init_character()
        self.max_night_soul = 80 # 夜魂值上限
        self.current_night_soul = 0
        self.Nightsoul_Blessing = False # 夜魂加持状态
        self.mode = '正常模式'  # 初始模式
        self.time_accumulator = 0   # 时间累积器

    def update(self, target):
        if  self.mode != '正常模式':
            if self.mode == '焚曜之环':
                if not self.consume_night_soul(5/60):  # 使用角色类方法
                    self.Skill.on_finish()
                    return True
                self.Skill.handle_sacred_ring(target)
            elif self.mode == '驰轮车':
                if not self.consume_night_soul(9/60):  # 使用角色类方法
                    self.Skill.on_finish()
                    return True
            
            self.time_accumulator += 1
            if self.time_accumulator >= 60:
                self.time_accumulator -= 60
                print(f"🕒 夜魂剩余：{self.current_night_soul:.2f}")

        super().update(target)

    def elemental_skill(self,hold=False):
        self._elemental_skill_impl(hold)

    def _elemental_skill_impl(self,hold=False):
        # 已处于技能状态时切换形态
        if self.mode != '正常模式':
            self.switch_mode()
            self._append_state(CharacterState.SKILL)
        elif self._is_change_state() and self.Skill.start(self,hold):
            self._append_state(CharacterState.SKILL)
            skillEvent = ElementalSkillEvent(self, frame=GetCurrentTime())
            EventBus.publish(skillEvent)

    def chargeNightsoulBlessing(self):
        if self.Nightsoul_Blessing:
            self.after_nightsoulBlessingevent = NightSoulBlessingEvent(self, frame=GetCurrentTime(), before=False)
            EventBus.publish(self.after_nightsoulBlessingevent)
            self.Nightsoul_Blessing = False
            self.switch_to_mode('正常模式')
        else:
            self.before_nightsoulBlessingevent = NightSoulBlessingEvent(self, frame=GetCurrentTime())
            EventBus.publish(self.before_nightsoulBlessingevent)
            self.Nightsoul_Blessing = True
            print(f"🌙 夜魂加持")

    def switch_mode(self):
        """切换武装形态（仅在夜魂加持状态下可用）"""
        if not self.Nightsoul_Blessing:
            return False

        new_mode = '驰轮车' if self.mode == '焚曜之环' else '焚曜之环'
        self.Skill.caster = self
        print(f"🔄 切换至形态：{new_mode}")
        self.mode = new_mode
        return True
    
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
            
            # 切换为正常模式时自动结束加持
            if new_mode == '正常模式' and self.Nightsoul_Blessing:
                self.chargeNightsoulBlessing()
                
            return True
    
    def consume_night_soul(self, amount):
        """安全消耗夜魂值并触发事件"""
        if not self.Nightsoul_Blessing:
            return False

        # 发布消耗事件
        actual_amount = min(amount, self.current_night_soul)
        event =NightSoulConsumptionEvent(
            character=self,
            amount=actual_amount,
            frame=GetCurrentTime()
        )
        EventBus.publish(event)
        if event.cancelled:
            return True
        
        self.current_night_soul -= actual_amount
        EventBus.publish(NightSoulConsumptionEvent(
            character=self,
            amount=actual_amount,
            frame=GetCurrentTime(),
            before=False
        ))
        
        # 自动退出加持状态检测
        if self.current_night_soul <= 0:
            self.chargeNightsoulBlessing()
        return True
    
    def gain_night_soul(self, amount):
        """获得夜魂值"""
        if not self.Nightsoul_Blessing:
            self.chargeNightsoulBlessing()
        self.current_night_soul = min(
            self.max_night_soul, 
            self.current_night_soul + amount
        )
       