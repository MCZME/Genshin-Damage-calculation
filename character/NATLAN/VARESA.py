from character.NATLAN.natlan import Natlan
from character.character import CharacterState
from core.BaseClass import ChargedAttackSkill, DashSkill, ElementalEnergy, EnergySkill, Infusion, NormalAttackSkill, PlungingAttackSkill, SkillBase, TalentEffect
from core.Logger import get_emulation_logger
from core.effect.BaseEffect import Effect
from core.calculation.DamageCalculation import Damage, DamageType
from core.Event import ChargedAttackEvent, DamageEvent, EventBus, EventHandler, NightSoulChangeEvent, NormalAttackEvent, PlungingAttackEvent, EventType
from core.Tool import GetCurrentTime, summon_energy

class VaresaNormalAttack(NormalAttackSkill,Infusion):
    def __init__(self, lv):
        super().__init__(lv=lv, cd=0)
        Infusion.__init__(self)
        self.element = ('雷', 1)  # 雷元素伤害

        self.normal_segment_frames = [30, 28, 58]  # 普通攻击的帧数
        
        self.damageMultiplier = {
            1:[46.78, 50.29, 53.8, 58.47, 61.98, 65.49, 70.17, 74.85, 79.52, 84.2, 88.88, 93.56, 99.4, 105.25, 111.1, ],
            2:[40.03, 43.03, 46.03, 50.03, 53.04, 56.04, 60.04, 64.04, 68.05, 72.05, 76.05, 80.06, 85.06, 90.06, 95.07, ],
            3:[56.31, 60.54, 64.76, 70.39, 74.61, 78.84, 84.47, 90.1, 95.73, 101.36, 106.99, 112.63, 119.66, 126.7, 133.74, ],
        }

        self.passion_segment_frames = [16,40,46]  # 炽热激情攻击的帧数
        self.passionMultipiler = {
            1:[54.41, 58.49, 62.57, 68.01, 72.09, 76.17, 81.61, 87.05, 92.49, 97.93, 103.37, 108.81, 115.62, 122.42, 129.22, ],
            2:[52.03, 55.93, 59.83, 65.04, 68.94, 72.84, 78.04, 83.25, 88.45, 93.65, 98.85, 104.06, 110.56, 117.06, 123.57, ],
            3:[73.59, 79.11, 84.62, 91.98, 97.5, 103.02, 110.38, 117.74, 125.1, 132.46, 139.81, 147.17, 156.37, 165.57, 174.77, ],
        }

    def start(self, caster, n):
        chase_effect = next((e for e in caster.active_effects if isinstance(e, ChaseEffect)), None)
        if chase_effect:
            caster.charged_attack()
            return False

        # 根据炽热激情状态选择帧数和倍率
        passion_effect = next((e for e in caster.active_effects if isinstance(e, PassionEffect)), None)
        if passion_effect:
            self.segment_frames = self.passion_segment_frames
            self.damageMultiplier = self.passionMultipiler
        else:
            self.segment_frames = self.normal_segment_frames
            self.damageMultiplier = self.damageMultiplier
            
        if not super().start(caster,n):
            return False
        return True

    def _apply_segment_effect(self, target):
        passion_effect = next((e for e in self.caster.active_effects if isinstance(e, PassionEffect)), None)
        if passion_effect:
            damage = Damage(
                damageMultiplier=self.passionMultipiler[self.current_segment+1][self.lv-1],
                element=('雷', self.apply_infusion()),
                damageType=DamageType.NORMAL,
                name=f'炽热激情·{self.name} 第{self.current_segment+1}段'
            )
        else:
            damage = Damage(
                damageMultiplier=self.damageMultiplier[self.current_segment+1][self.lv-1],
                element=('雷', self.apply_infusion()),
                damageType=DamageType.NORMAL,
                name=f'{self.name} 第{self.current_segment+1}段'
            )
        damage_event = DamageEvent(self.caster, target, damage, GetCurrentTime())
        EventBus.publish(damage_event)

        # 发布普通攻击事件（后段）
        normal_attack_event = NormalAttackEvent(
            self.caster, 
            frame=GetCurrentTime(), 
            before=False,
            damage=damage,
            segment=self.current_segment+1
        )
        EventBus.publish(normal_attack_event)

