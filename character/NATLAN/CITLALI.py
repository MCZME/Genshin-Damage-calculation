from character.NATLAN.natlan import Natlan
from core.base_class import (ChargedAttackSkill, ConstellationEffect, ElementalEnergy, 
                            EnergySkill, Infusion, NormalAttackSkill, PlungingAttackSkill, SkillBase, TalentEffect)
from core.effect.BaseEffect import ElementalDamageBoostEffect, ResistanceDebuffEffect, Effect
from core.BaseObject import ShieldObject, baseObject
from core.calculation.DamageCalculation import Damage, DamageType
from core.Event import DamageEvent, EventBus, NormalAttackEvent, ShieldEvent, EventHandler, EventType
from core.calculation.ShieldCalculation import Shield
from core.team import Team
from core.Tool import GetCurrentTime, summon_energy
from core.Logger import get_emulation_logger

class NormalAttack(NormalAttackSkill,Infusion):
    def __init__(self, lv, cd=0):
        super().__init__(lv, cd)
        Infusion.__init__(self)
        self.segment_frames = [22,32,80]
        self.end_action_frame = 20
        self.damageMultipiler = {
            1:[43.41, 46.66, 49.92, 54.26, 57.51, 60.77, 65.11, 69.45, 73.79, 78.13, 82.47, 86.81, 92.24, 97.67, 103.09, ],
            2:[38.81, 41.72, 44.64, 48.52, 51.43, 54.34, 58.22, 62.1, 65.98, 69.86, 73.75, 77.63, 82.48, 87.33, 92.18, ],
            3:[53.77, 57.8, 61.84, 67.21, 71.25, 75.28, 80.66, 86.03, 91.41, 96.79, 102.17, 107.54, 114.26, 120.99, 127.71, ],
        }

    def _apply_segment_effect(self, target):
        damage = Damage(
            damageMultipiler=self.damageMultipiler[self.current_segment+1][self.lv-1],
            element=('冰', self.apply_infusion()),
            damageType=DamageType.NORMAL,
            name=f'普通攻击 第{self.current_segment+1}段'
        )
        
        # 发布伤害事件
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

class ChargedAttack(ChargedAttackSkill):
    ...

class PlungingAttack(PlungingAttackSkill):
    ...

class FiveHeavensRainEffect(ResistanceDebuffEffect):
    """五重天的寒雨效果"""
    def __init__(self, character, traget):
        # 基础抗性降低20%，解锁命座2后额外降低20%
        debuff_value = 20
        if character.constellation >= 2:
            debuff_value += 20
        super().__init__('五重天的寒雨', character, traget, ['火', '水'], debuff_value, 12*60)  # 12秒持续时间

