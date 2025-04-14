from character.NATLAN.natlan import Natlan
from setup.BaseClass import ChargedAttackSkill, ConstellationEffect, ElementalEnergy, NormalAttackSkill, Damage, DamageType, SkillBase, EnergySkill, TalentEffect
from setup.BaseObject import baseObject
from setup.Effect.BaseEffect import AttackBoostEffect, DamageBoostEffect
from setup.Event import ChargedAttackEvent, DamageEvent, EventBus, EventType, GameEvent, HealEvent
from setup.HealingCalculation import Healing, HealingType
from setup.Logger import get_emulation_logger
from setup.Team import Team
from setup.Tool import GetCurrentTime, summon_energy
from setup.Effect.BaseEffect import Effect
from setup.Event import EventHandler

class LightningDashEffect(Effect, EventHandler):
    """电掣雷驰效果"""
    def __init__(self, character):
        super().__init__(character,5*60)
        self.name = '电掣雷驰'
        self.duration = 5*60
        EventBus.subscribe(EventType.AFTER_CHARGED_ATTACK, self)
        
    def apply(self):
        # 检查现有效果并刷新持续时间
        existing = next((e for e in self.character.active_effects 
                       if isinstance(e, LightningDashEffect) and e.name == self.name), None)
        if existing:
            existing.duration = self.duration
            return
            
        self.character.add_effect(self)
        get_emulation_logger().log_effect(f"{self.character.name}获得{self.name}效果")
        
    def remove(self):
        self.character.remove_effect(self)
        EventBus.unsubscribe(EventType.AFTER_CHARGED_ATTACK, self)
        get_emulation_logger().log_effect(f"{self.character.name}: {self.name}效果结束")
        
    def handle_event(self, event: GameEvent):
        if event.event_type == EventType.AFTER_CHARGED_ATTACK and event.data['character'] == self.character:
            self.remove()

class IansanNormalAttack(NormalAttackSkill):
    def __init__(self, lv):
        super().__init__(lv=lv)
        self.segment_frames = [10, 20, 30]  # 三段攻击的帧数分布
        self.damageMultipiler = {
            1: [46.98, 50.8, 54.62, 60.09, 63.91, 68.28, 74.29, 80.3, 86.3, 92.86, 99.41, 105.97, 112.52, 119.08, 125.63],
            2: [42.76, 46.25, 49.73, 54.7, 58.18, 62.16, 67.63, 73.1, 78.57, 84.53, 90.5, 96.47, 102.44, 108.4, 114.37],
            3: [64.39, 69.63, 74.87, 82.36, 87.6, 93.59, 101.82, 110.06, 118.29, 127.28, 136.26, 145.25, 154.23, 163.22, 172.2]
        }

    def start(self, caster, n):
        # 检查电掣雷驰效果
        has_lightning_dash = any(isinstance(effect, LightningDashEffect) 
                             for effect in caster.active_effects)
        
        if has_lightning_dash:
            # 如果有电掣雷驰效果，直接触发重击
            caster.charged_attack()
            return False
            
        return super().start(caster, n)

