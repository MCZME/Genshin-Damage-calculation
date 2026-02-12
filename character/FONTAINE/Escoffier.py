import random
from character.FONTAINE.fontaine import Fontaine
from core.base_class import (ConstellationEffect, ElementalEnergy, EnergySkill, Infusion, NormalAttackSkill, PlungingAttackSkill, 
                            PolearmChargedAttackSkill, SkillBase, TalentEffect)
from core.BaseObject import ArkheObject, baseObject
from core.event import DamageEvent, EventBus, EventHandler, EventType, HealEvent, ObjectEvent
from core.logger import get_emulation_logger
from core.team import Team
from core.tool import GetCurrentTime, summon_energy
from core.action.damage import Damage, DamageType
from core.action.healing import Healing, HealingType
from core.effect.BaseEffect import Effect, ResistanceDebuffEffect

class NormalAttack(NormalAttackSkill):
    def __init__(self, lv, cd=0):
        super().__init__(lv, cd)
        self.segment_frames = [20, 32, [51, 78]]  # 三段攻击的命中帧
        self.end_action_frame = 14  # 结束动作帧
        self.damageMultipiler = {
            1: [51.55, 55.75, 59.94, 65.94, 70.13, 74.93, 81.52, 88.12, 94.71, 101.9, 109.1, 116.29, 123.48, 130.68, 137.87],  # 一段伤害
            2: [47.59, 51.47, 55.34, 60.88, 64.75, 69.18, 75.26, 81.35, 87.44, 94.08, 100.72, 107.36, 114, 120.64, 127.28],  # 二段伤害
            3: [[33, 35.69, 38.37, 42.21, 44.89, 47.96, 52.19, 56.41, 60.63, 65.23, 69.84, 74.44, 79.05, 83.65, 88.25],  # 三段伤害第一部分
                [40.33, 43.62, 46.9, 51.59, 54.87, 58.62, 63.78, 68.94, 74.1, 79.73, 85.36, 90.98, 96.61, 102.24, 107.87]]  # 三段伤害第二部分
        }

class ChargedAttack(PolearmChargedAttackSkill):
    def __init__(self, lv, cd=0):
        super().__init__(lv, total_frames=99, cd=cd)
        self.normal_hit_frame = 20  # 第一段普通攻击帧（使用普通攻击第一段参数）
        self.charged_hit_frame = 58  # 第二段重击帧
        self.damageMultipiler = [
            [51.55, 55.75, 59.94, 65.94, 70.13, 74.93, 81.52, 88.12, 94.71, 101.9, 109.1, 116.29, 123.48, 130.68, 137.87],  # 第一段普通攻击伤害
            [115.41, 124.81, 134.2, 147.62, 157.01, 167.75, 182.51, 197.27, 212.04, 228.14, 244.24, 260.35, 276.45, 292.56, 308.66]  # 第二段重击伤害
        ]

class PlungingAttack(PlungingAttackSkill):
    ...