class ItzpapalotlObject(baseObject,EventHandler):
    """黑曜星魔·伊兹帕帕召唤物"""
    def __init__(self, character):
        super().__init__("伊兹帕帕", life_frame=20*60)  # 20秒持续时间
        self.character = character
        self.in_white_flint = False  # 白燧状态
        self.damage_interval = 2*60 
        self.last_damage_frame = -2*60  # 上次造成伤害的帧数
        self.storm_damage = [17.02, 18.3, 19.58, 21.28, 22.56, 23.83, 25.54, 
                           27.24, 28.94, 30.64, 32.35, 34.05, 36.18, 38.3, 40.43]
        self.current_character = character
        
    def apply(self):
        super().apply()
        if self.character.constellation >= 2:
            self.current_character.attributePanel['元素精通'] += 250
            get_emulation_logger().log_skill_use(f"❄️ {self.current_character.name} 获得 250 元素精通") 

            EventBus.subscribe(EventType.AFTER_CHARACTER_SWITCH, self)
    
    def handle_event(self, event):
        if event.event_type == EventType.AFTER_CHARACTER_SWITCH and self.character.constellation >= 2:
            if event.data['old_character'] == self.current_character:
                self.current_character.attributePanel['元素精通'] -= 250
                self.current_character = event.data['new_character']
                self.current_character.attributePanel['元素精通'] += 250
                get_emulation_logger().log_skill_use(f"❄️ {self.current_character.name} 获得 250 元素精通")

    def on_frame_update(self, target):
        # 检查夜魂值决定是否进入白燧状态
        if ((self.character.current_night_soul >= 50 or self.character.constellation >= 6) 
            and not self.in_white_flint):
            self.in_white_flint = True
            get_emulation_logger().log_skill_use("❄️ 伊兹帕帕进入白燧状态")
            
        # 白燧状态下每秒造成伤害并消耗夜魂值
        current_frame = GetCurrentTime()
        if self.in_white_flint:
            if current_frame - self.last_damage_frame >= self.damage_interval:
                # 造成霜陨风暴伤害(包含元素精通加成)
                base_damage = self.storm_damage[self.character.skill_params[1]-1]
                damage = Damage(
                    base_damage,
                    ('冰', 1),
                    DamageType.SKILL,
                    '霜陨风暴'
                )
                damage.setDamageData('夜魂伤害', True)
                event = DamageEvent(self.character, target, damage, current_frame)
                EventBus.publish(event)
                
                self.last_damage_frame = current_frame
                
                # 夜魂值耗尽时退出白燧状态
                if self.character.current_night_soul <= 0 and self.character.constellation < 6:
                    self.in_white_flint = False
                    get_emulation_logger().log_skill_use("❄️ 伊兹帕帕退出白燧状态")
    
    def update(self, target):
        super().update(target)
        if self.in_white_flint:
            # 每秒消耗8点夜魂值
            self.character.consume_night_soul(8/60)

    def on_finish(self, target):
        # 召唤物退场时结束夜魂加持
        if self.character.Nightsoul_Blessing:
            self.character.romve_NightSoulBlessing()
        get_emulation_logger().log_skill_use("❄️ 伊兹帕帕退场")
        if self.character.constellation >= 1:
            whiteStarDress = next((e for e in self.character.active_effects
                             if isinstance(e, WhiteStarDressEffect)), None)
            if whiteStarDress:
                whiteStarDress.remove()
        if self.character.constellation >= 2:
            self.current_character.attributePanel['元素精通'] -= 250
        super().on_finish(target)

class ElementalSkill(SkillBase):
    """元素战技：霜昼黑星"""
    def __init__(self, lv):
        super().__init__(
            name="霜昼黑星",
            total_frames=61,
            cd=16*60,
            lv=lv,
            element=('冰', 1),
            interruptible=True
        )
        self.hit_frame = 29  # 伤害触发帧
        self.shield_frame = 29+25  # 护盾触发帧
        self.damageMultipiler = [72.96, 78.43, 83.9, 91.2, 96.67, 102.14, 109.44, 
                                116.74, 124.03, 131.33, 138.62, 145.92, 155.04, 164.16, 173.28]
        self.shield_base = [1386.68, 1525.36, 1675.61, 1837.41, 2010.77, 2195.68, 
                          2392.16, 2600.19, 2819.77, 3050.92, 3293.62, 3547.88, 3813.7, 4091.07, 4380]
        self.shield_em = [576, 619.2, 662.4, 720, 763.2, 806.4, 864, 
                         921.6, 979.2, 1036.8, 1094.4, 1152, 1224, 1296, 1368]
        
    def start(self, caster):
        if not super().start(caster):
            return False
        get_emulation_logger().log_skill_use("❄️ 施放霜昼黑星")
        return True
        
    def on_frame_update(self, target):
        if self.current_frame == self.hit_frame:
            # 召唤伊兹帕帕
            izpapalotl = ItzpapalotlObject(self.caster)
            izpapalotl.apply()
            # 造成冰元素范围伤害
            damage = Damage(
                self.damageMultipiler[self.lv-1],
                self.element,
                DamageType.SKILL,
                '霜昼黑星'
            )
            damage.setDamageData('夜魂伤害', True)
            event = DamageEvent(self.caster, target, damage, GetCurrentTime())
            EventBus.publish(event)
            # 获得24点夜魂值并进入加持状态
            self.caster.gain_night_soul(24)
            if not self.caster.Nightsoul_Blessing:
                self.caster.gain_NightSoulBlessing()
        if self.current_frame == self.shield_frame:
            # 施加白曜护盾
            shield_value = (self.shield_em[self.lv-1] * self.caster.attributePanel['元素精通'] / 100
                          + self.shield_base[self.lv-1]) 
            shield = Shield(shield_value)
            event = ShieldEvent(self.caster, shield, GetCurrentTime())
            EventBus.publish(event)
            shield = ShieldObject(
                character=self.caster,
                name="白曜护盾",
                element_type='冰',
                shield_value=event.data['shield'].shield_value,
                duration=20*60  # 20秒持续时间
            )
            shield.apply()

            summon_energy(5, self.caster, ('冰', 2))

    def on_interrupt(self):
        return super().on_interrupt()
    
    def on_finish(self):
        return super().on_finish()

