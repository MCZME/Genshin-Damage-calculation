from character.FONTAINE.fontaine import Fontaine
from setup.BaseClass import ChargedAttackSkill, ConstellationEffect, ElementalEnergy, EnergySkill, NormalAttackSkill, SkillBase, TalentEffect
from setup.BaseObject import ArkheObject, baseObject
from setup.DamageCalculation import Damage, DamageType
from setup.Event import DamageEvent, EventBus, NormalAttackEvent
from setup.Team import Team
from setup.Tool import GetCurrentTime, summon_energy
from setup.Logger import get_emulation_logger

class NormalAttack(NormalAttackSkill):
    def __init__(self, lv, cd=0):
        super().__init__(lv, cd)
        self.segment_frames = [19, 26, 46]  # 三段攻击的命中帧
        self.damageMultipiler = {
            1: [54.58, 58.67, 62.76, 68.22, 72.31, 76.41, 81.87, 87.32, 92.78, 98.24, 103.7, 109.15, 115.98, 122.8, 129.62],  # 一段伤害
            2: [46.25, 49.71, 53.18, 57.81, 61.28, 64.74, 69.37, 73.99, 78.62, 83.24, 87.87, 92.49, 98.27, 104.05, 109.83],  # 二段伤害
            3: [72.34, 77.76, 83.19, 90.42, 95.85, 101.27, 108.51, 115.74, 122.97, 130.21, 137.44, 144.68, 153.72, 162.76, 171.8]   # 三段伤害
        }
        self.element = ('水', 1)  # 水元素伤害
        # 元素附着控制参数
        self.attach_sequence = [1, 0, 0]  # 元素附着序列 (每3次攻击附着1次)
        self.sequence_pos = 0  # 当前序列位置
        self.last_attach_time = 0  # 上次元素附着时间(帧数)

    def _apply_segment_effect(self, target):
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
        
        # 创建伤害对象
        element = ('水', 1 if should_attach else 0)
        damage = Damage(
            damageMultipiler=self.damageMultipiler[self.current_segment+1][self.lv-1],
            element=element,
            damageType=DamageType.NORMAL,
            name=f'普通攻击 第{self.current_segment+1}段'
        )
        
        # 发布伤害事件
        damage_event = DamageEvent(self.caster, target, damage, current_time)
        EventBus.publish(damage_event)

        # 发布普通攻击事件
        normal_attack_event = NormalAttackEvent(
            self.caster, 
            frame=current_time, 
            before=False,
            damage=damage,
            segment=self.current_segment+1
        )
        EventBus.publish(normal_attack_event)

