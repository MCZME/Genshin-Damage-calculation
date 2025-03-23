from character.NATLAN.natlan import Natlan
from setup.BaseClass import ChargedAttackSkill, ElementalEnergy, NormalAttackSkill, Damage, DamageType, SkillBase, EnergySkill, SkillSate
from setup.BaseObject import baseObject
from setup.BaseEffect import AttackBoostEffect
from setup.Event import ChargedAttackEvent, DamageEvent, EnergyChargeEvent, EventBus, EventType, GameEvent, HealEvent, NightSoulChangeEvent, NormalAttackEvent
from setup.HealingCalculation import Healing, HealingType
from setup.Team import Team
from setup.Tool import GetCurrentTime
from setup.BaseEffect import Effect
from setup.Event import EventHandler

class LightningDashEffect(Effect, EventHandler):
    """电掣雷驰效果"""
    def __init__(self, character):
        super().__init__(character)
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
        print(f"{self.character.name}获得{self.name}效果")
        
    def remove(self):
        self.character.remove_effect(self)
        EventBus.unsubscribe(EventType.AFTER_CHARGED_ATTACK, self)
        print(f"{self.character.name}: {self.name}效果结束")
        
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
            
        # 否则执行普通攻击
        if not super().start(caster,n):
            return False
        self.current_segment = 0
        self.segment_progress = 0
        self.max_segments = min(n,len(self.segment_frames))           # 实际攻击段数
        self.total_frames = sum(self.segment_frames[:self.max_segments])
        print(f"⚔️ 开始第{self.current_segment+1}段攻击")
        
        # 发布普通攻击事件（前段）
        normal_attack_event = NormalAttackEvent(self.caster, frame=GetCurrentTime())
        EventBus.publish(normal_attack_event)
        return True

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
            name='雷霆飞缒' if self.caster.Nightsoul_Blessing else self.name,
            is_nightsoul=True if self.caster.Nightsoul_Blessing else False
        )
        
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
                is_nightsoul=True
            )
            EventBus.publish(DamageEvent(self.caster, target, damage, GetCurrentTime()))
            
            # 恢复夜魂值
            self.caster.gain_night_soul(54)
            self.caster.gain_NightSoulBlessing()
            # 添加掣雷驰效果
            LightningDashEffect(self.caster).apply()

            for _ in range(4):
                energy_event = EnergyChargeEvent(self.caster,('雷', 6), GetCurrentTime())
                EventBus.publish(energy_event)
            
        return False

    def on_finish(self):
        super().on_finish()

    def on_interrupt(self):
        return super().on_interrupt()

class KineticMarkObject(baseObject):
    """动能标示对象"""
    def __init__(self, caster,max_boost):
        super().__init__(name="动能标示", life_frame=12*60) 
        self.caster = caster
        self.interval = 60  # 1秒攻击间隔（60帧）
        self.last_attack_time = -60  # 立即开始第一次攻击
        self.original_boost = 0  # 上一次攻击力加成
        self.max_boost = max_boost  # 最大攻击力加成
        self.current_character = caster # 记录当前角色

    def on_frame_update(self, target):
        if self.current_frame - self.last_attack_time >= self.interval:
            self._romve_boost()
            self._apply_boost()
            self.last_attack_time = self.current_frame

    def _apply_boost(self):
        if self.caster.current_night_soul > 42:
            # 夜魂值少于42点时的加成
            boost = self._get_attack() * self.caster.current_night_soul * 0.5
            t='高夜魂'
        else:
            # 夜魂值至少42点时的炽烈声援模式
            boost = self._get_attack() * 0.27
            t='低夜魂'
        if boost > self.max_boost:
            boost = self.max_boost
        self.current_character.attributePanel['固定攻击力'] += boost
        print(f"⚡ {self.current_character.name} 获得 {t} 动能标示攻击力加成")
        self.original_boost = boost

    def _get_attack(self):
        return (self.caster.attributePanel['攻击力'] * (1+self.caster.attributePanel['攻击力%'] / 100)
                + self.caster.attributePanel['固定攻击力'])

    def _romve_boost(self):
        self.current_character.attributePanel['固定攻击力'] -= self.original_boost
        print(f"⚡ {self.current_character.name} 移除动能标示攻击力加成")


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
            state=SkillSate.OnField,
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
            print("⚡ 召唤动能标示！")

        return False

class WarmUpEffect(Effect, EventHandler):
    """热身效应"""
    def __init__(self, character):
        super().__init__(character)
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
        print(f"{self.character.name}获得{self.name}效果")
        
    def remove(self):
        self.character.remove_effect(self)
        EventBus.unsubscribe(EventType.AFTER_NIGHT_SOUL_CHANGE, self)
        print(f"{self.character.name}: {self.name}效果结束")
        
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

class PassiveSkillEffect_2(Effect, EventHandler):
    """动能梯度测验"""
    def __init__(self):
        super().__init__('动能梯度测验')
        EventBus.subscribe(EventType.NightsoulBurst, self)
        
    def apply(self, character):
        self.character = character
        
    def handle_event(self, event: GameEvent):
        if event.event_type == EventType.NightsoulBurst:
            WarmUpEffect(self.character).apply()

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

    def update(self, target):
        return super().update(target)