class ElementalSkill(SkillBase):
    def __init__(self, lv, cd=15*60):
        super().__init__("低温烹饪", total_frames=52, cd=cd, lv=lv, element=('冰',0))
        self.skill_damage = [50.4, 54.18, 57.96, 63, 66.78, 70.56, 75.6, 80.64, 85.68, 90.72, 95.76, 100.8, 107.1, 113.4, 119.7]
        self.arkhe_damage = [33.6, 36.12, 38.64, 42, 44.52, 47.04, 50.4, 53.76, 57.12, 60.48, 63.84, 67.2, 71.4, 75.6, 79.8]
        self.duration = 20 * 60  # 20秒
        self.arkhe_cooldown = 10 * 60  # 10秒
        self.last_arkhe_time = 0
        self.hit_frame = 30

    def start(self, caster):
        if not super().start(caster):
            return False
        get_emulation_logger().log_skill_use(f"❄️ {caster.name} 启动低温冷藏模式")
        return True

    def on_frame_update(self, target):
        if self.current_frame == self.hit_frame:
            # 初始技能伤害
            damage = Damage(
                self.skill_damage[self.lv-1],
                self.element,
                DamageType.SKILL,
                '低温烹饪'
            )
            EventBus.publish(DamageEvent(self.caster, target, damage, get_current_time()))
            
            # 召唤厨艺机关
            kitchen_appliance = KitchenApplianceObject(
                self.caster, 
                self.lv,
                self.duration
            )
            kitchen_appliance.apply()
            
            summon_energy(4, self.caster, ('冰',2))

            # 始基力：荒性效果
            current_time = get_current_time()
            if current_time - self.last_arkhe_time >= self.arkhe_cooldown:
                arkhe_damage = Damage(
                    self.arkhe_damage[self.lv-1],
                    ('冰', 0),
                    DamageType.SKILL,
                    '流涌之刃'
                )
                arkhe = ArkheObject(
                    "流涌之刃",
                    self.caster,
                    "荒",
                    arkhe_damage,
                    60
                )
                arkhe.apply()
                self.last_arkhe_time = current_time

    def on_finish(self):
        super().on_finish()

class KitchenApplianceObject(baseObject,Infusion,EventHandler):
    def __init__(self, character, lv, duration):
        super().__init__("厨艺机关·低温冷藏", duration)
        Infusion.__init__(self)
        self.character = character
        self.lv = lv
        self.frozen_parfait_damage = [120, 129, 138, 150, 159, 168, 180, 192, 204, 216, 228, 240, 255, 270, 285]
        self.attack_interval = 60  # 1秒攻击间隔
        self.last_attack_time = 0
        self.c6_triggers = 0  # 命座6触发次数
        self.last_c6_time = 0  # 命座6上次触发时间
        
    def apply(self):
        o = next((o for o in Team.active_objects if o.name == self.name), None)
        if o:
            o.current_frame = 0
            o.c6_triggers = 0
            return
        Team.add_object(self)
        self.is_active = True
        EventBus.publish(ObjectEvent(self, get_current_time()))
        EventBus.subscribe(EventType.AFTER_DAMAGE, self)
        
    def on_finish(self, target):
        super().on_finish(target)
        EventBus.unsubscribe(EventType.AFTER_DAMAGE, self)
        
    def handle_event(self, event):
        if (self.character.constellation >= 6 and 
            event.data['character'] == Team.current_character and
            event.data['damage'].damageType in [DamageType.NORMAL, DamageType.CHARGED, DamageType.PLUNGING]):
            
            current_time = get_current_time()
            if (current_time - self.last_c6_time >= 30 and  # 0.5秒冷却
                self.c6_triggers < 6):  # 最多6次
                
                damage = Damage(
                    500,
                    ('冰', 1),
                    DamageType.SKILL,
                    '特级冻霜芭菲'
                )
                EventBus.publish(DamageEvent(self.character, event.data['target'], damage, current_time))
                
                self.c6_triggers += 1
                self.last_c6_time = current_time
                get_emulation_logger().log_effect(f"✨ 命座6触发：特级冻霜芭菲 (第{self.c6_triggers}次)")

    def on_frame_update(self, target):
        current_time = self.current_frame
        if current_time - self.last_attack_time >= self.attack_interval:
            damage = Damage(
                self.frozen_parfait_damage[self.lv-1],
                ('冰',self.apply_infusion()),
                DamageType.SKILL,
                '冻霜芭菲'
            )
            EventBus.publish(DamageEvent(self.character, target, damage, get_current_time()))
            self.last_attack_time = current_time

