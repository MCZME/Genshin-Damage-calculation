import types
from character.FONTAINE.fontaine import Fontaine
from core.BaseClass import (ChargedAttackSkill, ConstellationEffect, ElementalEnergy, EnergySkill, 
                             NormalAttackSkill, PlungingAttackSkill, SkillBase, TalentEffect)
from core.effect.BaseEffect import Effect
from core.BaseObject import ArkheObject, baseObject
from core.calculation.DamageCalculation import Damage, DamageType
from core.Event import DamageEvent, EventBus, EventHandler, EventType, HealEvent, HurtEvent
from core.calculation.HealingCalculation import Healing, HealingType
from core.Logger import get_emulation_logger
from core.Team import Team
from core.Tool import GetCurrentTime, summon_energy

class ArkheAttackHandler(EventHandler):
    def __init__(self, character):
        super().__init__()
        self.character = character
        self.last_trigger_time = -360  # 初始值确保第一次攻击可以触发
        self.damageMultiplier = [9.46, 10.23, 11, 12.1, 12.87, 13.75, 14.96, 
                                 16.17, 17.38, 18.7, 20.02, 21.34, 22.66, 23.98, 25.3, ]

        EventBus.subscribe(EventType.AFTER_NORMAL_ATTACK, self)
        
    def handle_event(self, event):
        if event.event_type == EventType.AFTER_NORMAL_ATTACK and event.data['character'] == self.character:
            current_time = event.frame
            if current_time - self.last_trigger_time >= 360:
                name = '流涌之刃' if self.character.arkhe == '荒性' else '灵息之刺'
                damage = Damage(self.damageMultiplier[self.character.NormalAttack.lv - 1],
                                ('水',0),
                                DamageType.NORMAL,
                                name)
                ArkheObject(name, self.character, self.character.arkhe, damage, 18).apply()
                self.last_trigger_time = current_time

    def remove(self):
        EventBus.unsubscribe(EventType.AFTER_NORMAL_ATTACK, self)

class SalonMember(baseObject,EventHandler):
    """沙龙成员"""

    last_erengy_time = 0

    def __init__(self, character, name="沙龙成员", life_frame=0):
        super().__init__(name, life_frame)
        self.character = character
        self.hp_consumption = 0
        self.attack_interval = 60
        self.last_attack_time = 0

    def apply(self):
        super().apply()
        EventBus.subscribe(EventType.BEFORE_INDEPENDENT_DAMAGE, self)
    
    def on_frame_update(self, target):
        if self.current_frame - self.last_attack_time >= self.attack_interval:
            damage = Damage(self.damageMultiplier[self.character.Skill.lv - 1],
                            ('水',1),
                            DamageType.SKILL,
                            self.name)
            damage.setBaseValue('生命值')
            EventBus.publish(DamageEvent(self.character, target, damage, GetCurrentTime()))
            self.last_attack_time = self.current_frame
            self.summon_energy()

    def summon_energy(self):
        if GetCurrentTime() - SalonMember.last_erengy_time >= 2.5*60:
            summon_energy(1, self.character, ('水',2))
            SalonMember.last_erengy_time = GetCurrentTime()

    def on_finish(self, target):
        super().on_finish(target)
        EventBus.unsubscribe(EventType.BEFORE_INDEPENDENT_DAMAGE, self)

    def consume_character_hp(self):
        number = 0
        for c in Team.team:
            if c.currentHP/c.maxHP > 0.5:
                EventBus.publish(HurtEvent(self.character, c, self.hp_consumption*c.maxHP/100, GetCurrentTime()))
                number += 1
        return number

    def handle_event(self, event):
        if event.event_type == EventType.BEFORE_INDEPENDENT_DAMAGE and event.data['character'] == self.character:
            if event.data['damage'].name == self.name:
                number = self.consume_character_hp()
                boost = [100,110,120,130,140][number]
                event.data['damage'].setPanel('独立伤害加成', boost)
                event.data['damage'].setDamageData('独立伤害加成', boost)