class IansanChargedAttack(ChargedAttackSkill):
    def __init__(self, lv, total_frames=27+20, cd=0):
        super().__init__(lv=lv, total_frames=total_frames, cd=cd)
        self.element = ('雷', 1)
        self.normal_hit_frame = 27
        self.normal_total_frames = self.normal_hit_frame + 20
        self.damageMultipiler = [100.28, 108.44, 116.6, 128.26, 136.42, 145.75, 158.58, 171.4, 
                                 184.23, 198.22, 212.21, 226.2, 240.2, 254.19, 268.18, ]
        # 夜魂状态参数
        self.nightsoul_hit_frame = 28
        self.nightsoul_total_frames = self.nightsoul_hit_frame + 18
        self.nightsoul_damageMultipiler = [84.19, 91.05, 97.9, 107.69, 114.54, 122.37, 133.14,
                                        143.91, 154.68, 166.43, 178.18, 189.93, 201.67, 213.42, 225.17, ]


    def start(self, caster):
        if not super().start(caster):
            return False

        if self.caster.Nightsoul_Blessing:
            self.hit_frame = self.nightsoul_hit_frame
            self.total_frames = self.nightsoul_total_frames
            self.damageMultipiler = self.nightsoul_damageMultipiler
        else:
            self.hit_frame = self.normal_hit_frame
            self.total_frames = self.normal_total_frames
            self.damageMultipiler = self.damageMultipiler           
        # 检查电掣雷驰效果
        has_lightning_dash = any(isinstance(effect, LightningDashEffect) 
                             for effect in caster.active_effects)
        if has_lightning_dash:
            self.hit_frame = 16
            self.total_frames = 24 
        return True

    def _apply_attack(self, target):
        event = ChargedAttackEvent(self.caster, frame=GetCurrentTime())
        EventBus.publish(event)
        
        clamped_lv = min(max(self.lv, 1), 15) - 1
        
        damage = Damage(
            damageMultipiler=self.damageMultipiler[clamped_lv],
            element=self.element if self.caster.Nightsoul_Blessing else ('物理',0),
            damageType=DamageType.CHARGED,
            name='雷霆飞缒' if self.caster.Nightsoul_Blessing else self.name
        )
        damage.setDamageData('夜魂伤害',True if self.caster.Nightsoul_Blessing else False)
        # 触发天赋1效果
        if self.caster.Nightsoul_Blessing and self.caster.level >= 20:
            StandardActionEffect(self.caster).apply()
        
        # 发布伤害事件
        damage_event = DamageEvent(self.caster, target, damage, GetCurrentTime())
        EventBus.publish(damage_event)
            
        event = ChargedAttackEvent(self.caster, frame=GetCurrentTime(), before=False)
        EventBus.publish(event)

    def on_frame_update(self, target):
        if self.current_frame == self.hit_frame:
            self._apply_attack(target)

class ElementalSkill(SkillBase):
    """电掣雷驰技能"""
    def __init__(self, lv, total_frames=12+22, cd=16*60):
        super().__init__(name="电掣雷驰", 
                        total_frames=total_frames,
                        cd=cd,
                        lv=lv,
                        element=('雷', 1),
                        interruptible=False)
        self.hit_frame = 12  # 命中帧
        self.damageMultipiler = [286.4, 307.88, 329.36, 358, 379.48, 400.96, 
            429.6, 458.24, 486.88, 515.52, 544.16, 572.8, 608.6, 644.4, 680.2, ]

    def on_frame_update(self, target):
        if self.current_frame == self.hit_frame:
            damage = Damage(
                self.damageMultipiler[self.lv - 1],
                self.element,
                DamageType.SKILL,
                '电掣雷驰',
            )
            damage.setDamageData('夜魂伤害',True)
            EventBus.publish(DamageEvent(self.caster, target, damage, GetCurrentTime()))
            
            # 恢复夜魂值
            self.caster.gain_night_soul(54)
            self.caster.gain_NightSoulBlessing()
            # 添加掣雷驰效果
            LightningDashEffect(self.caster).apply()

            summon_energy(4,self.caster,('雷', 2))

        self.caster.movement += 3.6

    def on_finish(self):
        super().on_finish()

    def on_interrupt(self):
        return super().on_interrupt()