class SkeletonSpiritObject(baseObject):
    """宿灵之髑召唤物"""
    def __init__(self, character, lv):
        super().__init__("宿灵之髑", life_frame=60)
        self.character = character
        self.lv = lv
        self.damage = [134.4, 144.48, 154.56, 168, 178.08, 188.16, 201.6, 
                      215.04, 228.48, 241.92, 255.36, 268.8, 285.6, 302.4, 319.2]
        
    def on_finish(self, target):
        super().on_finish(target)
        self._attack(target)

    def on_frame_update(self, target):
        return super().on_frame_update(target)

    def _attack(self, target):
        # 爆炸造成伤害并恢复夜魂值
        damage = Damage(
            self.damage[self.lv-1],
            ('冰', 1),
            DamageType.BURST,
            '宿灵之髑爆炸'
        )
        damage.setDamageData('夜魂伤害', True)
        event = DamageEvent(self.character, target, damage, GetCurrentTime())
        EventBus.publish(event)
        
        # 恢复3点夜魂值
        self.character.gain_night_soul(3)
        get_emulation_logger().log_skill_use("❄️ 宿灵之髑爆炸，恢复夜魂值")

class ElementalBurst(EnergySkill):
    """元素爆发：诸曜饬令"""
    def __init__(self, lv):
        super().__init__(
            name="诸曜饬令",
            total_frames=138,
            cd=15*60,
            lv=lv,
            element=('冰', 2),
            interruptible=False
        )
        self.hit_frame = 106  # 冰风暴伤害触发帧
        self.spawn_frame = 106+30  # 宿灵之髑召唤帧
        self.storm_damage = [537.6, 577.92, 618.24, 672, 712.32, 752.64, 
                           806.4, 860.16, 913.92, 967.68, 1021.44, 1075.2, 1142.4, 1209.6, 1276.8]
        
    def start(self, caster):
        if not super().start(caster):
            return False
        get_emulation_logger().log_skill_use("❄️ 施放诸曜饬令")
        return True
        
    def on_frame_update(self, target):
        if self.current_frame == self.hit_frame:
            # 冰风暴造成范围伤害(包含元素精通加成)
            base_damage = self.storm_damage[self.lv-1]
            damage = Damage(
                base_damage,
                self.element,
                DamageType.BURST,
                '诸曜饬令·冰风暴'
            )
            damage.setDamageData('夜魂伤害', True)
            event = DamageEvent(self.caster, target, damage, GetCurrentTime())
            EventBus.publish(event)
            
            # 恢复24点夜魂值
            self.caster.gain_night_soul(24)
            
        elif self.current_frame == self.spawn_frame:
            # 召唤1个宿灵之髑
            spirit = SkeletonSpiritObject(self.caster, self.lv)
            spirit.apply()

class PassiveSkillEffect_1(TalentEffect,EventHandler):
    def __init__(self):
        super().__init__('五重天的寒雨')

    def apply(self, character):
        super().apply(character)
        self.last_recovery_time = -9999
        self.recovery_interval = 8*60  # 8秒冷却

        EventBus.subscribe(EventType.AFTER_MELT, self)
        EventBus.subscribe(EventType.AFTER_FREEZE, self)

    def handle_event(self, event):
        if event.event_type in (EventType.AFTER_MELT, EventType.AFTER_FREEZE):
            itzpapa = next((x for x in Team.active_objects if isinstance(x, ItzpapalotlObject)), None)
            if itzpapa:
                target = event.data['elementalReaction'].target
                effect = FiveHeavensRainEffect(self.character,target)
                effect.apply()
                if event.frame - self.last_recovery_time > self.recovery_interval:
                    self.last_recovery_time = event.frame
                    self.character.gain_night_soul(16)
                    get_emulation_logger().log_skill_use("❄️ 天赋「五重天的寒雨」触发，恢复16点夜魂值")