class Usher(SalonMember):
    """乌瑟勋爵 - 球球章鱼形态"""
    def __init__(self, character, life_frame=0):
        super().__init__(character, "乌瑟勋爵", life_frame)
        self.character = character
        self.damageMultiplier = [5.96, 6.41, 6.85, 7.45, 7.9, 8.34, 8.94, 9.54, 10.13, 10.73, 11.32, 11.92, 12.67, 13.41, 14.16]

    def apply(self):
        super().apply()
        self.hp_consumption = 2.4
        self.attack_interval = 200
        self.last_attack_time = -self.attack_interval + 72

class Chevalmarin(SalonMember):
    """海薇玛夫人 - 泡泡海马形态"""
    def __init__(self, character, life_frame=0):
        super().__init__(character, "海薇玛夫人", life_frame)
        self.damageMultipiler = [3.23, 3.47, 3.72, 4.04, 4.28, 4.52, 4.85, 5.17, 5.49, 5.82, 6.14, 6.46, 6.87, 7.27, 7.68]

    def apply(self):
        super().apply()
        self.hp_consumption = 1.6
        self.attack_interval = 97
        self.last_attack_time = -self.attack_interval + 72

class Crabaletta(SalonMember):
    """谢贝蕾妲小姐 - 重甲蟹形态"""
    def __init__(self, character, life_frame=0):
        super().__init__(character, "谢贝蕾妲小姐", life_frame)
        self.damageMultipiler = [8.29, 8.91, 9.53, 10.36, 10.98, 11.6, 12.43, 
                                 13.26, 14.09, 14.92, 15.75, 16.58, 17.61, 18.65, 19.68]

    def apply(self):
        super().apply()
        self.hp_consumption = 3.6
        self.attack_interval = 314
        self.last_attack_time = -self.attack_interval + 30