class KineticMarkObject(baseObject):
    """动能标示对象"""
    def __init__(self, caster,max_boost):
        # 命座6效果：持续时间延长3秒（180帧）
        base_life = 12 * 60
        if caster.constellation >= 6:
            base_life += 3 * 60
        super().__init__(name="动能标示", life_frame=base_life) 
        self.caster = caster
        self.interval = 60  # 1秒攻击间隔（60帧）
        self.last_attack_time = -60  # 立即开始第一次攻击
        self.original_boost = 0  # 上一次攻击力加成
        self.max_boost = max_boost  # 最大攻击力加成
        self.current_character = caster # 记录当前角色

        EventBus.subscribe(EventType.BEFORE_CHARACTER_SWITCH, self)
        EventBus.subscribe(EventType.AFTER_CHARACTER_SWITCH, self)


    def on_frame_update(self, target):
        if self.current_frame - self.last_attack_time >= self.interval:
            self._romve_boost()
            self._apply_boost()
            self.last_attack_time = self.current_frame
            
        # 每秒检查移动距离并恢复夜魂值
        if self.current_frame % 60 == 0:
            self._night_soul_recovery()

    def _apply_boost(self):
        if self.caster.current_night_soul < 42:
            boost = self._get_attack() * self.caster.current_night_soul * 0.5 / 100
            t='低夜魂'
        else:
            boost = self._get_attack() * 0.27
            t='高夜魂'
        if boost > self.max_boost:
            boost = self.max_boost
        self.current_character.attributePanel['固定攻击力'] += boost
        get_emulation_logger().log_effect(f"⚡ {self.current_character.name} 获得 {t} 动能标示攻击力加成")
        self.original_boost = boost

    def _get_attack(self):
        return (self.caster.attributePanel['攻击力'] * (1+self.caster.attributePanel['攻击力%'] / 100)
                + self.caster.attributePanel['固定攻击力'])

    def _romve_boost(self):
        self.current_character.attributePanel['固定攻击力'] -= self.original_boost
        get_emulation_logger().log_effect(f"⚡ {self.current_character.name} 移除动能标示攻击力加成")

    def _night_soul_recovery(self):
        """根据移动距离恢复夜魂值"""
        if self.current_character == self.caster:
            return
            
        current_movement = self.current_character.movement
        movement_delta = current_movement - self.last_movement
        self.last_movement = current_movement
        
        # 计算基础夜魂值恢复量
        night_soul_gain = movement_delta * 0.06
        if night_soul_gain > 0:
            # 检查标准动作效果
            standard_action = next((e for e in self.caster.active_effects 
                                 if isinstance(e, StandardActionEffect)), None)
            if standard_action:
                # 应用额外夜魂值恢复
                extra_gain = standard_action.extra_night_soul
                current_time = GetCurrentTime()
                
                # 检查是否触发强化恢复
                if standard_action.is_enhanced and \
                   current_time - standard_action.last_enhanced_time >= standard_action.enhanced_interval:
                    extra_gain = standard_action.enhanced_night_soul
                    standard_action.is_enhanced = False
                    standard_action.last_enhanced_time = current_time
                    get_emulation_logger().log_effect(f"⚡ {self.caster.name} 触发强化夜魂恢复，额外恢复 {extra_gain} 点")
                
                night_soul_gain += extra_gain
            
            # 检查原力激扬效果
            force_excitation = next((e for e in self.caster.active_effects 
                                   if isinstance(e, ForceExcitationEffect)), None)
            if force_excitation and force_excitation.consume_stack():
                # 消耗一层原力激扬，额外恢复4点夜魂值
                night_soul_gain += 4
                get_emulation_logger().log_effect(f"⚡ {self.caster.name} 消耗1层原力激扬，额外恢复4点夜魂值")
            
            # 检查夜魂值是否溢出
            overflow = (self.caster.current_night_soul + night_soul_gain) - self.caster.max_night_soul
            if overflow > 0:
                # 记录溢出量
                self.caster._last_overflow = overflow
                get_emulation_logger().log_effect(f"⚡ {self.caster.name} 夜魂值溢出 {overflow:.1f} 点")
                LimitBreakEffect(Team.current_character).apply()
            
            # 如果有上次溢出，额外恢复50%
            if hasattr(self.caster, '_last_overflow') and self.caster._last_overflow > 0:
                extra_recovery = self.caster._last_overflow * 0.5
                night_soul_gain += extra_recovery
                get_emulation_logger().log_effect(f"⚡ {self.caster.name} 基于上次溢出量额外恢复 {extra_recovery:.1f} 点夜魂值")
                self.caster._last_overflow = 0
            
            self.caster.gain_night_soul(night_soul_gain)
            get_emulation_logger().log_effect(f"⚡ {self.current_character.name} 移动距离 {movement_delta:.1f}，为伊安珊恢复 {night_soul_gain:.1f} 夜魂值")

    def on_finish(self, target):
        self.caster.romve_NightSoulBlessing()
        # 取消订阅事件
        EventBus.unsubscribe(EventType.BEFORE_CHARACTER_SWITCH, self)
        EventBus.unsubscribe(EventType.AFTER_CHARACTER_SWITCH, self)
        return super().on_finish(target)

    def handle_event(self, event: GameEvent):
        if event.event_type == EventType.BEFORE_CHARACTER_SWITCH:
            # 角色切换前，移除旧角色的加成
            if event.data['old_character'] == self.current_character:
                self._romve_boost()
        elif event.event_type == EventType.AFTER_CHARACTER_SWITCH:
            # 角色切换后，给新角色添加加成
            if event.data['old_character'] == self.current_character:
                self.current_character = event.data['new_character']
                self.last_movement = self.current_character.movement  # 重置移动距离记录
                self._apply_boost()