class PassiveSkillEffect_2(TalentEffect,EventHandler):
    """天赋2：白燧蝶的星衣"""
    def __init__(self):
        super().__init__('白燧蝶的星衣')
    
    def apply(self, character):
        super().apply(character)
        EventBus.subscribe(EventType.NightsoulBurst, self)
        EventBus.subscribe(EventType.BEFORE_FIXED_DAMAGE, self)
    
    def handle_event(self, event):
        if event.event_type == EventType.NightsoulBurst:
            # 队伍角色触发夜魂迸发时恢复4点夜魂值
            self.character.gain_night_soul(4)
            get_emulation_logger().log_skill_use(f"❄️ 天赋「白燧蝶的星衣」触发，恢复4点夜魂值")
        elif event.event_type == EventType.BEFORE_FIXED_DAMAGE and event.data['character'] == self.character:
            if event.data['damage'].damageType == DamageType.BURST and event.data['damage'].name == '诸曜饬令·冰风暴':
                event.data['damage'].panel['固定伤害基础值加成'] += self.character.attributePanel['元素精通'] * 12
                event.data['damage'].setDamageData('白燧蝶的星衣_伤害值加成', self.character.attributePanel['元素精通'] * 12)
            elif event.data['damage'].damageType == DamageType.SKILL and event.data['damage'].name == '霜陨风暴':
                event.data['damage'].panel['固定伤害基础值加成'] += self.character.attributePanel['元素精通'] * 0.9
                event.data['damage'].setDamageData('白燧蝶的星衣_伤害值加成', self.character.attributePanel['元素精通'] * 0.9)

class WhiteStarDressEffect(Effect,EventHandler):
    """白星之裙效果"""
    def __init__(self, character):
        super().__init__(character, 10)
        self.name = '白星之裙'
        self.star_blade_stacks = 0 # 星刃层数
        self.last_reaction_time = -9999
        self.reaction_cooldown = 8 * 60
        self.msg = f"""
        <p><span style="color: #faf8f0; font-size: 14pt;">{self.character.name} - {self.name}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">除茜特菈莉外的附近的当前场上角色的
        普通攻击、重击、下落攻击、元素战技或元素爆发造成伤害时，
        将消耗1层「星刃」，提升造成的伤害，提升值相当于茜特菈莉元素精通的200%。</span></p>
        """
        
    def apply(self):
        super().apply()
        whiteStarDress = next((e for e in self.character.active_effects
                             if isinstance(e, WhiteStarDressEffect)), None)
        if whiteStarDress:
            whiteStarDress.star_blade_stacks = 10
            return

        self.star_blade_stacks = 10
        self.character.add_effect(self)
        get_emulation_logger().log_effect(f"{self.character.name}获得{self.name}效果")
        EventBus.subscribe(EventType.BEFORE_FIXED_DAMAGE, self)
        EventBus.subscribe(EventType.AFTER_MELT, self)
        EventBus.subscribe(EventType.AFTER_FREEZE, self)
        
    def remove(self):
        super().remove()
        get_emulation_logger().log_effect(f"{self.character.name}: {self.name}效果结束")

    def update(self, target):
        pass
    
    def handle_event(self, event):
        if event.event_type == EventType.BEFORE_FIXED_DAMAGE:
            if event.data['damage'].damageType != DamageType.REACTION and \
               event.data['character'] != self.character and \
               event.data['character'].on_field and \
               self.star_blade_stacks > 0:
                event.data['damage'].setDamageData('白星之裙', self.character.attributePanel['元素精通'] * 2)
                event.data['damage'].panel['固定伤害基础值加成'] += self.character.attributePanel['元素精通'] * 2
                self.star_blade_stacks -= 1
        elif event.event_type in (EventType.AFTER_MELT, EventType.AFTER_FREEZE):
            if event.frame - self.last_reaction_time > self.reaction_cooldown:
                self.last_reaction_time = event.frame
                self.star_blade_stacks += 3