class VaresaPlungingAttackSkill(PlungingAttackSkill):
    def __init__(self, lv, total_frames=34, cd=0):
        super().__init__(lv, total_frames, cd)
        self.element = ('雷', 1)

        self.normal_hit_frame = 38
        self.normal_total_frames = 68
        self.damageMultiplier = {
            '下坠期间伤害': [74.59, 80.66, 86.73, 95.4, 101.47, 108.41, 117.95, 127.49, 137.03, 147.44, 157.85, 168.26, 178.66, 189.07, 199.48],
            '低空坠地冲击伤害': [149.14, 161.28, 173.42, 190.77, 202.91, 216.78, 235.86, 254.93, 274.01, 294.82, 315.63, 336.44, 357.25, 378.06, 398.87],
            '高空坠地冲击伤害': [186.29, 201.45, 216.62, 238.28, 253.44, 270.77, 294.6, 318.42, 342.25, 368.25, 394.24, 420.23, 446.23, 472.22, 498.21]
        }
        self.passion_hit_frame = 28
        self.passion_total_frames = (14 + 18)*2
        self.passionMultipiler = {
            '下坠期间伤害': [74.59, 80.66, 86.73, 95.4, 101.47, 108.41, 117.95, 127.49, 137.03, 147.44, 157.85, 168.26, 178.66, 189.07, 199.48],
            '低空坠地冲击伤害': [223.72, 241.93, 260.13, 286.15, 304.36, 325.17, 353.78, 382.4, 411.01, 442.23, 473.45, 504.66, 535.88, 567.09, 598.31],
            '高空坠地冲击伤害': [279.43, 302.18, 324.92, 357.41, 380.16, 406.15, 441.89, 477.64, 513.38, 552.37, 591.36, 630.35, 669.34, 708.33, 747.32]
        }
        self.v = 1.7
    
    def start(self, caster, is_high=False):
        """启动下落攻击并设置高度类型"""
        if not super().start(caster):
            return False
            
        # 根据炽热激情状态选择帧数和倍率
        passion_effect = next((e for e in self.caster.active_effects if isinstance(e, PassionEffect)), None)
        if passion_effect:
            self.hit_frame = self.passion_hit_frame
            self.total_frames = self.passion_total_frames
            self.damageMultiplier = self.passionMultipiler
        else:
            self.hit_frame = self.normal_hit_frame
            self.total_frames = self.normal_total_frames
            self.damageMultiplier = self.damageMultiplier
            
        self.height_type = '高空' if is_high else '低空'
        event = PlungingAttackEvent(self.caster, frame=GetCurrentTime())
        EventBus.publish(event)
        return True

    def _apply_impact_damage(self, target):
        clamped_lv = min(max(self.lv, 1), 15) - 1
        damage_type_key = '高空坠地冲击伤害' if self.height_type == '高空' else '低空坠地冲击伤害'
        
        # 计算基础伤害
        passion_effect = next((e for e in self.caster.active_effects if isinstance(e, PassionEffect)), None)
        if passion_effect:
            base_damage = self.passionMultipiler[damage_type_key][clamped_lv]

        else:
            base_damage = self.damageMultiplier[damage_type_key][clamped_lv]

        # 检查虹色坠击效果
        rainbow_effect = next((e for e in self.caster.active_effects if isinstance(e, RainbowPlungeEffect)), None)
        if rainbow_effect:
            if passion_effect:
                base_damage += 180  # 炽热激情状态下180%额外伤害
            else:
                base_damage += 50  # 普通状态下50%额外伤害

        # 发布基础伤害事件
        damage = Damage(
            base_damage,
            self.element,
            DamageType.PLUNGING,
            f'夜魂·{damage_type_key}' if not passion_effect else f'炽热激情·夜魂·{damage_type_key}'
        )
        damage.setDamageData('夜魂伤害',True)
        damage_event = DamageEvent(self.caster, target, damage, GetCurrentTime())
        EventBus.publish(damage_event)

        EventBus.publish(PlungingAttackEvent(self.caster, frame=GetCurrentTime(), before=False))
        
        # 炽热激情状态下消耗全部夜魂值
        if passion_effect:
            self.caster.consume_night_soul(self.caster.current_night_soul)
        else:
            # 普通状态下触发夜魂值获取
            self.caster.gain_night_soul(25)
       