class ChargedAttack(ChargedAttackSkill):
    def __init__(self, lv, total_frames=212, cd=0):
        super().__init__(lv, total_frames, cd)
        self.damageMultipiler = {
            '重击伤害': [136.8, 147.06, 157.32, 171.0, 181.26, 191.52, 205.2, 218.88, 232.56, 246.24, 259.92, 273.6, 290.7, 307.8, 324.9],
            '衡平推裁伤害': [7.32, 7.91, 8.51, 9.36, 9.96, 10.64, 11.57, 12.51, 13.45, 14.47, 15.49, 16.51, 17.53, 18.55, 19.57]
        }
        self.interval = [9,31,55,80,105,130,154,173]
        self.hp_cost_interval = [43,73,104,134,165]
        self.hp_cost_per_half_second = 8
        self.heal_per_droplet = 16
        # 元素附着控制参数
        self.attach_sequence = [1, 0, 0]  # 元素附着序列 (每3次攻击附着1次)
        self.sequence_pos = 0  # 当前序列位置
        self.last_attach_time = 0  # 上次元素附着时间(帧数)

    def start(self, caster):
        if not super().start(caster):
            return False
        self.total_frames = 212
        self.source_water_droplet = 0
        for obj in Team.active_objects:
            if isinstance(obj, SourceWaterDroplet):
                obj.on_finish
                self.source_water_droplet += 1
            if self.source_water_droplet >= 3:
                break
        self.hit_frame = [212,155,101,31][self.source_water_droplet]
        self.total_frames = self.hit_frame + 3*60
        get_emulation_logger().log_skill_use(f"开始重击，吸收的源水之滴数量为：{self.source_water_droplet}")
        return True

    def on_frame_update(self, target):
        current_time = GetCurrentTime()
        
        if self.current_frame == self.hit_frame + 11:
            self.caster.heal((self.heal_per_droplet * self.source_water_droplet * self.caster.maxHP/100))
            
        if self.current_frame in [i + self.hit_frame for i in self.interval]:
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
            
            element = ('水', 1 if should_attach else 0)
            damage = Damage(
                damageMultipiler=self.damageMultipiler['衡平推裁伤害'][self.lv-1],
                element=element,
                damageType=DamageType.CHARGED,
                name='衡平推裁'
            )
            damage.setBaseValue('生命值')
            EventBus.publish(DamageEvent(self.caster, target, damage, current_time))
            
        if self.current_frame in [i + self.hit_frame for i in self.hp_cost_interval]:
            self.caster.heal(-(self.hp_cost_per_half_second * self.caster.maxHP)/100)

    def on_finish(self):
        return super().on_finish()
    
    def on_interrupt(self):
        return super().on_interrupt()

class ElementalSkill(SkillBase):
    def __init__(self, lv):
        super().__init__(name="泪水啊，我必偿还", total_frames=30, cd=12*60, lv=lv,
                        element=('水', 1), interruptible=False)
        self.damageMultipiler = {
            '技能伤害':[12.86, 13.83, 14.79, 16.08, 17.04, 18.01, 19.3, 20.58, 
                        21.87, 23.16, 24.44, 25.73, 27.34, 28.94, 30.55],
            '灵息之刺伤害':[20.8, 22.36, 23.92, 26.0, 27.56, 29.12, 31.2, 33.28,
                        35.36, 37.44, 39.52, 41.6, 44.2, 46.8, 49.4]}
        self.arkhe_interval = 10 * 60  # 10秒
        self.last_arkhe_time = -10 * 60

    def start(self, caster):
        if not super().start(caster):
            return False
        return True

    def on_frame_update(self, target):
        current_time = GetCurrentTime()
        logger = get_emulation_logger()
        
        if self.current_frame == 23:
            hp_multiplier = self.damageMultipiler['技能伤害'][self.lv-1]
            damage = Damage(
                hp_multiplier,
                element=('水', 1),
                damageType=DamageType.SKILL,
                name=self.name
            )
            damage.setBaseValue('生命值')
            EventBus.publish(DamageEvent(self.caster, target, damage, current_time))
            
            # 生成3枚源水之滴
            for _ in range(3):
                droplet = SourceWaterDroplet(
                    caster=self.caster,
                )
                droplet.apply()
                logger.log_effect(f"🌊 生成源水之滴")
        
            # 芒性伤害 - 灵息之刺
            if (current_time - self.last_arkhe_time >= self.arkhe_interval):  # 主伤害触发后才开始计时
                self.last_arkhe_time = current_time
                arkhe_damage = Damage(
                    damageMultipiler=self.damageMultipiler['灵息之刺伤害'][self.lv-1],
                    element=('水', 0),
                    damageType=DamageType.SKILL,
                    name='灵息之刺'
                )
                arkhe = ArkheObject('灵息之刺', self.caster, self.caster.arkhe,
                                    arkhe_damage, 19)
                arkhe.apply()
                logger.log_damage(self.caster, target, arkhe_damage)
            
            summon_energy(4, self.caster, ('水',2))

    def on_finish(self):
        return super().on_finish()
    
    def on_interrupt(self):
        return super().on_interrupt()