class Singer(baseObject):
    """众水的歌者 - 芒性召唤物"""
    def __init__(self, character, life_frame=0):
        super().__init__("众水的歌者", life_frame)
        self.character = character
        self.heal_interval = 124
        self.last_heal_time = -37
        self.multipiler = [(4.8, 462.23), (5.16, 508.45), (5.52, 558.54), (6, 612.47), (6.36, 670.26), 
                           (6.72, 731.89), (7.2, 797.39), (7.68, 866.73), (8.16, 939.92), (8.64, 1016.97), 
                           (9.12, 1097.87), (9.6, 1182.63), (10.2, 1271.23), (10.8, 1363.69), (11.4, 1460)]
        
    def apply(self):
        super().apply()
        if self.character.level > 60:
            self.heal_interval *= (1 - min((self.character.maxHP // 1000) * 0.004, 0.16 ))

    def on_frame_update(self, target):
        if self.current_frame - self.last_heal_time >= self.heal_interval:
            heal = Healing(self.multipiler[self.character.Skill.lv - 1],
                           HealingType.SKILL,
                           self.name)
            heal.base_value = '生命值'
            EventBus.publish(HealEvent(self.character, Team.current_character, heal, GetCurrentTime()))
            self.last_heal_time = self.current_frame

class NormalAttack(NormalAttackSkill):
    def __init__(self, lv, cd=0):
        super().__init__(lv, cd)
        self.segment_frames = [15, 28, 32, 43]
        self.damageMultipiler = {
            1: [48.39, 52.32, 56.26, 61.89, 65.83, 70.33, 76.52, 82.71, 88.9, 95.65, 102.4, 109.15, 115.9, 122.65, 129.4],
            2: [43.73, 47.29, 50.85, 55.93, 59.49, 63.56, 69.15, 74.75, 80.34, 86.44, 92.54, 98.65, 104.75, 110.85, 116.95],
            3: [55.12, 59.61, 64.09, 70.5, 74.99, 80.12, 87.17, 94.22, 101.27, 108.96, 116.65, 124.34, 132.03, 139.72, 147.41],
            4: [73.3, 79.26, 85.23, 93.75, 99.72, 106.54, 115.91, 125.29, 134.66, 144.89, 155.12, 165.35, 175.57, 185.8, 196.03]
        }
        self.end_action_frame = 26

    def start(self, caster, n):
        self.arkhe_handler = ArkheAttackHandler(caster)
        return super().start(caster, n)

    def on_finish(self):
        super().on_finish()
        self.arkhe_handler.remove()

class ChargedAttack(ChargedAttackSkill):
    def __init__(self, lv, total_frames=47, cd=0):
        super().__init__(lv, total_frames, cd)
        self.damageMultipiler = [74.22, 80.26, 86.3, 94.93, 100.97, 107.88, 117.37, 
                                 126.86, 136.35, 146.71, 157.07, 167.42, 177.78, 188.13, 198.49]
        self.hit_frame = 32

    def _apply_attack(self, target):
        # 切换始基力属性
        old_arkhe = self.caster.arkhe
        self.caster.arkhe = '芒性' if old_arkhe == '荒性' else '荒性'
        get_emulation_logger().log_skill_use(f"🔁 {self.caster.name}切换了始基力属性为{self.caster.arkhe}")
        
        # 调用父类方法造成物理伤害
        super()._apply_attack(target)
        
        # 获取所有召唤物并计算剩余时间
        summons = [obj for obj in Team.active_objects if isinstance(obj, (SalonMember, Singer))]
        remaining_frames = summons[0].life_frame - summons[0].current_frame if summons else 0
        
        # 移除所有旧召唤物
        for obj in summons:
            obj.on_finish(target)
        
        # 创建新召唤物
        if self.caster.arkhe == '芒性':
            # 荒性→芒性：创建1个众水的歌者
            Singer(self.caster, remaining_frames).apply()
        else:
            # 芒性→荒性：创建3个沙龙成员
            Usher(self.caster, remaining_frames).apply()
            Chevalmarin(self.caster, remaining_frames).apply()
            Crabaletta(self.caster, remaining_frames).apply()

class PlungingAttack(PlungingAttackSkill):
    def __init__(self, lv, cd=0):
        super().__init__(lv, cd)
        ...

class ElementalSkill(SkillBase):
    def __init__(self, lv):
        super().__init__('孤心沙龙', 56, 20*60, lv, ('水',1))
        self.damageMultipiler = [7.86, 8.45, 9.04, 9.83, 10.42, 11.01, 11.8, 12.58, 13.37, 14.16, 14.94, 15.73, 16.71, 17.69, 18.68, ]

    def start(self, caster):
        if not super().start(caster):
            return False
        if caster.arkhe == '芒性':
            self.cd_frame = 10
        if caster.constellation >= 6:
            CenterOfAttentionEffect(caster).apply()
        return True
        
    def on_frame_update(self, target):
        if self.current_frame == 18:
            damage = Damage(self.damageMultipiler[self.lv - 1],
                            ('水', 1),
                            DamageType.SKILL,
                            self.name)
            damage.setBaseValue('生命值')
            EventBus.publish(DamageEvent(self.caster, target, damage, GetCurrentTime()))

            if self.caster.arkhe == '芒性':
                Singer(self.caster, 30*60).apply()
            elif self.caster.arkhe == '荒性':
                Usher(self.caster, 30*60).apply()
                Chevalmarin(self.caster, 30*60).apply()
                Crabaletta(self.caster, 30*60).apply()

    def on_finish(self):
        return super().on_finish()
    
    def on_interrupt(self):
        return super().on_interrupt()

class UniversalExaltationEffect(Effect):
    """普世欢腾效果"""
    def __init__(self, character, current_character,duration, burst_skill):
        super().__init__(character, duration)
        self.name = "普世欢腾"
        self.current_character = current_character
        self.burst_skill = burst_skill
        self.origin_fanfare_points = 0
        self.damage_bonus_rates = [0.07, 0.09, 0.11, 0.13, 0.15, 
                                  0.17, 0.19, 0.21, 0.23, 0.25,
                                  0.27, 0.29, 0.31, 0.33, 0.35]
        self.healing_bonus_rates = [0.01, 0.02, 0.03, 0.04, 0.05,
                                   0.06, 0.07, 0.08, 0.09, 0.1,
                                   0.11, 0.12, 0.13, 0.14, 0.15]
        
    def apply(self):
        super().apply()
        universalExaltation = next((effect for effect in self.current_character.active_effects 
                                    if isinstance(effect, UniversalExaltationEffect)), None)
        if universalExaltation:
            universalExaltation.duration = self.duration
            return
        self.current_character.add_effect(self)
        get_emulation_logger().log_effect(f"🎉 {self.current_character.name}获得了普世欢腾效果")

    def remove(self):
        self.remove_effect()
        if self.current_character == self.character:
            self.burst_skill.init()
        super().remove()
        get_emulation_logger().log_effect(f"🎉 {self.current_character.name}的普世欢腾效果消失了")

    def apply_effect(self):
        self.current_character.attributePanel['伤害加成'] += (self.damage_bonus_rates[self.burst_skill.lv - 1]*
                                                          self.burst_skill.fanfare_points)
        self.current_character.attributePanel['受治疗加成'] += (self.healing_bonus_rates[self.burst_skill.lv - 1]*
                                                           self.burst_skill.fanfare_points)
        self.origin_fanfare_points = self.burst_skill.fanfare_points

        self.msg = f"""
        <p><span style="color: #faf8f0; font-size: 14pt;">{self.character.name} - {self.name}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">根据气氛值获得伤害加成和受治疗加成</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">当前气氛值：{self.burst_skill.fanfare_points:.2f}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">伤害加成：{self.damage_bonus_rates[self.burst_skill.lv - 1] * self.burst_skill.fanfare_points:.2f}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">受治疗加成：{self.healing_bonus_rates[self.burst_skill.lv - 1] * self.burst_skill.fanfare_points:.2f}</span></p>
        """
        if self.character.constellation >= 2:
            self.msg += f"<p><span style='color: #c0e4e6; font-size: 12pt;'>当前超出上限的气氛值：{self.burst_skill.over_fanfare_points:.2f}</span></p>"
        # get_emulation_logger().log_effect(f"🎉 气氛值为{self.burst_skill.fanfare_points}")
        
    def remove_effect(self):
        self.current_character.attributePanel['伤害加成'] -= (self.damage_bonus_rates[self.burst_skill.lv - 1]*
                                                          self.origin_fanfare_points)
        self.current_character.attributePanel['受治疗加成'] -= (self.healing_bonus_rates[self.burst_skill.lv - 1]*
                                                           self.origin_fanfare_points)
        
    def update(self, target):
        self.remove_effect()
        self.apply_effect()
        super().update(target)

class ElementalBurst(EnergySkill,EventHandler):
    def __init__(self, lv):
        super().__init__('万众狂欢', 113, 15*60, lv, ('水',1))
        self.damageMultipiler = [11.41, 12.26, 13.12, 14.26, 15.11, 
                                  15.97, 17.11, 18.25, 19.39, 20.53, 
                                  21.67, 22.81, 24.24, 25.66, 27.09]
        self.fanfare_max = 300  # 气氛值上限
        self.fanfare_points = 0  # 当前气氛值
        self.over_fanfare_points = 0 # 超过上限的气氛值
        self.hit_frame = 98
        
    def add_fanfare_points(self, points):
        """增加气氛值"""
        self.fanfare_points = min(self.fanfare_points + points, self.fanfare_max)
        
    def start(self, caster):
        if not super().start(caster):
            return False
        
        EventBus.subscribe(EventType.AFTER_HEALTH_CHANGE, self)

        for member in Team.team:
            UniversalExaltationEffect(caster, member, 18*60, self).apply()

        if caster.constellation >= 1:
            self.fanfare_max = 400
            self.fanfare_points = 150

        return True
        
    def on_frame_update(self, target):
        if self.current_frame == self.hit_frame:
            # 造成水元素伤害
            damage = Damage(self.damageMultipiler[self.lv - 1],
                           ('水', 1),
                           DamageType.BURST,
                           self.name)
            damage.setBaseValue('生命值')
            EventBus.publish(DamageEvent(self.caster, target, damage, GetCurrentTime()))
    
    def on_finish(self):
        return super().on_finish()
    
    def init(self):
        self.fanfare_points = 0
        EventBus.unsubscribe(EventType.AFTER_HEALTH_CHANGE, self)
    
    def handle_event(self, event):
        if event.event_type == EventType.AFTER_HEALTH_CHANGE:
            character = event.data['character']
            self.add_fanfare_points(abs(event.data['amount']/character.maxHP)*100)

class PassiveSkillEffect_1(TalentEffect, EventHandler):
    """停不了的圆舞"""
    def __init__(self):
        super().__init__("停不了的圆舞")
        
    def apply(self,character):
        super().apply(character)
        EventBus.subscribe(EventType.AFTER_HEAL, self)
        
    def handle_event(self, event):
        if event.event_type == EventType.AFTER_HEAL:
            if (event.data['target'] == Team.current_character and 
                event.data['character'] != self.character):
                amount = event.data['healing'].final_value
                if amount > event.data['target'].maxHP - event.data['target'].currentHP:
                    EndlessWaltzEffect(self.character).apply()
                
class EndlessWaltzEffect(Effect):
    """停不了的圆舞持续治疗效果"""
    def __init__(self, character):
        super().__init__(character, 240)
        self.name = "停不了的圆舞"
        self.heal_timer = 0
        self.heal_interval = 120
        self.msg = f"""
        <p><span style="color: #c0e4e6; font-size: 12pt;">{character.name} - {self.name}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">持续治疗,芙宁娜天赋</span></p>
        """

    def apply(self):
        super().apply()
        endlessWaltz = next((effect for effect in self.character.active_effects if isinstance(effect, EndlessWaltzEffect)), None)
        if endlessWaltz:
            endlessWaltz.duration = self.duration
            return
        self.character.add_effect(self)
        get_emulation_logger().log_effect(f"♥ {self.character.name}获得{self.name}")

    def remove(self):
        super().remove()
        get_emulation_logger().log_effect(f"♥ {self.character.name}失去{self.name}")
        
    def on_frame_update(self, target):
        self.heal_timer += 1
        if self.heal_timer >= self.heal_interval:
            self.heal_timer = 0
            # 为队伍中附近角色恢复生命值
            for member in Team.team:
                heal = Healing(2, HealingType.PASSIVE, self.name,"目标")
                heal.base_value = '生命值'
                EventBus.publish(HealEvent(self.character, member, heal, GetCurrentTime()))
    
    def update(self, target):
        super().update(target)
        self.on_frame_update(target)

class PassiveSkillEffect_2(TalentEffect, EventHandler):
    """无人听的自白"""
    def __init__(self):
        super().__init__("无人听的自白")
        
    def apply(self, character):
        super().apply(character)
        EventBus.subscribe(EventType.BEFORE_DAMAGE_BONUS, self)
        
    def handle_event(self, event):
        if event.event_type == EventType.BEFORE_DAMAGE_BONUS:
            if event.data['damage'].name in ['乌瑟勋爵','海薇玛夫人','谢贝蕾妲小姐']:
                hp_bonus = min(self.character.maxHP // 1000 * 0.7, 28)
                event.data['damage'].panel['伤害加成'] += hp_bonus
                event.data['damage'].setDamageData('无人听的自白_伤害加成', hp_bonus)

class ConstellationEffect_1(ConstellationEffect):
    """「爱是难驯鸟，哀乞亦无用。」"""
    def __init__(self):
        super().__init__('「爱是难驯鸟，哀乞亦无用。」')

    def apply(self, character):
        super().apply(character)

class ConstellationEffect_2(ConstellationEffect):
    """「女人皆善变，仿若水中萍。」"""
    def __init__(self):
        super().__init__('「女人皆善变，仿若水中萍。」')

    def apply(self, character):
        super().apply(character)
        def new_add(self,points):
            if self.fanfare_points + points*2.5 > self.fanfare_max:
                self.caster.attributePanel['生命值%'] -= min(self.over_fanfare_points * 0.35,140)
                self.fanfare_points = self.fanfare_max
                self.over_fanfare_points += self.fanfare_points + points*2.5 - self.fanfare_max
                self.caster.attributePanel['生命值%'] += min(self.over_fanfare_points * 0.35,140)
            else:
                self.fanfare_points += points*2.5
        self.character.Burst.add_fanfare_points = types.MethodType(new_add, self.character.Burst)

class ConstellationEffect_3(ConstellationEffect):
    """「秘密藏心间，无人知我名。」"""
    def __init__(self):
        super().__init__('「秘密藏心间，无人知我名。」')

    def apply(self, character):
        super().apply(character)
        self.character.Burst.lv = min(15, self.character.Burst.lv + 3)

class ConstellationEffect_4(ConstellationEffect,EventHandler):
    """「若非处幽冥，怎知生可贵！」"""
    def __init__(self):
        super().__init__('「若非处幽冥，怎知生可贵！」')
        self.last_time = 0
        self.interval = 5*60

    def apply(self, character):
        super().apply(character)
        EventBus.subscribe(EventType.AFTER_DAMAGE, self)
        EventBus.subscribe(EventType.AFTER_HEAL, self)

    def handle_event(self, event):
        if event.event_type in [EventType.AFTER_DAMAGE, EventType.AFTER_HEAL]:
            if GetCurrentTime() - self.last_time >= self.interval:
                self.last_time = GetCurrentTime()
                summon_energy(1, self.character, ('无', 4),True,True)
                get_emulation_logger().log("CONSTELLATION", f"✨ 「若非处幽冥，怎知生可贵！」生效")

class ConstellationEffect_5(ConstellationEffect):
    """「我已有觉察，他名即是…！」"""
    def __init__(self):
        super().__init__('「我已有觉察，他名即是…！」')

    def apply(self, character):
        super().apply(character)
        self.character.Skill.lv = min(15, self.character.Skill.lv + 3)
                                   
class ConstellationEffect_6(ConstellationEffect):
    """「诸君听我颂，共举爱之杯！」"""
    def __init__(self):
        super().__init__('「诸君听我颂，共举爱之杯！」')

    def apply(self, character):
        super().apply(character)

class CenterOfAttentionEffect(Effect,EventHandler):
    def __init__(self, character):
        super().__init__(character, 10*60)
        self.name = '万众瞩目'
        self.last_time = 0
        self.interval = 0.1*60 
        self.count = 0
        self.max_count = 6
        # 元素附着控制参数
        self.attach_sequence = [1, 0, 0]  # 元素附着序列 (每3次攻击附着1次)
        self.sequence_pos = 0  # 当前序列位置
        self.last_attach_time = 0  # 上次元素附着时间(帧数)
        self.msg = f"""
        <p><span style="color: #faf8f0; font-size: 14pt;">{self.character.name} - {self.name}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">芙宁娜的普通攻击、重击与下落攻击将转为无法被附魔覆盖的水元素伤害，
        且造成的伤害提升，提升值相当于芙宁娜生命值上限的18%。</span></p>
        """

    def apply(self):
        super().apply()
        centerOfAttention = next((e for e in self.character.active_effects if isinstance(e, CenterOfAttentionEffect)), None)
        if centerOfAttention:
            centerOfAttention.duration = self.duration
            return
        self.character.add_effect(self)
        EventBus.subscribe(EventType.BEFORE_CALCULATE, self)
        EventBus.subscribe(EventType.BEFORE_FIXED_DAMAGE, self)
        EventBus.subscribe(EventType.AFTER_NORMAL_ATTACK, self)
        EventBus.subscribe(EventType.AFTER_CHARGED_ATTACK, self)
        EventBus.subscribe(EventType.AFTER_PLUNGING_ATTACK, self)

    def remove(self):
        super().remove()
        EventBus.unsubscribe(EventType.BEFORE_CALCULATE, self)
        EventBus.unsubscribe(EventType.BEFORE_FIXED_DAMAGE, self)
        EventBus.unsubscribe(EventType.AFTER_NORMAL_ATTACK, self)
        EventBus.unsubscribe(EventType.AFTER_CHARGED_ATTACK, self)
        EventBus.unsubscribe(EventType.AFTER_PLUNGING_ATTACK, self)

    def update(self, target):
        super().update(target)
        if self.count >= self.max_count:
            self.remove()

    def handle_event(self, event):
        if event.data['character'] != self.character:
            return
        if event.event_type == EventType.BEFORE_CALCULATE:
            if event.data['damage'].damageType in [DamageType.CHARGED, DamageType.PLUNGING]:
                event.data['damage'].element = ('水',1)
                event.data['damage'].setDamageData('不可覆盖', True)
            elif event.data['damage'].damageType == DamageType.NORMAL:
                if event.data['damage'].name not in ['流涌之刃','灵息之刺']:
                    event.data['damage'].element = self.set_element_attach()
                    event.data['damage'].setDamageData('不可覆盖', True)
        elif event.event_type == EventType.BEFORE_FIXED_DAMAGE:
            if event.data['damage'].damageType in [DamageType.NORMAL, DamageType.CHARGED, DamageType.PLUNGING]:
                if event.data['damage'].name not in ['流涌之刃','灵息之刺']:
                    event.data['damage'].panel['固定伤害基础值加成'] += self.character.maxHP * 0.18
                    event.data['damage'].setDamageData('万众瞩目_固定伤害加成', self.character.maxHP * 0.18)
                    if self.character.arkhe == '芒性':
                        event.data['damage'].panel['固定伤害基础值加成'] += self.character.maxHP * 0.25
                        event.data['damage'].setDamageData('万众瞩目_芒性_固定伤害加成', self.character.maxHP * 0.25)
                    self.count += 1
        elif event.event_type in [EventType.AFTER_NORMAL_ATTACK, EventType.AFTER_CHARGED_ATTACK, EventType.AFTER_PLUNGING_ATTACK]:
            if GetCurrentTime() - self.last_time >= self.interval:
                self.last_time = GetCurrentTime()
                if self.character.arkhe == '荒性':
                    CenterOfAttentionHealEffect(self.character).apply()
                elif self.character.arkhe == '芒性':
                    for c in Team.team:
                        EventBus.publish(HurtEvent(self.character, c, 0.01 * c.maxHP, GetCurrentTime()))

    def set_element_attach(self):
        current_time = GetCurrentTime()
        # 重击伤害元素附着判断
        should_attach = False
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

        return ('水', 1 if should_attach else 0)

class CenterOfAttentionHealEffect(Effect):
    def __init__(self, character):
        super().__init__(character, 2.9*60)
        self.name = '万众瞩目_治疗'
        self.last_time = 0
        self.interval = 60
        self.msg = f"""
        <p><span style="color: #faf8f0; font-size: 14pt;">{self.character.name} - {self.name}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">基于芙宁娜生命值上限的4%，为附近的队伍中所有角色恢复生命值，
        持续2.9秒，重复触发将延长持续时间。</span></p>
        """

    def apply(self):
        super().apply()
        heal = next((e for e in self.character.active_effects if isinstance(e, CenterOfAttentionHealEffect)), None)
        if heal:
            heal.duration = self.duration
            return
        self.character.add_effect(self)
        get_emulation_logger().log("CONSTELLATION", f"✨ 「万众瞩目_治疗」生效")

    def remove(self):
        super().remove()
        get_emulation_logger().log("CONSTELLATION", f"✨ 「万众瞩目_治疗」失效")

    def update(self, target):
        super().update(target)
        if GetCurrentTime() - self.last_time >= self.interval:
            self.last_time = GetCurrentTime()
            for c in Team.team:
                heal = Healing(4, HealingType.BURST, self.name)
                EventBus.publish(HealEvent(self.character, c, heal,GetCurrentTime()))

class Furina(Fontaine):
    ID = 75
    def __init__(self, level=1, skill_params=..., constellation=0):
        super().__init__(Furina.ID, level, skill_params, constellation)

    def _init_character(self):
        super()._init_character()
        self.elemental_energy = ElementalEnergy(self,('水',60))
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

Furina_table = {
    'id': Furina.ID,
    'name': '芙宁娜',
    'type': '单手剑',
    'element': '水',
    'rarity': 5,
    'association':'枫丹',
    'normalAttack': {'攻击次数': 4},
    'chargedAttack': {},
    # 'plungingAttack': {'攻击距离':['高空', '低空']},
    'skill': {},
    'burst': {}
}