class VaresaChargedAttack(ChargedAttackSkill):
    def __init__(self, lv, total_frames=27+20, cd=0):
        super().__init__(lv=lv, total_frames=total_frames, cd=cd)
        self.element = ('雷', 1)  # 雷元素伤害
        self.normal_hit_frame = 54
        self.normal_total_frames=self.normal_hit_frame+40
        self.damageMultiplier = [89.28, 95.98, 102.67, 111.6, 118.3, 124.99, 133.92, 142.85, 151.78,
                                  160.7, 169.63, 178.56, 189.72, 200.88, 212.04, ]
        
        self.passion_hit_frame = 42
        self.passion_total_frames=self.passion_hit_frame+16
        self.passionMultipiler = [92.64, 99.59, 106.54, 115.8, 122.75, 129.7, 138.96, 148.22, 157.49, 166.75, 176.02, 185.28, 196.86, 208.44, 220.02, ]

    def start(self, caster):
        if not super().start(caster):
            return False
            
        # 根据炽热激情状态选择帧数和倍率
        self.v = 1.7
        passion_effect = next((e for e in self.caster.active_effects if isinstance(e, PassionEffect)), None)
        if passion_effect:
            self.hit_frame = self.passion_hit_frame
            self.total_frames = self.passion_total_frames
            self.damageMultiplier = self.passionMultipiler
        else:
            self.hit_frame = self.normal_hit_frame
            self.total_frames = self.normal_total_frames
            self.damageMultiplier = self.damageMultiplier
        chase_effect = next((e for e in self.caster.active_effects if isinstance(e, ChaseEffect)), None)
        if chase_effect:
            self.hit_frame = 14
            self.total_frames = 14+14
            self.v = 5.357
            
        return True

    def _apply_attack(self, target):
        event = ChargedAttackEvent(self.caster, frame=GetCurrentTime())
        EventBus.publish(event)
        
        clamped_lv = min(max(self.lv, 1), 15) - 1
        passion_effect = next((e for e in self.caster.active_effects if isinstance(e, PassionEffect)), None)
        if passion_effect:
            damage = Damage(
                damageMultipiler=self.passionMultipiler[clamped_lv],
                element=self.element,
                damageType=DamageType.CHARGED,
                name=f'炽热激情·{self.name}',
            )
        else:
            damage = Damage(
                damageMultipiler=self.damageMultipiler[clamped_lv],
                element=self.element,
                damageType=DamageType.CHARGED,
                name=self.name,
            )

        damage.setDamageData('夜魂伤害',True)
        # 发布伤害事件
        damage_event = DamageEvent(self.caster, target, damage, GetCurrentTime())
        EventBus.publish(damage_event)

        event = ChargedAttackEvent(self.caster, frame=GetCurrentTime(), before=False)
        EventBus.publish(event)

    def on_frame_update(self, target):
        if self.current_frame == self.hit_frame:
            self._apply_attack(target)
        elif self.current_frame > self.hit_frame:
            self.caster.height += self.v
        self.caster.movement += self.v

    def on_finish(self):
        super().on_finish()
        self.caster._append_state(CharacterState.FALL)