class SourceWaterDroplet(baseObject):
    """源水之滴对象"""
    def __init__(self, caster):
        super().__init__(name="源水之滴", life_frame=15*60)
        self.caster = caster

    def on_frame_update(self, target):
        pass

class ElementalBurst(EnergySkill):
    def __init__(self, lv):
        super().__init__(name="潮水啊，我已归来", total_frames=155, cd=18*60, lv=lv,
                        element=('水', 1), interruptible=False)
        self.damageMultipiler = {
            '技能伤害': [22.26, 23.93, 25.6, 27.82, 29.49, 31.16, 33.39, 35.61, 
                        37.84, 40.06, 42.29, 44.52, 47.3, 50.08, 52.86],
            '水瀑伤害': [9.11, 9.79, 10.47, 11.38, 12.06, 12.75, 13.66, 14.57,
                        15.48, 16.39, 17.3, 18.21, 19.35, 20.49, 21.63]
        }

    def on_frame_update(self, target):
        current_time = GetCurrentTime()
        logger = get_emulation_logger()
        
        # 初始爆发伤害 (95帧)
        if self.current_frame == 95:
            hp_multiplier = self.damageMultipiler['技能伤害'][self.lv-1]
            damage = Damage(
                hp_multiplier,
                element=('水', 1),
                damageType=DamageType.BURST,
                name=self.name
            )
            damage.setBaseValue('生命值')
            EventBus.publish(DamageEvent(self.caster, target, damage, current_time))
            
        # 第一道水瀑 (135帧)
        elif self.current_frame == 135:
            hp_multiplier = self.damageMultipiler['水瀑伤害'][self.lv-1]
            damage = Damage(
                hp_multiplier,
                element=('水', 1),
                damageType=DamageType.BURST,
                name=f"{self.name}-水瀑"
            )
            damage.setBaseValue('生命值')
            EventBus.publish(DamageEvent(self.caster, target, damage, current_time))
            
        # 第二道水瀑 (154帧)
        elif self.current_frame == 154:
            hp_multiplier = self.damageMultipiler['水瀑伤害'][self.lv-1]
            damage = Damage(
                hp_multiplier,
                element=('水', 1),
                damageType=DamageType.BURST,
                name=f"{self.name}-水瀑"
            )
            damage.setBaseValue('生命值')
            EventBus.publish(DamageEvent(self.caster, target, damage, current_time))
            
        if self.current_frame in [94, 135, 152]:
            for _ in range(2):
                droplet = SourceWaterDroplet(
                    caster=self.caster,
                )
                droplet.apply()
                logger.log_effect(f"🌊 生成源水之滴")

    def on_finish(self):
        return super().on_finish()
    
    def on_interrupt(self):
        return super().on_interrupt()
    
class PassiveSkillEffect_1(TalentEffect):

    def __init__(self, name):
        super().__init__(name)

class PassiveSkillEffect_2(TalentEffect):

    def __init__(self, name):
        super().__init__(name)

class ConstellationEffect_1(ConstellationEffect):

    def __init__(self, name):
        super().__init__(name)

class Neuvillette(Fontaine):
    ID = 73

    def __init__(self, level=1, skill_params=..., constellation=0):
        super().__init__(Neuvillette.ID, level, skill_params, constellation)

    def _init_character(self):
        super()._init_character()
        self.elemental_energy = ElementalEnergy(self,('水',70))
        self.NormalAttack = NormalAttack(self.skill_params[0])
        self.ChargedAttack = ChargedAttack(self.skill_params[0])
        self.Skill = ElementalSkill(self.skill_params[1])
        self.Burst = ElementalBurst(self.skill_params[2])

Neuvillette_table = {
    'id': Neuvillette.ID,
    'name': '那维莱特',
    'type': '法器',
    'element': '水',
    'rarity': 5,
    'association':'枫丹',
    'normalAttack': {'攻击次数': 3},
    'chargedAttack': {},
    # 'plungingAttack': {'攻击距离':['高空', '低空']},
    'skill': {},
    'burst': {}
}