class ElementalBurst(EnergySkill):
    """元素爆发：力的三原理"""
    def __init__(self, lv, caster):
        super().__init__(
            name="力的三原理",
            total_frames=40+20,  # 技能动画帧数
            cd=18 * 60,  # 20秒冷却
            lv=lv,
            element=('雷', 1),
            interruptible=False,
            caster=caster
        )
        self.damageMultipiler = {
            '技能伤害':[430.4, 462.68, 494.96, 538, 570.28, 602.56, 645.6, 688.64, 731.68, 774.72, 817.76, 860.8, 914.6, 968.4, 1022.2, ],
            '最大攻击力加成':[330, 370, 410, 450, 490, 530, 570, 610, 650, 690, 730, 770, 810, 850, 890, ],
        }
        self.High_Nightsoul_Points_ATK_Conversion_Rate = 27
        self.Low_Nightsoul_Points_ATK_Conversion_Rate = 0.5
        self.summon_frame = 40  # 召唤动能标示的帧数

    def on_frame_update(self, target):
        if self.current_frame == self.summon_frame:
            # 造成雷元素范围伤害
            damage = Damage(
                self.damageMultipiler['技能伤害'][self.lv-1],
                element=('雷', 1),
                damageType=DamageType.BURST,
                name='力的三原理'
            )
            event = DamageEvent(self.caster, target, damage, GetCurrentTime())
            EventBus.publish(event)

            # 获得15点夜魂值并进入夜魂加持状态
            self.caster.gain_night_soul(15)
            self.caster.gain_NightSoulBlessing()

            # 召唤动能标示
            kinetic_mark = KineticMarkObject(self.caster,self.damageMultipiler['最大攻击力加成'][self.lv-1])
            kinetic_mark.apply()
            get_emulation_logger().log_effect("⚡ 召唤动能标示！")

        return False

class WarmUpEffect(Effect, EventHandler):
    """热身效应"""
    def __init__(self, character):
        super().__init__(character,10 * 60)
        self.name = '热身效应'
        self.duration = 10 * 60  # 10秒
        self.last_heal_time = -9999
        self.heal_interval = 2.8 * 60  # 2.8秒
        EventBus.subscribe(EventType.AFTER_NIGHT_SOUL_CHANGE, self)
        
    def apply(self):
        existing = next((e for e in self.character.active_effects 
                       if isinstance(e, WarmUpEffect)), None)
        if existing:
            existing.duration = self.duration
            return
            
        self.character.add_effect(self)
        get_emulation_logger().log_effect(f"{self.character.name}获得{self.name}效果")
        
    def remove(self):
        self.character.remove_effect(self)
        EventBus.unsubscribe(EventType.AFTER_NIGHT_SOUL_CHANGE, self)
        get_emulation_logger().log_effect(f"{self.character.name}: {self.name}效果结束")
        
    def handle_event(self, event: GameEvent):
        if event.event_type == EventType.AFTER_NIGHT_SOUL_CHANGE:
            if event.data['amount'] > 0:
                current_time = GetCurrentTime()
                if current_time - self.last_heal_time >= self.heal_interval:
                    self._heal()
                    self.last_heal_time = current_time
                    
    def _heal(self):
        active_character = Team.current_character
        heal = Healing(60,HealingType.PASSIVE, name='热身效应')
        event = HealEvent(self.character, active_character, heal, GetCurrentTime())
        EventBus.publish(event)