class RainbowPlungeEffect(Effect, EventHandler):
    """虹色坠击效果"""
    def __init__(self, caster):
        super().__init__(caster,duration=5*60)
        self.name = '虹色坠击'
        self.msg = f"""
        <p><span style="color: #faf8f0; font-size: 14pt;">{self.character.name} - {self.name}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">持续期间，瓦雷莎进行下落攻击时，
        坠地冲击能额外造成50%攻击力的伤害；
        若瓦雷莎处于炽热激情状态，
        则坠地冲击改为能额外造成180%攻击力的伤害。</span></p>
        """
        
    def apply(self):
        super().apply()
        rainbowPlungeEffect = next((e for e in self.character.active_effects if isinstance(e, RainbowPlungeEffect)), None)
        if rainbowPlungeEffect:
            rainbowPlungeEffect.duration = self.duration
        self.character.add_effect(self)
        EventBus.subscribe(EventType.AFTER_PLUNGING_ATTACK, self)
        get_emulation_logger().log_effect(f"🌈 {self.character.name}获得{self.name}效果")
        
    def remove(self):
        super().remove()
        EventBus.unsubscribe(EventType.AFTER_PLUNGING_ATTACK, self)
        get_emulation_logger().log_effect(f"🌈 {self.character.name}的{self.name}效果消失")
        
    def handle_event(self, event):
        if event.event_type == EventType.AFTER_PLUNGING_ATTACK:
            if event.data['character'] == self.character and event.data['is_plunging_impact']:
                self.remove()

class ChaseEffect(Effect,EventHandler):
    """逐击效果"""
    def __init__(self, caster):
        super().__init__(caster,duration=5*60)
        self.name = '逐击'
        self.msg = f"""
        <p><span style="color: #faf8f0; font-size: 14pt;">{self.character.name} - {self.name}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">瓦雷莎将快速进行重击</span></p>
        """
        
    def apply(self):
        super().apply()
        chase = next((e for e in self.character.active_effects if isinstance(e, ChaseEffect)), None)
        if chase:
            chase.duration = self.duration
            return
        self.character.add_effect(self)
        EventBus.subscribe(EventType.AFTER_CHARGED_ATTACK, self)
        get_emulation_logger().log_effect(f"✨ {self.character.name}获得{self.name}效果")
        
    def remove(self):
        super().remove()
        EventBus.unsubscribe(EventType.AFTER_CHARGED_ATTACK, self)
        get_emulation_logger().log_effect(f"✨ {self.character.name}的{self.name}效果消失")
        
    def handle_event(self, event):
        if event.event_type == EventType.AFTER_CHARGED_ATTACK:
            if event.data['character'] == self.character:
                chaseEffect = next((e for e in self.character.active_effects if isinstance(e, ChaseEffect)), None)
                if chaseEffect:
                    chaseEffect.remove()