class ElementalBurst(EnergySkill):
    def __init__(self, lv, cd=15*60):
        super().__init__("花刀技法", total_frames=137, cd=cd, lv=lv, element=('冰',2))
        self.skill_damage = [592.8, 637.26, 681.72, 741, 785.46, 829.92, 889.2, 948.48, 1007.76, 1067.04, 1126.32, 1185.6, 1259.7, 1333.8, 1407.9]
        self.healing_amount = [
            (172.03, 1078.53), (184.93, 1186.39), (197.84, 1303.25), (215.04, 1429.1), 
            (227.94, 1563.93), (240.84, 1707.75), (258.05, 1860.57), (275.25, 2022.37),
            (292.45, 2193.16), (309.66, 2372.94), (326.86, 2561.7), (344.06, 2759.46),
            (365.57, 2966.21), (387.07, 3181.94), (408.58, 3406.67)
        ]
        self.hit_frame = 96

    def start(self, caster):
        if not super().start(caster):
            return False
        get_emulation_logger().log_skill_use(f"❄️✨ {caster.name} 施展花刀技法")
        return True

    def on_frame_update(self, target):
        if self.current_frame == self.hit_frame:
            # 技能伤害
            damage = Damage(
                self.skill_damage[self.lv-1],
                self.element,
                DamageType.BURST,
                '花刀技法'
            )
            EventBus.publish(DamageEvent(self.caster, target, damage, get_current_time()))

            # 全队治疗
            healing = Healing(
                self.healing_amount[self.lv-1],
                HealingType.BURST,
                '花刀技法治疗'
            )
            healing.base_value = '攻击力'
            
            for char in Team.team:
                heal_event = HealEvent(
                    self.caster,
                    char,
                    healing,
                    get_current_time()
                )
                EventBus.publish(heal_event)

    def on_finish(self):
        super().on_finish()
        get_emulation_logger().log_skill_use(f"✨ {self.caster.name} 花刀技法结束")

class RecoveryDietEffect(Effect):
    """康复食疗效果"""
    def __init__(self, character, duration=9*60):
        super().__init__(character, duration + (6*60 if character.constellation >= 4 else 0))
        self.name = "康复食疗"
        self.healing_rate = 138.24
        self.last_heal_time = -60
        self.c4_triggers = 0  # 命座4触发次数
        
    def apply(self):
        super().apply()
        existing = next((e for e in self.character.active_effects if isinstance(e,RecoveryDietEffect)), None)
        if existing:
            existing.duration = self.duration
            existing.c4_triggers = 0
        self.character.add_effect(self)
        get_emulation_logger().log_effect(f"{self.character.name}获得康复食疗效果")

    def remove(self):
        super().remove()
        get_emulation_logger().log_effect(f"{self.character.name}失去康复食疗效果")
        
    def update(self, target):
        current_time = get_current_time()
        if current_time - self.last_heal_time >= 60:  # 每秒治疗一次
            healing = Healing(
                self.healing_rate,
                HealingType.PASSIVE,
                '康复食疗'
            )
            healing.base_value = '攻击力'
            
            # 命座4效果
            if (self.character.constellation >= 4 and 
                self.character.level >= 60 and  # 需要天赋1解锁
                self.c4_triggers < 7):  # 最多7次
                
                crit_rate = self.character.attributePanel['暴击率']
                if random.random() * 100 <= crit_rate:  # 按暴击率判断
                    healing.base_Multipiler *= 2  # 治疗量提升100%
                    summon_energy(1, self.character, ('无',2),True,True,0)
                    self.c4_triggers += 1
                    get_emulation_logger().log_effect(f"✨ 命座4触发：治疗量提升100%，恢复2点能量 (第{self.c4_triggers}次)")
            
            heal_event = HealEvent(
                self.character,
                Team.current_character,
                healing,
                current_time
            )
            EventBus.publish(heal_event)
            self.last_heal_time = current_time
            
        super().update(target)

class PassiveSkillEffect_1(TalentEffect, EventHandler):
    def __init__(self, name="美食胜过良药"):
        super().__init__(name)
        
    def apply(self, character):
        super().apply(character)
        EventBus.subscribe(EventType.AFTER_BURST, self)

    def handle_event(self, event):
        if not event.data['character'] == self.character:
            return
        
        RecoveryDietEffect(self.character).apply()