class StandardActionEffect(Effect, EventHandler):
    """标准动作效果"""
    def __init__(self, character):
        super().__init__(character, 15 * 60)
        self.name = '标准动作'
        self.duration = 15 * 60  # 15秒
        self.attack_boost = 20  # 攻击力提升20%
        self.extra_night_soul = 1  # 额外恢复1点夜魂值
        self.enhanced_night_soul = 4  # 强化后额外恢复4点
        self.last_enhanced_time = -9999  # 上次触发强化恢复的时间
        self.enhanced_interval = 2.8 * 60  # 2.8秒冷却
        self.is_enhanced = False  # 是否触发强化恢复
        EventBus.subscribe(EventType.AFTER_NIGHT_SOUL_CHANGE, self)
        
    def apply(self):
        # 检查现有效果并刷新持续时间
        existing = next((e for e in self.character.active_effects 
                       if isinstance(e, StandardActionEffect)), None)
        if existing:
            existing.duration = self.duration
            return
            
        # 应用攻击力提升
        self.original_attack = self.character.attributePanel['攻击力%']
        self.character.attributePanel['攻击力%'] += self.attack_boost
        self.character.add_effect(self)
        get_emulation_logger().log_effect(f"{self.character.name}获得{self.name}效果，攻击力提升{self.attack_boost}%")
        
    def remove(self):
        # 移除攻击力提升
        self.character.attributePanel['攻击力%'] -= self.attack_boost
        self.character.remove_effect(self)
        EventBus.unsubscribe(EventType.AFTER_NIGHT_SOUL_CHANGE, self)
        get_emulation_logger().log_effect(f"{self.character.name}: {self.name}效果结束")
        
    def handle_event(self, event: GameEvent):
        if event.event_type == EventType.AFTER_NIGHT_SOUL_CHANGE:
            # 队伍中角色消耗/恢复夜魂值后，标记下次恢复强化
            if event.data['character'] != self.character:
                self.is_enhanced = True
    
    def update(self, target):
        super().update(target)
        if not self.character.Nightsoul_Blessing:
            self.remove()

class PassiveSkillEffect_1(TalentEffect):
    """强化抗阻练习"""
    def __init__(self):
        super().__init__('强化抗阻练习')

class PassiveSkillEffect_2(TalentEffect, EventHandler):
    """动能梯度测验"""
    def __init__(self):
        super().__init__('动能梯度测验')
        
    def apply(self, character):
        self.character = character
        EventBus.subscribe(EventType.NightsoulBurst, self)
        
    def handle_event(self, event: GameEvent):
        if event.event_type == EventType.NightsoulBurst:
            WarmUpEffect(self.character).apply()

class ConstellationEffect_1(ConstellationEffect, EventHandler):
    """命座1：万事从来开头难"""
    def __init__(self):
        super().__init__('万事从来开头难')
        self.last_trigger_time = -9999
        self.trigger_interval = 18 * 60  # 18秒
        self.night_soul_consumed = 0  # 累计消耗的夜魂值
        
    def apply(self, character):
        self.character = character
        EventBus.subscribe(EventType.AFTER_NIGHT_SOUL_CHANGE, self)
        
    def handle_event(self, event: GameEvent):
        if not self.character.Nightsoul_Blessing:
            return
            
        current_time = GetCurrentTime()
        if current_time - self.last_trigger_time < self.trigger_interval:
            return
            
        # 检查夜魂值消耗
        if event.data['amount'] < 0:
            self.night_soul_consumed += abs(event.data['amount'])
            if self.night_soul_consumed >= 6:
                # 恢复15点元素能量
                summon_energy(1, self.character, ('雷', 15),True,True)
                self.last_trigger_time = current_time
                self.night_soul_consumed = 0  # 重置累计消耗
                get_emulation_logger().log_effect(f"⚡ {self.character.name} 触发命座1效果，恢复15点元素能量")