class ElementalSkill(SkillBase):
    """元素战技：夜虹逐跃"""
    def __init__(self, lv):
        super().__init__(name="夜虹逐跃", total_frames=30, cd=15*60, lv=lv,
                        element=('雷', 1), interruptible=True)
        self.max_charges = 2  # 最大使用次数
        self.current_charges = 2  # 当前使用次数
        self.last_use_time = [-self.cd] * self.max_charges  # 每个充能的最后使用时间
        self.normal_hit_frame = 30  # 普通状态命中帧
        self.normal_total_frames = 46  # 普通状态总帧数
        self.passion_hit_frame = 24  # 炽热激情状态命中帧
        self.passion_total_frames = 48  # 炽热激情状态总帧数
        self.damageMultipiler = {
            '突进伤害': [74.48, 80.07, 85.65, 93.1, 98.69, 104.27, 111.72, 119.17, 126.62, 
                        134.06, 141.51, 148.96, 158.27, 167.58, 176.89],
            '炽热激情状态突进伤害': [106.4, 114.38, 122.36, 133, 140.98, 148.96, 159.6, 170.24,
                               180.88, 191.52, 202.16, 212.8, 226.1, 239.4, 252.7],
        }
        
    def update_charges(self):
        """更新当前充能次数，基于各充能槽位的冷却状态"""
        current_time = GetCurrentTime()
        available = 0
        for i in range(self.max_charges):
            if current_time >= self.last_use_time[i] + self.cd:
                available += 1
        self.current_charges = min(available, self.max_charges)

    def start(self, caster):
        self.update_charges()
        if self.current_charges <= 0:
            get_emulation_logger().log_effect("当前无可用充能")
            return False

        # 找到第一个可用的充能槽位
        current_time = GetCurrentTime()
        used_index = -1
        for i in range(self.max_charges):
            if current_time >= self.last_use_time[i] + self.cd:
                used_index = i
                break
        if used_index == -1:
            return False  # 无可用充能，不应发生

        self.current_frame = 0
        self.caster = caster
        # 标记该充能槽位已使用
        self.last_use_time[used_index] = current_time
        self.current_charges -= 1

        # 根据炽热激情状态选择帧数和倍率
        passion_effect = next((e for e in caster.active_effects if isinstance(e, PassionEffect)), None)
        if passion_effect:
            self.hit_frame = self.passion_hit_frame
            self.total_frames = self.passion_total_frames
        else:
            self.hit_frame = self.normal_hit_frame
            self.total_frames = self.normal_total_frames

        caster.gain_night_soul(20)
        
        # 应用逐击效果
        chase_effect = ChaseEffect(caster)
        chase_effect.apply()
        return True

    def update(self,target):
        self.current_frame += 1
        if self.current_frame >= self.total_frames:
            self.on_finish()
            return True
        self.on_frame_update(target)
        return False

    def on_frame_update(self, target):
        if self.current_frame == self.hit_frame:
            # 检查炽热激情状态
            passion_effect = next((e for e in self.caster.active_effects if isinstance(e, PassionEffect)), None)
            
            if passion_effect:
                damage_key = '炽热激情状态突进伤害'
                skill_name = f'炽热激情·{self.name}'
            else:
                damage_key = '突进伤害' 
                skill_name = self.name
                
            damage = Damage(
                self.damageMultipiler[damage_key][self.lv-1],
                element=self.element,
                damageType=DamageType.SKILL,
                name=skill_name
            )
            damage_event = DamageEvent(self.caster, target, damage, GetCurrentTime())
            EventBus.publish(damage_event)

            if self.caster.level >= 20:
                effect = RainbowPlungeEffect(self.caster)
                effect.apply()
            summon_energy(3, self.caster,('雷', 2))
            
        self.caster.movement += 4.347

    def on_finish(self):
        return super().on_finish()
    
    def on_interrupt(self):
        return super().on_interrupt()