class PassiveSkillEffect_2(TalentEffect, EventHandler):
    def __init__(self, name="灵感浸入调味"):
        super().__init__(name)
        
    def apply(self, character):
        super().apply(character)
        EventBus.subscribe(EventType.AFTER_DAMAGE, self)

    def handle_event(self, event):
        if not event.data['character'] == self.character:
            return
            
        damage = event.data['damage']
        target = event.data['target']
        
        # 只处理元素战技和元素爆发伤害
        if damage.damageType not in [DamageType.SKILL, DamageType.BURST]:
            return
            
        # 计算队伍中水/冰元素角色数量
        hydro_cryo_count = sum(
            1 for char in Team.team 
            if char.element in ['水', '冰']
        )
        
        # 根据角色数量确定抗性降低幅度
        debuff_rates = {1: 5, 2: 10, 3: 15, 4: 55}
        debuff_rate = debuff_rates.get(hydro_cryo_count, 0)
        
        if debuff_rate > 0:
            # 应用水/冰抗性降低效果
            ResistanceDebuffEffect(
                name=self.name,
                source=self.character,
                target=target,
                elements=['水', '冰'],
                debuff_rate=debuff_rate,
                duration=12*60  # 12秒
            ).apply()

class MealDanceEffect(Effect, EventHandler):
    """味蕾绽放的餐前旋舞效果"""
    def __init__(self, character, duration=15*60):
        super().__init__(character, duration)
        self.name = "味蕾绽放的餐前旋舞"
        self.bonus = 60 
        self.msg = f"""
        <p><span style="color: #faf8f0; font-size: 14pt;">{self.character.name} - {self.name}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">冰元素暴击伤害提升{self.bonus}%</span></p>
        """
        
    def apply(self):
        existing = next((e for e in self.character.active_effects if isinstance(e, MealDanceEffect)), None)
        if existing:
            existing.duration = self.duration
        super().apply()
        self.character.add_effect(self)
        EventBus.subscribe(EventType.BEFORE_CRITICAL_BRACKET, self)
        get_emulation_logger().log_effect(f"{self.character.name}获得{self.name}效果")

    def remove(self):
        EventBus.unsubscribe(EventType.BEFORE_CRITICAL_BRACKET, self)
        super().remove()
        get_emulation_logger().log_effect(f"{self.character.name}失去{self.name}效果")

    def handle_event(self, event):
        if event.data['damage'].element[0] == '冰':
            event.data['damage'].panel['暴击伤害'] += self.bonus
            event.data['damage'].setDamageData('爱可菲_命座_暴击伤害加成', self.bonus)

class ConstellationEffect_1(ConstellationEffect, EventHandler):
    def __init__(self, name="味蕾绽放的餐前旋舞"):
        super().__init__(name)
        
    def apply(self, character):
        super().apply(character)
        # 订阅技能和爆发释放事件
        EventBus.subscribe(EventType.AFTER_SKILL, self)
        EventBus.subscribe(EventType.AFTER_BURST, self)

    def handle_event(self, event):
        if not event.data['character'] == self.character:
            return
            
        # 检查队伍元素类型和天赋解锁状态
        if not self._check_conditions():
            return
            
        MealDanceEffect(self.character).apply()

    def _check_conditions(self):
        """检查触发条件"""
        # 检查天赋2是否解锁
        if self.character.level < 60:
            return False
            
        # 检查队伍中水/冰元素角色数量
        hydro_cryo_count = sum(
            1 for char in Team.team 
            if char.element in ['水', '冰']
        )
        
        return hydro_cryo_count == 4

