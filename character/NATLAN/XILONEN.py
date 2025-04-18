from character.NATLAN.natlan import Natlan
from core.BaseClass import DashSkill, ElementalEnergy, EnergySkill, JumpSkill, NormalAttackSkill, SkillBase, TalentEffect
from core.effect.BaseEffect import DefenseBoostEffect, Effect, ResistanceDebuffEffect
from core.calculation.DamageCalculation import Damage, DamageType
from core.Event import DamageEvent, EventBus, EventHandler, EventType, GameEvent, HealEvent, NormalAttackEvent
from core.calculation.HealingCalculation import Healing, HealingType
from core.Logger import get_emulation_logger
from core.Tool import GetCurrentTime, summon_energy
from core.Team import Team

class BladeRollerEffect(Effect,EventHandler):
    """刃轮巡猎效果"""
    def __init__(self, character):
        super().__init__(character,0)
        self.name = "刃轮巡猎"
        self.is_effect = False
        self.Multipiler = [9, 12, 15, 18, 21, 24, 27, 30, 33, 36, 39, 42, 45, 48, 51]
        self.msg = f"""
        <p><span style="color: #faf8f0; font-size: 14pt;">{self.character.name} - {self.name}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">在这种状态下进行普通攻击与下落攻击时，
        将转为基于希诺宁的防御力，造成具有夜魂性质且无法被附魔覆盖的岩元素伤害。</span></p>
        """

    def apply(self):
        super().apply()
        BladeRoller = next((e for e in self.character.active_effects if isinstance(e, BladeRollerEffect)), None)
        if BladeRoller:
            return
        
        self.character.add_effect(self)

        self._update_samplers()

        EventBus.subscribe(EventType.BEFORE_NIGHTSOUL_BLESSING, self)
        EventBus.subscribe(EventType.AFTER_NIGHT_SOUL_CHANGE, self)

    def remove(self):
        super().remove()
        EventBus.unsubscribe(EventType.BEFORE_NIGHTSOUL_BLESSING, self)
        EventBus.unsubscribe(EventType.AFTER_NIGHT_SOUL_CHANGE, self)
        self.character.romve_NightSoulBlessing()
    
    def _update_samplers(self):
        n=0
        for i in Team.team:
            if i != self.character:
                if i.element in ['火', '水', '雷', '冰']:
                    self.character.samplers[n]['element'] = i.element
                    n += 1

    def handle_event(self, event):
        if event.event_type == EventType.BEFORE_NIGHTSOUL_BLESSING:
            for i in self.character.samplers:
                if i['element'] == '岩':
                    i['active'] = True
        elif event.event_type == EventType.AFTER_NIGHT_SOUL_CHANGE:
            if event.data['character'] == self.character:
                if self.character.current_night_soul == self.character.max_night_soul:
                    self.character.consume_night_soul(self.character.max_night_soul)
                    self.is_effect = True
    
    def update(self, target):
        if self.is_effect:
            effect = ResistanceDebuffEffect('源音采样',self.character,target,
                                            list(self._get_element()),
                                            self.Multipiler[self.character.skill_params[1]-1],
                                            15*60)
            effect.apply()
            self.is_effect = False
            get_emulation_logger().log_effect("🎧 源音采样生效")
            self.remove()

    def _get_element(self):
        s = set()
        for i in self.character.samplers:
            s.add(i['element'])
        return s