class PassionEffect(Effect, EventHandler):
    """炽热激情效果"""
    def __init__(self, character, duration = 15*60):
        super().__init__(character, duration)
        self.name = '炽热激情'
        self.character = character
        self.start_time = GetCurrentTime()
        self.msg = f"""
        <p><span style="color: #faf8f0; font-size: 14pt;">{self.character.name} - {self.name}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">在炽热激情状态下，
        瓦雷莎的普通攻击、元素战技和元素爆发会分别得到对应的强化，
        并能在进行下落攻击后的短暂时间内，
        施放特殊的元素爆发。</span></p>
        """
              
    def apply(self):
        super().apply()
        passionEffect = next((e for e in self.character.active_effects if isinstance(e, PassionEffect)), None)
        if passionEffect:
            return
        # 进入炽热激情状态时，增加1次元素战技使用次数
        if self.character.Skill.current_charges < self.character.Skill.max_charges:
            t = self.character.Skill.last_use_time
            for i in range(len(t)):
                if GetCurrentTime() < t[i] + self.character.Skill.cd:
                    t[i] = GetCurrentTime() - self.character.Skill.cd
                    break

        self.character.add_effect(self)
        EventBus.subscribe(EventType.AFTER_NIGHT_SOUL_CHANGE, self)
        EventBus.subscribe(EventType.AFTER_PLUNGING_ATTACK, self)
        get_emulation_logger().log_effect("🔥 进入炽热激情状态！")
        
    def remove(self):
        super().remove()
        self.character.romve_NightSoulBlessing()
        EventBus.unsubscribe(EventType.AFTER_NIGHT_SOUL_CHANGE, self)
        EventBus.unsubscribe(EventType.AFTER_PLUNGING_ATTACK, self)
        get_emulation_logger().log_effect("🔥 炽热激情状态结束！")
        
    def handle_event(self, event):
        if event.event_type == EventType.AFTER_NIGHT_SOUL_CHANGE:
            if event.data['character'] == self.character:
                # 如果夜魂值低于最大值，结束状态
                if self.character.current_night_soul < self.character.max_night_soul:
                    self.remove()
        elif event.event_type == EventType.AFTER_PLUNGING_ATTACK:
            if event.data['character'] == self.character:
                passionEffect = next((e for e in self.character.active_effects if isinstance(e, PassionEffect)), None)
                if passionEffect:
                    effect = LimitDriveEffect(self.character)
                    effect.apply()

class LimitDriveEffect(Effect,EventHandler):
    """极限驱动效果"""
    def __init__(self, character):
        super().__init__(character, 1.5*60)
        self.name = '极限驱动'
        self.character = character
        self.msg = f"""
        <p><span style="color: #faf8f0; font-size: 14pt;">{self.character.name} - {self.name}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">在这种状态下，瓦雷莎将能够无视元素爆发的冷却时间，
        消耗更少的元素能量，施放特殊的元素爆发「闪烈降临·大火山崩落」。</span></p>
        """
        
    def apply(self):
        super().apply()
        limitDriveEffect = next((e for e in self.character.active_effects if isinstance(e, LimitDriveEffect)), None)
        if limitDriveEffect:
            limitDriveEffect.duration = self.duration
            return
        
        self.character.add_effect(self)
        get_emulation_logger().log_effect("⚡ 进入极限驱动状态！")
        EventBus.subscribe(EventType.BEFORE_SKILL, self)
        
    def remove(self):
        super().remove()
        EventBus.unsubscribe(EventType.BEFORE_SKILL, self)
        get_emulation_logger().log_effect("⚡ 极限驱动状态结束！")

    def handle_event(self, event):
        if event.event_type == EventType.BEFORE_SKILL:
            if event.data['character'] == self.character:
                limitDriveEffect = next((e for e in self.character.active_effects if isinstance(e, LimitDriveEffect)), None)
                if limitDriveEffect:
                    limitDriveEffect.remove()

class SpecialElementalBurst(EnergySkill):
    """特殊元素爆发：闪烈降临·大火山崩落"""
    def __init__(self, lv, caster):
        super().__init__(
            name="闪烈降临·大火山崩落",
            total_frames=42 + 44,
            cd=0,
            lv=lv,
            element=('雷', 1),
            interruptible=False,
            caster=caster
        )
        self.damageMultipiler = {
            '「大火山崩落」伤害':[402.64, 432.84, 463.04, 503.3, 533.5, 563.7,
                          603.96, 644.22, 684.49, 724.75, 765.02, 805.28, 855.61, 905.94, 956.27, ],
        }
        self.hit_frame = 42

    def start(self, caster):
        limitDriveEffect = next((e for e in self.caster.active_effects if isinstance(e, LimitDriveEffect)), None)
        if not limitDriveEffect:
            return
        self.caster = caster
        self.current_frame = 0
        if self.caster.elemental_energy.current_energy >= 30:
            self.caster.elemental_energy.current_energy -= 30
            self.caster._enter_passion_state(90)
            return True
        else:
            return False
        
    def on_frame_update(self, target):
        if self.current_frame == self.hit_frame:
            damage = Damage(
                self.damageMultipiler['「大火山崩落」伤害'][self.lv-1],
                element=self.element,
                damageType=DamageType.PLUNGING,
                name=self.name,
            )
            damage.setDamageData('夜魂伤害',True)
            damage_event = DamageEvent(self.caster, target, damage, GetCurrentTime())
            EventBus.publish(damage_event)
        self.caster.movement += 1.627