class ConstellationEffect_1(ConstellationEffect, EventHandler):
    """命座1：四百星的芒刃"""
    def __init__(self):
        super().__init__('四百星的芒刃')
        
    def apply(self, character):
        super().apply(character)
        EventBus.subscribe(EventType.AFTER_SKILL, self)
        
    def handle_event(self, event):
        # 元素战技施放时触发
        if event.event_type == EventType.AFTER_SKILL and \
           event.data['character'] == self.character:
            # 应用白星之裙效果
            effect = WhiteStarDressEffect(self.character)
            effect.apply()
            get_emulation_logger().log_skill_use("✨ 命座1「四百星的芒刃」触发，获得10层星刃")

class ConstellationEffect_2(ConstellationEffect):
    """命座2：吞心者的巡行"""
    def __init__(self):
        super().__init__('吞心者的巡行')
        
    def apply(self, character):
        super().apply(character)
        # 常驻元素精通提升125点
        character.attributePanel['元素精通'] += 125

class ConstellationEffect_3(ConstellationEffect):
    def __init__(self):
        super().__init__('云中蛇的羽冠')

    def apply(self, character):
        super().apply(character)
        self.character.Skill.lv = min(15, self.character.Skill.lv + 3)

class ConstellationEffect_4(ConstellationEffect, EventHandler):
    def __init__(self):
        super().__init__('拒亡者的灵髑')
        self.last_tigger_time = -9999
        self.inveral = 8 * 60

    def apply(self, character):
        super().apply(character)
        EventBus.subscribe(EventType.AFTER_DAMAGE, self)
        EventBus.subscribe(EventType.BEFORE_FIXED_DAMAGE, self)

    def handle_event(self, event):
        if event.event_type == EventType.AFTER_DAMAGE and \
           event.data['damage'].damageType == DamageType.SKILL and \
           event.data['character'] == self.character and \
           event.data['damage'].name == '霜昼黑星':
            if event.frame - self.last_tigger_time > self.inveral:
                self.last_tigger_time = event.frame
                SkeletonSpiritObsidianObject(self.character).apply()
        elif event.event_type == EventType.BEFORE_FIXED_DAMAGE and \
           event.data['damage'].damageType == DamageType.SKILL and \
           event.data['character'] == self.character and \
           event.data['damage'].name == '宿灵之髑·黑星':
            event.data['damage'].panel['固定伤害基础值加成'] += self.character.attributePanel['元素精通'] * 18
            event.data['damage'].setDamageData('拒亡者的灵髑', self.character.attributePanel['元素精通'] * 18)

class SkeletonSpiritObsidianObject(SkeletonSpiritObject):
    def __init__(self, character):
        super().__init__(character,0)
        self.name = '宿灵之髑·黑星'

    def _attack(self, target):
        damage = Damage(0,('冰',1),DamageType.SKILL,self.name)
        damage.setDamageData('夜魂伤害',True)
        EventBus.publish(DamageEvent(self.character, target, damage,GetCurrentTime()))

        self.character.gain_night_soul(16)
        summon_energy(1, self.character, ('无', 8), True, True, 0)

class ConstellationEffect_5(ConstellationEffect):
    def __init__(self):
        super().__init__('五恶曜的咒缚')

    def apply(self, character):
        super().apply(character)
        self.character.Burst.lv = min(15, self.character.Burst.lv + 3)

class ConstellationEffect_6(ConstellationEffect, EventHandler):
    def __init__(self):
        super().__init__('原动天的密契')
        self.consumed_night_soul = 0

    def apply(self, character):
        super().apply(character)
        EventBus.subscribe(EventType.AFTER_NIGHT_SOUL_CHANGE, self)

    def handle_event(self, event):
        if event.event_type == EventType.AFTER_NIGHT_SOUL_CHANGE and \
           event.data['character'] == self.character and \
           event.data['amount'] <= 0:
            self.consumed_night_soul -= event.data['amount']
            cifra_of_the_secret_law_point = min(40, int(self.consumed_night_soul))
            for c in Team.team:
                PyroAndHydroDmgBonus(self.character, c, cifra_of_the_secret_law_point).apply()