class XilonenNormalAttack(NormalAttackSkill):
    def __init__(self, lv):
        super().__init__(lv=lv, cd=0)
        
        # 普通攻击参数
        self.normal_segment_frames = [18, 24, 36]  # 三段剑击的帧数
        
        # 元素附着控制参数
        self.attach_sequence = [1, 0, 0, 1, 0, 0]  # 元素附着序列
        self.sequence_pos = 0  # 当前序列位置
        self.last_attach_time = 0  # 上次元素附着时间(帧数)
        self.damageMultipiler = {
            1: [51.79, 56.01, 60.22, 66.25, 70.46, 75.28, 81.9, 88.53, 95.15, 102.38, 109.61, 116.83, 124.06, 131.29, 138.51],
            2: [27.37 + 27.37, 29.6 + 29.6, 31.83 + 31.83, 35.01 + 35.01, 37.24 + 37.24, 39.79 + 39.79, 43.29 + 43.29, 46.79 + 46.79, 50.29 + 50.29, 54.11 + 54.11, 57.93 + 57.93, 61.75 + 61.75, 65.57 + 65.57, 69.39 + 69.39, 73.21 + 73.21],
            3: [72.95, 78.89, 84.83, 93.31, 99.25, 106.03, 115.36, 124.69, 134.02, 144.2, 154.38, 164.56, 174.74, 184.92, 195.1]
        }
        
        # 刃轮巡猎参数
        self.night_soul_segment_frames = [17, 20, 33, 41]  # 四段踢击的帧数
        self.night_soul_damageMultipiler = {
            1: [56.02, 60.58, 65.14, 71.66, 76.22, 81.43, 88.59, 95.76, 102.92, 110.74, 118.56, 126.38, 134.19, 142.01, 149.83],
            2: [55.05, 59.53, 64.01, 70.41, 74.89, 80.01, 87.05, 94.09, 101.13, 108.82, 116.5, 124.18, 131.86, 139.54, 147.22],
            3: [65.82, 71.17, 76.53, 84.18, 89.54, 95.66, 104.08, 112.5, 120.92, 130.1, 139.28, 148.47, 157.65, 166.84, 176.02],
            4: [86.03, 93.03, 100.03, 110.04, 117.04, 125.04, 136.04, 147.05, 158.05, 170.05, 182.06, 194.06, 206.07, 218.07, 230.07]
        }

    def start(self, caster, n):
        # 检查夜魂加持状态
        if caster.Nightsoul_Blessing:
            self.segment_frames = self.night_soul_segment_frames
            self.damageMultipiler = self.night_soul_damageMultipiler
            self.element = ('岩', 1)  # 岩元素伤害
        else:
            self.segment_frames = self.normal_segment_frames
            self.damageMultipiler = self.damageMultipiler
            self.element = ('物理', 0)  # 普通伤害
            
        if not super().start(caster, n):
            return False
        return True

    def _apply_segment_effect(self, target):
        if self.caster.Nightsoul_Blessing:
            current_time = GetCurrentTime()
            # 计算是否应该附着元素
            should_attach = False
            
            # 序列控制检查
            if self.sequence_pos < len(self.attach_sequence):
                should_attach = self.attach_sequence[self.sequence_pos] == 1
                self.sequence_pos += 1
            else:
                self.sequence_pos = 0
                should_attach = self.attach_sequence[self.sequence_pos] == 1
                self.sequence_pos += 1
            
            # 冷却时间控制检查 (2.5秒 = 150帧)
            if current_time - self.last_attach_time >= 150:
                should_attach = True
            
            # 更新上次附着时间
            if should_attach:
                self.last_attach_time = current_time
            
            # 夜魂状态下基于防御力的岩元素伤害
            element = ('岩', 1 if should_attach else 0)
            damage = Damage(
                damageMultipiler=self.damageMultipiler[self.current_segment+1][self.lv-1],
                element=element,
                damageType=DamageType.NORMAL,
                name=f'刃轮巡猎·{self.name} 第{self.current_segment+1}段'
            )
            damage.baseValue = "防御力"
            damage.setDamageData('夜魂伤害', True)
            damage.setDamageData('不可覆盖', True)
        else:
            damage = Damage(
                damageMultipiler=self.damageMultipiler[self.current_segment+1][self.lv-1],
                element=self.element,
                damageType=DamageType.NORMAL,
                name=f'{self.name} 第{self.current_segment+1}段'
            )
            
        damage_event = DamageEvent(self.caster, target, damage, GetCurrentTime())
        EventBus.publish(damage_event)

        # 发布普通攻击事件
        normal_attack_event = NormalAttackEvent(
            self.caster, 
            frame=GetCurrentTime(), 
            before=False,
            damage=damage,
            segment=self.current_segment+1
        )
        EventBus.publish(normal_attack_event)