class ElementalBurst(EnergySkill):
    def __init__(self, lv, caster):
        super().__init__(
            name="闪烈降临！", 
            total_frames=90 +38,
            cd=20 * 60,
            lv=lv,
            element=('雷', 1),
            interruptible=False,
            caster=caster
        )
        self.original_cd = 20 * 60
        self.damageMultipiler = {
            '飞踢伤害':[345.12, 371, 396.89, 431.4, 457.28, 483.17, 517.68, 552.19, 
                    586.7, 621.22, 655.73, 690.24, 733.38, 776.52, 819.66, ],
            '炽热激情状态飞踢伤害':[575.2, 618.34, 661.48, 719, 762.14, 805.28, 862.8,
                           920.32, 977.84, 1035.36, 1092.88, 1150.4, 1222.3, 1294.2, 1366.1, ],
        }
        self.hit_frame = 90

    def on_frame_update(self, target):
        if self.current_frame == self.hit_frame:
            passion_effect = next((e for e in self.caster.active_effects if isinstance(e, PassionEffect)), None)
            damage_key = '炽热激情状态飞踢伤害' if passion_effect else '飞踢伤害'
            
            damage = Damage(
                self.damageMultipiler[damage_key][self.lv-1],
                element=self.element,
                damageType=DamageType.BURST,
                name=f'{self.name} {damage_key}',
            )
            damage.setDamageData('夜魂伤害',True)
            damage_event = DamageEvent(self.caster, target, damage, GetCurrentTime())
            EventBus.publish(damage_event)
                
            get_emulation_logger().log_effect("⚡ 正义英雄的飞踢！")
        self.caster.movement += 1.09375

class PassiveSkillEffect_1(TalentEffect):
    def __init__(self):
        super().__init__('连势，三重腾跃！')

    def apply(self, character):
        super().apply(character)

class HeroReturnsEffect(Effect):
    """英雄二度归来效果"""
    def __init__(self, character):
        super().__init__(character, 12 * 60)
        self.name = '英雄二度归来'
        self.attack_bonus = 35  # 35%攻击力提升
        self.stacks = [0,0]
        self.stack = 0
        self.max_stacks = 2  # 最大层数
        
    def apply(self):
        super().apply()
        existing = next((e for e in self.character.active_effects 
                       if isinstance(e, HeroReturnsEffect)), None)
        if existing:
            existing.character.attributePanel['攻击力%'] -= self.attack_bonus * existing.stack
            existing.stacks[existing.stacks.index(min(existing.stacks))] = self.duration
            existing.get_stacks()
            existing.character.attributePanel['攻击力%'] += self.attack_bonus * existing.stack
            get_emulation_logger().log_effect(f"⚔️ {self.character.name} 英雄二度归来效果叠加至{existing.stacks}层")
            return
            
        self.character.add_effect(self)
        self.stacks[0] = self.duration
        self.character.attributePanel['攻击力%'] += self.attack_bonus
        get_emulation_logger().log_effect(f"⚔️ {self.character.name} 获得英雄二度归来效果")
        
    def remove(self):
        super().remove()
        self.character.attributePanel['攻击力%'] -= self.attack_bonus * self.stack
        get_emulation_logger().log_effect(f"⚔️ {self.character.name} 的英雄二度归来效果消失")
        
    def get_stacks(self):
        self.stack = 0
        for i in self.stacks:
            if i > 0:
                self.stack += 1

    def update(self, target):
        s = 0
        for i in range(self.max_stacks):
            if self.stacks[i] > 0:
                self.stacks[i] -= 1
            else:
                s += 1
        if s > 0 and s < self.stack:
            self.get_stacks()
        elif s > 0 and s == self.stack:
            self.remove()

        self.msg = f"""
        <p><span style="color: #faf8f0; font-size: 14pt;">{self.character.name} - {self.name}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">瓦雷莎的攻击力提升35%</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">当前层数：{self.stack}</span></p>
        """