class IansanAttackBoostEffect(AttackBoostEffect,EventHandler):
    """伊安珊攻击力提升效果"""
    def __init__(self, character):
        super().__init__(character, '偷懒是健身大忌', 30, 0)
        self.current_character = character
    
    def apply(self):
        # 防止重复应用
        existing = next((e for e in self.current_character.active_effects 
                       if isinstance(e, AttackBoostEffect) and e.name == self.name), None)
        if existing:
            existing.duration = self.duration  # 刷新持续时间
            return
            
        self.current_character.add_effect(self)
        self.current_character.attributePanel['攻击力%'] += self.bonus
        get_emulation_logger().log_effect(f"{self.current_character.name} 获得 {self.name} ,攻击力提升了{self.bonus}%")
        EventBus.subscribe(EventType.AFTER_CHARACTER_SWITCH, self)

    def remove(self):
        self.current_character.attributePanel['攻击力%'] -= self.bonus
        self.current_character.remove_effect(self)
        EventBus.unsubscribe(EventType.AFTER_CHARACTER_SWITCH, self)

    def handle_event(self, event: GameEvent):
        if event.event_type == EventType.AFTER_CHARACTER_SWITCH:
            # 角色切换后，检查伊安珊是否在后台
            if not self.character.on_field:
                self.remove() 
                self.current_character = event.data['new_character']
                if self.character != Team.current_character:
                    self.apply()

    def update(self, target):
        existing = next((e for e in self.character.active_effects 
                       if isinstance(e, StandardActionEffect)), None)
        if not existing:
            self.remove()

class ConstellationEffect_2(ConstellationEffect, EventHandler):
    """命座2：偷懒是健身大忌!"""
    def __init__(self):
        super().__init__('偷懒是健身大忌!')
        
    def apply(self, character):
        EventBus.subscribe(EventType.AFTER_BURST, self)
        self.character = character
        
    def handle_event(self, event: GameEvent):
        if event.event_type == EventType.AFTER_BURST and event.data['character'] == self.character:
            # 检查是否解锁天赋1
            if self.character.level < 20:
                return   
            # 应用标准动作效果
            StandardActionEffect(self.character).apply() 
            IansanAttackBoostEffect(self.character).apply()

class ForceExcitationEffect(Effect):
    """原力激扬效果"""
    def __init__(self, character):
        super().__init__(character,0)
        self.name = '原力激扬'
        self.stacks = 0
        self.max_stacks = 2
        
    def apply(self):
        force_excitation = next((e for e in self.character.active_effects
                           if isinstance(e, ForceExcitationEffect)), None)
        if force_excitation:
            return
        else:
            self.character.add_effect(self)

    def add_stack(self):
        if self.stacks < self.max_stacks:
            self.stacks += 1
            get_emulation_logger().log_effect(f"{self.character.name} 获得1层{self.name}，当前层数：{self.stacks}")
            
    def consume_stack(self):
        if self.stacks > 0:
            self.stacks -= 1
            get_emulation_logger().log_effect(f"{self.character.name} 消耗1层{self.name}，当前层数：{self.stacks}")
            return True
        return False
    
    def update(self, target):
        existing = next((e for e in Team.active_objects 
                       if isinstance(e, KineticMarkObject)), None)
        if not existing:
            self.remove()

class ConstellationEffect_3(ConstellationEffect):
    """命座3：科学的饮食规划"""
    def __init__(self):
        super().__init__('科学的饮食规划')

    def apply(self, character):
        skill_lv = character.Skill.lv + 3
        if skill_lv > 15:
            skill_lv = 15
        character.Skill = ElementalSkill(skill_lv)

class ConstellationEffect_4(ConstellationEffect, EventHandler):
    """命座4：循序渐进是关键"""
    def __init__(self):
        super().__init__('循序渐进是关键')
        
    def apply(self, character):
        self.character = character
        self.force_excitation = None
        self.is_gain = True
        EventBus.subscribe(EventType.AFTER_BURST, self)
        
    def handle_event(self, event: GameEvent):
        if event.event_type == EventType.AFTER_BURST:
            # 检查是否是其他角色施放元素爆发
            if event.data['character'] != self.character and self.is_gain:
                # 获取或创建原力激扬效果
                self.force_excitation = next((e for e in self.character.active_effects 
                                            if isinstance(e, ForceExcitationEffect)), None)
                if not self.force_excitation:
                    self.force_excitation = ForceExcitationEffect(self.character)
                    self.force_excitation.apply()
                # 添加两层原力激扬
                self.force_excitation.add_stack()
                self.force_excitation.add_stack()
                self.is_gain = False            
            elif event.data['character'] == self.character and not self.is_gain:
                self.is_gain = True