class ElementalSkill(SkillBase):
    """元素战技：音火锻淬"""
    def __init__(self, lv):
        super().__init__(
            name="音火锻淬",
            total_frames=19,  # 技能动画帧数
            cd=7 * 60,
            lv=lv,
            element=('岩', 1),
            interruptible=False
        )
        self.damageMultipiler = [
            179.2, 192.64, 206.08, 224, 237.44, 250.88, 268.8, 286.72, 304.64,
            322.56, 340.48, 358.4, 380.8, 403.2, 425.6]
        self.hit_frame = 9  # 命中帧数

    def start(self, caster):
        BladeRoller = next((e for e in caster.active_effects if isinstance(e, BladeRollerEffect)), None)
        if BladeRoller:
            BladeRoller.remove()
            get_emulation_logger().log_skill_use(f'{caster.name}退出刃轮巡猎状态')
            return False
        if not super().start(caster):
            return False

        # 获得夜魂值并进入夜魂状态
        self.caster.gain_night_soul(45)
        self.caster.gain_NightSoulBlessing()

        effect = BladeRollerEffect(self.caster)
        effect.apply()

        return True

    def on_frame_update(self, target):
        if self.current_frame == self.hit_frame:
            damage = Damage(
                self.damageMultipiler[self.lv-1],
                element=('岩', 1),
                damageType=DamageType.SKILL,
                name='音火锻淬'
            )
            damage.baseValue = "防御力"
            damage.setDamageData('夜魂伤害', True)
            
            event = DamageEvent(self.caster, target, damage, GetCurrentTime())
            EventBus.publish(event)
            
            summon_energy(4, self.caster,('岩',2))
        self.caster.movement += 5.27

    def on_finish(self):
        super().on_finish()

    def on_interrupt(self):
        return super().on_interrupt()

class JoyfulRhythmEffect(Effect, EventHandler):
    """欢兴律动效果"""
    def __init__(self, character):
        super().__init__(character, 12 * 60)  # 12秒持续时间
        self.name = "欢兴律动"
        self.last_trigger_time = 0
        self.interval = 1.5 * 60
        self.healing_multiplier = [
            (104, 500.74), (111.8, 550.82), (119.6, 605.07), (130, 663.5), (137.8, 726.1),
            (145.6, 792.88), (156, 863.82), (166.4, 938.94), (176.8, 1018.24), (187.2, 1101.71),
            (197.6, 1189.35), (208, 1281.16), (221, 1377.15), (234, 1477.31), (247, 1581.65)
        ]
        self.current_character = character
        self.msg = f"""
        <p><span style="color: #faf8f0; font-size: 14pt;">{self.character.name} - {self.name}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">持续恢复血量</span></p>
        """

    def apply(self):
        super().apply()
        existing = next((e for e in self.current_character.active_effects if isinstance(e, JoyfulRhythmEffect)), None)
        if existing:
            existing.duration = self.duration
            return
            
        self.current_character.add_effect(self)
        EventBus.subscribe(EventType.AFTER_CHARACTER_SWITCH, self)

    def change_character(self, character):
        self.current_character.remove_effect(self)
        self.current_character = character
        self.current_character.add_effect(self)

    def handle_event(self, event):
        if event.event_type == EventType.AFTER_CHARACTER_SWITCH:
            if event.data['old_character'] == self.current_character:
                self.change_character(event.data['new_character'])

    def remove(self):
        super().remove()

    def update(self, target):
        super().update(target)
        current_time = GetCurrentTime()
        if current_time - self.last_trigger_time >= self.interval:
            self.last_trigger_time = current_time
            lv = self.character.skill_params[2] - 1
            def_mult, flat = self.healing_multiplier[lv]
            
            heal = Healing((def_mult, flat), HealingType.BURST, '欢兴律动')
            heal.base_value = '防御力'
            heal_event = HealEvent(
                self.character,
                Team.current_character,
                heal,
                current_time
            )
            EventBus.publish(heal_event)
            get_emulation_logger().log_effect("🎶 欢兴律动治疗触发")