class FreshDelicacyEffect(Effect, EventHandler):
    """现制名肴效果"""
    def __init__(self, character, duration=15*60):
        super().__init__(character, duration)
        self.name = "现制名肴"
        self.cold_brew_stacks = 5  # 初始5层冷煮
        self.msg = f"""
        <p><span style="color: #faf8f0; font-size: 14pt;">{self.character.name} - {self.name}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">拥有{self.cold_brew_stacks}层冷煮效果</span></p>
        """
        
    def apply(self):
        existing = next((e for e in self.character.active_effects if isinstance(e, FreshDelicacyEffect)), None)
        if existing:
            existing.duration = self.duration
            existing.cold_brew_stacks = 5
        super().apply()
        self.character.add_effect(self)
        EventBus.subscribe(EventType.BEFORE_FIXED_DAMAGE, self)
        get_emulation_logger().log_effect(f"{self.character.name}获得{self.name}效果")

    def remove(self):
        EventBus.unsubscribe(EventType.BEFORE_FIXED_DAMAGE, self)
        super().remove()
        get_emulation_logger().log_effect(f"{self.character.name}失去{self.name}效果")

    def handle_event(self, event):
        # 只处理其他角色的冰元素伤害
        if (event.data['character'] != self.character and 
            event.data['damage'].element[0] == '冰' and
            self.cold_brew_stacks > 0):
            if event.data['damage'].damageType not in [DamageType.SKILL, DamageType.BURST, DamageType.NORMAL,
                                                       DamageType.CHARGED, DamageType.PLUNGING]:
                return
            
            # 计算伤害提升值(爱可菲攻击力的240%)
            attributePanel = self.character.attributePanel
            atk_bonus = attributePanel['攻击力'] * (1 + attributePanel['攻击力%']/100) + attributePanel['固定攻击力']
            event.data['damage'].panel['固定伤害基础值加成'] += atk_bonus * 2.4
            event.data['damage'].setDamageData('冷煮伤害加成', atk_bonus * 2.4)
            
            self.cold_brew_stacks -= 1
            get_emulation_logger().log_effect(f"消耗1层冷煮，提升{atk_bonus:.2f}伤害")

class ConstellationEffect_2(ConstellationEffect, EventHandler):
    def __init__(self, name="鲜香味腴的炖煮艺术"):
        super().__init__(name)
        
    def apply(self, character):
        super().apply(character)
        # 订阅元素战技事件
        EventBus.subscribe(EventType.AFTER_SKILL, self)

    def handle_event(self, event):
        if (event.data['character'] == self.character):
            # 应用现制名肴效果
            FreshDelicacyEffect(self.character).apply()

class ConstellationEffect_3(ConstellationEffect):
    def __init__(self, name="焦糖褐变的烘烤魔法"):
        super().__init__(name)
        
    def apply(self, character):
        super().apply(character)
        # 提升元素战技等级3级，最高不超过15级
        character.Skill.lv = min(15, character.Skill.lv + 3)

class ConstellationEffect_4(ConstellationEffect):
    def __init__(self, name="迷迭生香的配比秘方"):
        super().__init__(name)
        
    def apply(self, character):
        super().apply(character)

class ConstellationEffect_5(ConstellationEffect):
    def __init__(self, name="千种酱汁的风味交响"):
        super().__init__(name)
        
    def apply(self, character):
        super().apply(character)
        character.Burst.lv = min(15, character.Burst.lv + 3)

class ConstellationEffect_6(ConstellationEffect):
    def __init__(self, name="虹彩缤纷的甜点茶话"):
        super().__init__(name)
        
    def apply(self, character):
        super().apply(character)
        get_emulation_logger().log_skill_use(f"✨ 命座6「{self.name}」已激活 - 厨艺机关强化")

class Escoffier(Fontaine):
    ID = 98
    def __init__(self, level=1, skill_params=..., constellation=0):
        super().__init__(Escoffier.ID, level, skill_params, constellation)

    def _init_character(self):
        super()._init_character()
        self.elemental_energy = ElementalEnergy(self,('冰',60))
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

Escoffier_table = {
    'id': Escoffier.ID,
    'name': '爱可菲',
    'type': '长柄武器',
    'element': '冰',
    'rarity': '5',
    'association':'枫丹',
    'normalAttack': {'攻击次数': 3},
    'chargedAttack': {},
    # 'plungingAttack': {'攻击距离':['高空', '低空']},
    'skill': {},
    'burst': {}
}