class LimitBreakEffect(DamageBoostEffect, EventHandler):
    """极限发力效果"""
    def __init__(self, character):
        super().__init__(character,'极限发力',25,3*60)
        self.current_character = character

    def apply(self):
        # 防止重复应用
        existing = next((e for e in self.character.active_effects 
                       if isinstance(e, DamageBoostEffect) and e.name == self.name), None)
        if existing:
            existing.duration = self.duration  # 刷新持续时间
            return
        
        self.current_character.add_effect(self)
        self.current_character.attributePanel[self.attribute_name] += self.bonus
        get_emulation_logger().log_effect(f"{self.current_character.name}获得{self.name}效果")
        EventBus.subscribe(EventType.BEFORE_CHARACTER_SWITCH, self)
    
    def remove(self):
        self.current_character.attributePanel[self.attribute_name] -= self.bonus
        get_emulation_logger().log_effect(f"{self.current_character.name}: {self.name}的伤害加成效果结束")
        self.current_character.remove_effect(self)
        EventBus.unsubscribe(EventType.BEFORE_CHARACTER_SWITCH, self)

    def handle_event(self, event: GameEvent):
        if event.event_type == EventType.BEFORE_CHARACTER_SWITCH:
            if event.data['old_character'] == self.current_character:
                self.remove()
                self.current_character = event.data['new_character']
                self.apply()  

class ConstellationEffect_5(ConstellationEffect):
    """命座5：还没有到极限呢！"""
    def __init__(self):
        super().__init__('还没有到极限呢！')

    def apply(self, character):
        burst_lv = character.Burst.lv + 3
        if burst_lv > 15:
            burst_lv = 15
        character.Burst = ElementalBurst(burst_lv, character)

class ConstellationEffect_6(ConstellationEffect):
    """命座6：「沃陆之邦」的训教"""
    def __init__(self):
        super().__init__('「沃陆之邦」的训教')
        
    def apply(self, character):
        self.character = character

# 默认 位移100 25帧 v=4 一个闪避的距离 转化率r = 0.08
class Iansan(Natlan):
    ID = 97
    def __init__(self, level=1, skill_params=..., constellation=0):
        super().__init__(Iansan.ID, level, skill_params, constellation)

    def _init_character(self):
        super()._init_character()
        self.elemental_energy = ElementalEnergy(self, ('雷', 70))
        self.max_night_soul = 54
        self.Nightsoul_Blessing = False
        self.NormalAttack = IansanNormalAttack(lv=self.skill_params[0])
        self.ChargedAttack = IansanChargedAttack(lv=self.skill_params[0])
        self.Skill = ElementalSkill(lv=self.skill_params[1])
        self.Burst = ElementalBurst(lv=self.skill_params[2], caster=self)
        self.talent2 = PassiveSkillEffect_2()
        self.constellation_effects[0] = ConstellationEffect_1()
        self.constellation_effects[1] = ConstellationEffect_2()
        self.constellation_effects[2] = ConstellationEffect_3()
        self.constellation_effects[3] = ConstellationEffect_4()
        self.constellation_effects[4] = ConstellationEffect_5()
        self.constellation_effects[5] = ConstellationEffect_6()
        
    def update(self, target):
        super().update(target)
        if self.Nightsoul_Blessing:
            self.consume_night_soul(8/60)
    
    def consume_night_soul(self, amount):
        a = super().consume_night_soul(amount)
        if self.current_night_soul <= 0:
            self.romve_NightSoulBlessing()
            return True
        return a

iansan_table = {
    'id':Iansan.ID,
    'name':'伊安珊',
    'type': '长柄武器',
    'rarity': 4,
    'element': '雷',
    'association': '纳塔',
    'normalAttack':{'攻击次数':3},
    'chargedAttack':{},
    'skill':{},
    'burst':{}
}