class FierceRhythmEffect(Effect):
    """燥烈律动效果"""
    def __init__(self, character):
        super().__init__(character, 12 * 60)
        self.name = "燥烈律动"
        self.damage_multiplier = [
            281.28, 302.38, 323.47, 351.6, 372.7, 393.79, 421.92, 450.05, 
            478.18, 506.3, 534.43, 562.56, 597.72, 632.88, 668.04
        ]
        self.beat_count = 0
        self.max_beats = 2

    def apply(self):
        super().apply()
        existing = next((e for e in self.character.active_effects if isinstance(e, FierceRhythmEffect)), None)
        if existing:
            existing.duration = self.duration
            return
            
        self.character.add_effect(self)

    def remove(self):
        super().remove()

    def update(self, target):
        if self.beat_count < self.max_beats:
            self.beat_count += 1
            
            # 设置命中帧 (33,69)
            hit_frame = 33 if self.beat_count == 1 else 69
            
            damage = Damage(
                self.damage_multiplier[self.character.skill_params[2]-1],
                element=('岩', 1),
                damageType=DamageType.BURST,
                name='燥烈律动 节拍伤害'
            )
            damage.baseValue = "防御力"
            damage.setDamageData('夜魂伤害', True)
            
            event = DamageEvent(self.character, target, damage, GetCurrentTime())
            EventBus.publish(event)
            print(f"🥁 燥烈律动第{self.beat_count}次节拍伤害")
            if self.beat_count == self.max_beats:
                self.remove()
                print("🥁 燥烈律动结束")

class ElementalBurst(EnergySkill):
    """元素爆发：豹烈律动"""
    def __init__(self, lv):
        super().__init__(
            name="豹烈律动",
            total_frames=100,  # 技能动画帧数
            cd=15 * 60,  # 15秒冷却
            lv=lv,
            element=('岩', 1),
            interruptible=False,
        )
        self.damage_multiplier = [
            281.28, 302.38, 323.47, 351.6, 372.7, 393.79, 421.92, 450.05, 
            478.18, 506.3, 534.43, 562.56, 597.72, 632.88, 668.04
        ]
        self.hit_frame = 96  # 命中帧数

    def on_frame_update(self, target):
        if self.current_frame == self.hit_frame:
            # 基础伤害
            damage = Damage(
                self.damage_multiplier[self.lv-1],
                element=('岩', 1),
                damageType=DamageType.BURST,
                name='豹烈律动'
            )
            damage.baseValue = "防御力"
            damage.setDamageData('夜魂伤害', True)
            
            event = DamageEvent(self.caster, target, damage, GetCurrentTime())
            EventBus.publish(event)
            
            # 根据源音采样类型触发不同效果
            converted_count = sum(1 for s in self.caster.samplers if s['element'] != '岩')
            if converted_count >= 2:
                effect = JoyfulRhythmEffect(self.caster)
                print("🎵 触发欢兴律动效果")
            else:
                effect = FierceRhythmEffect(self.caster)
                print("🥁 触发燥烈律动效果")
                
            effect.apply()
            
            print("🎛️ 豹烈律动启动！")