class PassiveSkillEffect_2(TalentEffect,EventHandler):
    def __init__(self):
        super().__init__('英雄，二度归来！')
        
    def apply(self, character):
        super().apply(character)
        EventBus.subscribe(EventType.NightsoulBurst, self)
        
    def handle_event(self, event):
        if event.event_type == EventType.NightsoulBurst:
                effect = HeroReturnsEffect(self.character)
                effect.apply()

# todo
# 1.命座1——6
# 2.元素战技次数逻辑，cd不独立，每隔一段时间恢复一次
# 3.天赋英雄二度归来层数测试
class Varesa(Natlan):
    ID = 96
    def __init__(self, level=1, skill_params=..., constellation=0):
        super().__init__(Varesa.ID, level, skill_params, constellation)

    def _init_character(self):
        super()._init_character()
        self.elemental_energy = ElementalEnergy(self, ('雷', 70))
        self.max_night_soul = 40
        self.NormalAttack = VaresaNormalAttack(lv=self.skill_params[0])
        self.PlungingAttack = VaresaPlungingAttackSkill(lv=self.skill_params[0])
        self.ChargedAttack = VaresaChargedAttack(lv=self.skill_params[0])
        self.Dash = DashSkill(22,4.5)
        self.Skill = ElementalSkill(lv=self.skill_params[1])
        self.Burst = ElementalBurst(lv=self.skill_params[2], caster=self)
        self.NormalBurst = ElementalBurst(lv=self.skill_params[2], caster=self)
        self.SpecialBurst = SpecialElementalBurst(lv=self.skill_params[2], caster=self)
        self.talent1 = PassiveSkillEffect_1()
        self.talent2 = PassiveSkillEffect_2()
        
    def _enter_passion_state(self,duration=15 * 60):
        """进入炽热激情状态"""
        self.gain_NightSoulBlessing()
        passion_effect = PassionEffect(self,duration)
        passion_effect.apply()

    def elemental_burst(self):
        limit_drive_effect = next((e for e in self.active_effects if isinstance(e, LimitDriveEffect)), None)
        if limit_drive_effect:
            self.Burst = self.SpecialBurst
        else:
            self.Burst = self.NormalBurst
        return super().elemental_burst()

    def gain_night_soul(self, amount):
        """获取夜魂值"""
        actual_amount = min(amount, self.max_night_soul - self.current_night_soul)
        EventBus.publish(NightSoulChangeEvent(
            character=self,
            amount=actual_amount,
            frame=GetCurrentTime(),
        ))
        self.current_night_soul += actual_amount
        EventBus.publish(NightSoulChangeEvent(
            character=self,
            amount=actual_amount,
            frame=GetCurrentTime(),
            before=False
        ))
        existing = next((e for e in self.active_effects 
                       if isinstance(e, PassionEffect)), None)
        
        if self.current_night_soul >= self.max_night_soul and existing is None:
            self._enter_passion_state()

Varesa_table = {
    'id': Varesa.ID,
    'name': '瓦雷莎',
    'type': '法器',
    'element': '雷',
    'rarity': 5,
    'association':'纳塔',
    'normalAttack': {'攻击次数': 3},
    'chargedAttack': {},
    'plungingAttack': {'攻击距离':['高空', '低空']},
    'skill': {},
    'burst': {},
    'dash' : {}
}