class PyroAndHydroDmgBonus(ElementalDamageBoostEffect,EventHandler):
    def __init__(self, character, current_character, point):
        super().__init__(character, current_character, '火水元素伤害加成',('火', '水'), 0, 10)
        self.point = point
        
    def _update_dmg_bonus(self):
        self.element_dmg_bonus = self.point * 1.5
        self.dmg_bonus = self.point * 2.5

    def apply(self):
        self.is_active = True
        existing = next((e for e in self.current_character.active_effects if isinstance(e, PyroAndHydroDmgBonus)), None)
        if existing:
            existing.romoveEffect()
            existing.point = self.point
            existing._update_dmg_bonus()
            existing.setEffect()
            return
        self._update_dmg_bonus()
        self.setEffect()
        self.current_character.add_effect(self)
        EventBus.subscribe(EventType.AFTER_SKILL, self)
        EventBus.subscribe(EventType.OBJECT_DESTROY, self)
        get_emulation_logger().log_effect(f'{self.current_character.name}获得了{self.name}')

    def setEffect(self):
        self.msg = f"""
            <p><span style="color: #faf8f0; font-size: 14pt;">{self.character.name} - {self.name}</span></p>
            <p><span style="color: #c0e4e6; font-size: 12pt;">获得{self.element_dmg_bonus:.2f}%水火元素伤害加成</span></p>
        """
        for e in ['火', '水']:
            self.current_character.attributePanel[e + '元素伤害加成'] += self.element_dmg_bonus
        if self.current_character == self.character:
            self.character.attributePanel['伤害加成'] += self.dmg_bonus
            self.msg += f"""
                <p><span style="color: #c0e4e6; font-size: 12pt;">茜特菈莉获得{self.dmg_bonus:.2f}%伤害加成</span></p>
            """
        
    def romoveEffect(self):
        for e in ['火', '水']:
            self.current_character.attributePanel[e + '元素伤害加成'] -= self.element_dmg_bonus
        if self.current_character == self.character:
            self.character.attributePanel['伤害加成'] -= self.dmg_bonus

    def remove(self):
        super().remove()
        self.point = 0
        EventBus.unsubscribe(EventType.AFTER_SKILL, self)   
        EventBus.unsubscribe(EventType.OBJECT_DESTROY, self)

    def handle_event(self, event):
        if event.event_type == EventType.AFTER_SKILL and \
           event.data['character'] == self.character and \
           self.is_active:
            self.remove()
        elif event.event_type == EventType.OBJECT_DESTROY and \
            event.data['object'].name == "伊兹帕帕" and \
            self.is_active:
            self.remove()

    def update(self, target):
        ...

class CITLALI(Natlan):
    ID = 93
    def __init__(self, level=1, skill_params=[1,1,1], constellation=0):
        super().__init__(self.ID, level, skill_params, constellation)

    def _init_character(self):
        super()._init_character()
        self.elemental_energy = ElementalEnergy(self, ('冰',60))
        self.max_night_soul = 100
        self.NormalAttack = NormalAttack(lv=self.skill_params[0])
        # self.ChargeAttack = ChargedAttack()
        # self.PlungingAttack = PlungingAttack()
        self.Skill = ElementalSkill(lv=self.skill_params[1])
        self.Burst = ElementalBurst(lv=self.skill_params[2])
        self.talent1 = PassiveSkillEffect_1()
        self.talent2 = PassiveSkillEffect_2()
        self.constellation_effects[0] = ConstellationEffect_1()
        self.constellation_effects[1] = ConstellationEffect_2()
        self.constellation_effects[2] = ConstellationEffect_3()
        self.constellation_effects[3] = ConstellationEffect_4()
        self.constellation_effects[4] = ConstellationEffect_5()
        self.constellation_effects[5] = ConstellationEffect_6()
    
citlali_table = {
    'id': CITLALI.ID,
    'name': '茜特菈莉',
    'type': '法器',
    'element': '冰',
    'rarity': 5,
    'association': '纳塔',
    'normalAttack': {'攻击次数': 3},
    # 'chargedAttack': {},
    # 'plungingAttack': {'攻击距离':['高空', '低空']},
    'skill':{},
    'burst':{},
}