class PassiveSkillEffect_1(TalentEffect,EventHandler):
    """天赋1：四境四象回声"""
    def __init__(self):
        super().__init__('四境四象回声')
        self.last_trigger_time = 0
        self.trigger_interval = 6  # 0.1秒CD (6帧)

    def apply(self, character):
        super().apply(character)
        EventBus.subscribe(EventType.BEFORE_DAMAGE_BONUS, self)
        EventBus.subscribe(EventType.AFTER_NORMAL_ATTACK, self)
        EventBus.subscribe(EventType.BEFORE_PLUNGING_ATTACK, self)

    def handle_event(self, event):
        if not self.character.Nightsoul_Blessing:
            return
        
        # 计算元素转化的源音采样数量
        converted_count = sum(1 for s in self.character.samplers if s['element'] != '岩')
            
        # 检查是否为普攻或下落攻击伤害
        if event.event_type in [EventType.AFTER_NORMAL_ATTACK, EventType.BEFORE_PLUNGING_ATTACK]:
            current_time = GetCurrentTime()
            if current_time - self.last_trigger_time < self.trigger_interval:
                return

            if converted_count >= 2:
                # 效果1：获得35点夜魂值
                self.character.gain_night_soul(35)
                self.last_trigger_time = current_time
                get_emulation_logger().log_skill_use("🎵 天赋「四境四象回声」触发，获得35点夜魂值")
        elif event.event_type == EventType.BEFORE_DAMAGE_BONUS:
            if converted_count <2 and event.data['damage'].damageType in [DamageType.NORMAL,DamageType.PLUNGING]:
                event.data['damage'].panel['伤害加成'] += 30
                event.data['damage'].setDamageData('四境四象回声_伤害加成', 30)

class PassiveSkillEffect_2(TalentEffect,EventHandler):
    """天赋2：便携铠装护层"""
    def __init__(self):
        super().__init__('便携铠装护层')
        self.colddown = 14* 60
        self.last_trigger_time = 0

    def apply(self, character):
        super().apply(character)
        EventBus.subscribe(EventType.NightsoulBurst, self)
        EventBus.subscribe(EventType.AFTER_NIGHT_SOUL_CHANGE, self)
    
    def handle_event(self, event):
        if event.event_type == EventType.NightsoulBurst:
            effect = DefenseBoostEffect(self.character, '便携铠装护层', 20, 15*60)
            effect.apply()
        elif event.event_type == EventType.AFTER_NIGHT_SOUL_CHANGE:
            if (event.data['character'] == self.character and
                event.data['amount'] == -90 and 
                GetCurrentTime() - self.last_trigger_time > self.colddown):
                get_emulation_logger().log_effect('希诺宁 便携铠装护层 触发夜魂迸发')
                NightsoulBurstEvent = GameEvent(EventType.NightsoulBurst, event.frame,character=event.data['character'])
                EventBus.publish(NightsoulBurstEvent)
    
# todo
# 希诺宁的夜魂加持状态具有如下限制：处于夜魂加持状态下时，希诺宁的夜魂值有9秒的时间限制，超过时间限制后，希诺宁的夜魂值将立刻耗竭。
# 处于夜魂加持状态下时，夜魂值耗竭后，希诺宁将无法通过固有天赋「四境四象回声」产生夜魂值。
class Xilonen(Natlan):
    ID = 89
    def __init__(self, level=1, skill_params=..., constellation=0):
        super().__init__(Xilonen.ID, level, skill_params, constellation)

    def _init_character(self):
        super()._init_character()
        self.elemental_energy = ElementalEnergy(self,('岩',60))
        self.max_night_soul = 90
        self.NormalAttack = XilonenNormalAttack(lv=self.skill_params[0])
        self.Dash = DashSkill(22,4.5)
        self.Jump = JumpSkill(30,1.33)
        self.Skill = ElementalSkill(lv=self.skill_params[1])
        self.Burst = ElementalBurst(lv=self.skill_params[2])
        self.talent1 = PassiveSkillEffect_1()
        self.talent2 = PassiveSkillEffect_2()
        
        # 初始化3个源音采样器
        self.samplers = [{'element': '岩', 'active': False} for _ in range(3)]

Xilonen_table = {
    'id': Xilonen.ID,
    'name': '希诺宁',
    'type': '单手剑',
    'element': '岩',
    'rarity': 5,
    'association':'纳塔',
    'normalAttack': {'攻击次数': 4},
    'skill': {},
    'burst': {},
    'dash': {},
    'jump': {},
}
