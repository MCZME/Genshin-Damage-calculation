from core.context import get_context
from character.LIYUE.liyue import Liyue
from core.base_class import ConstellationEffect, ElementalEnergy, EnergySkill, NormalAttackSkill, SkillBase, TalentEffect
from core.effect.BaseEffect import AttackBoostEffect, Effect, ResistanceDebuffEffect
from core.BaseObject import baseObject
from core.action.damage import Damage, DamageType
from core.event import DamageEvent
from core.tool import GetCurrentTime, summon_energy
from core.team import Team

class GuobaObject(baseObject):
    """锅巴对象"""
    def __init__(self, caster, damage):
        super().__init__(name="锅巴", life_frame=420)  # 存在7秒（420帧）
        self.caster = caster
        self.damage = damage
        self.interval = 96  # 1.6秒攻击间隔（96帧）
        self.last_attack_time = -10  # 第126帧开始第一次攻击
        self.is_acquirable = True  # 辣椒是否可被拾取
        self.constellation = caster.constellation  # 添加命座判断

    def on_frame_update(self, target):
        if self.current_frame - self.last_attack_time >= self.interval:
            self._attack(target)
            self.last_attack_time = self.current_frame

    def _attack(self, target):
        event = DamageEvent(self.caster, target, self.damage, get_current_time())
        get_context().event_engine.publish(event)

        summon_energy(1, self.caster, ('火', 2))

        # 命座1效果：锅巴攻击降低火抗
        if self.constellation >= 1:
            debuff = ResistanceDebuffEffect(
                name="外酥里嫩",
                source=self.caster,
                target=target,
                elements=["火"],
                debuff_rate=15,
                duration=6*60
            )
            debuff.apply()

    def on_finish(self, target):
        if self.caster.level >= 60 and self.is_acquirable:
            # 锅巴消失时触发辣椒效果
            effect = ChiliPepperEffect(self.caster ,Team.current_character)
            effect.apply()
        super().on_finish(target)

class ElementalSkill(SkillBase):
    """元素战技：锅巴出击"""
    def __init__(self, lv):
        super().__init__(
            name="锅巴出击",
            total_frames=45,  # 技能动画帧数
            cd=12 * 60,  # 12秒冷却
            lv=lv,
            element=('火', 1),
            interruptible=False,
        )
        self.damageMultipiler = [
            111.28, 119.63, 127.97, 139.1, 147.45, 155.79, 166.92, 178.05, 189.18, 200.3, 211.43, 222.56, 236.47, 250.38, 264.29
        ]
        self.summon_frame = 40  # 召唤锅巴的帧数（第40帧）

    def on_frame_update(self, target):
        if self.current_frame == self.summon_frame:
            damage = Damage(
                self.damageMultipiler[self.lv-1],
                element=('火', 1),
                damageType=DamageType.SKILL,
                name='锅巴出击'
            )
            guoba = GuobaObject(
                caster=self.caster,
                damage=damage
            )
            guoba.apply()
            print("🌶️ 召唤锅巴！")
        return False

    def on_finish(self):
        super().on_finish()

    def on_interrupt(self):
        return super().on_interrupt()

class PyronadoObject(baseObject):
    """旋火轮"""
    def __init__(self, caster, damage_multiplier, lv):
        base_duration = 600 - 56  # 基础持续时间544帧（9.07秒）
        # 如果命座4激活，增加40%持续时间
        if caster.constellation >= 4:
            base_duration = int(base_duration * 1.4)
            
        super().__init__(name="旋火轮", life_frame=base_duration)
        self.caster = caster
        self.damage_multiplier = damage_multiplier
        self.lv = lv
        self.interval = 72  # 0.6秒攻击间隔（72帧）
        self.last_attack_time = -72  # 第56帧开始第一次攻击

    def on_frame_update(self, target):
        if self.current_frame - self.last_attack_time >= self.interval:
            self._attack(target)
            self.last_attack_time = self.current_frame

    def _attack(self, target):
        damage = Damage(
            self.damage_multiplier[self.lv-1],
            element=('火', 1),
            damageType=DamageType.BURST,
            name='旋火轮 旋转伤害'
        )
        event = DamageEvent(self.caster, target, damage, get_current_time())
        get_context().event_engine.publish(event)

    def on_finish(self, target):
        del self.caster
        return super().on_finish(target)

class ElementalBurst(EnergySkill):
    """元素爆发：旋火轮"""
    def __init__(self, lv, caster):
        super().__init__(
            name="旋火轮",
            total_frames=80,  # 技能动画帧数
            cd=20 * 60,  # 20秒冷却
            lv=lv,
            element=('火', 1),
            interruptible=False,
            caster=caster
        )
        self.cd_frame = 19
        self.damageMultipiler = {
            '一段挥舞': [72, 77.4, 82.8, 90, 95.4, 100.8, 108, 115.2, 122.4, 129.6, 136.8, 144, 153, 162, 171],
            '二段挥舞': [88, 94.6, 101.2, 110, 116.6, 123.2, 132, 140.8, 149.6, 158.4, 167.2, 176, 187, 198, 209],
            '三段挥舞': [109.6, 117.82, 126.04, 137, 145.22, 153.44, 164.4, 175.36, 186.32, 197.28, 208.24, 219.2, 232.9, 246.6, 260.3],
            '旋火轮': [112, 120.4, 128.8, 140, 148.4, 156.8, 168, 179.2, 190.4, 201.6, 212.8, 224, 238, 252, 266]
        }
        self.swing_frames = [18, 33, 56]  # 三段挥舞的命中帧

    def on_frame_update(self, target):
        # 处理挥舞伤害
        if self.current_frame in self.swing_frames:
            swing_index = self.swing_frames.index(self.current_frame)
            damage_type = ['一段挥舞', '二段挥舞', '三段挥舞'][swing_index]
            damage = Damage(
                self.damageMultipiler[damage_type][self.lv-1],
                element=('火', 2),
                damageType=DamageType.BURST,
                name=f'{self.name} {damage_type}'
            )
            event = DamageEvent(self.caster, target, damage, get_current_time())
            get_context().event_engine.publish(event)

        # 在最后一帧召唤旋火轮
        if self.current_frame == 56:
            pyronado = PyronadoObject(
                caster=self.caster,
                damage_multiplier=self.damageMultipiler['旋火轮'],
                lv=self.lv
            )
            pyronado.apply()
            print("🔥 召唤旋火轮！")

        return False

    def on_finish(self):
        super().on_finish()

    def on_interrupt(self):
        return super().on_interrupt()

class ExplosionEffect(Effect):
    """内爆效果"""
    def __init__(self, source, damage):
        super().__init__(source,2*60)
        self.damage = damage
        self.duration = 2 * 60  # 2秒
        self.name = '内爆'
        self.msg = f"""
        <p><span style="color: #faf8f0; font-size: 14pt;">{self.character.name} - {self.name}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">2秒后造成火元素伤害</span></p>
        """

    def apply(self):
        super().apply()
        existing = next((e for e in self.character.active_effects 
                       if isinstance(e, ExplosionEffect) and e.name == self.name), None)
        if existing:
            existing.duration = self.duration
            return
            
        self.character.add_effect(self)

    def update(self, target):
        if self.duration > 0:
            self.duration -= 1
            if self.duration <= 0:
                event = DamageEvent(
                    self.character,
                    target,
                    self.damage,
                    get_current_time()
                )
                get_context().event_engine.publish(event)
                self.remove()
                print("💥 内爆效果触发！")

class PassiveSkillEffect_2(TalentEffect):
    def __init__(self):
        super().__init__('绝云朝天椒')

    def apply(self, character):
        super().apply(character)

class ChiliPepperEffect(AttackBoostEffect):
    """辣椒效果"""
    def __init__(self, character, current_character):
        super().__init__(character, current_character,"绝云朝天椒🌶️",10,10*60)

class ConstellationEffect_1(ConstellationEffect):
    """命座1：外酥里嫩"""
    def __init__(self):
        self.name = "外酥里嫩"
        
    def apply(self, character):
        pass 

class ConstellationEffect_2(ConstellationEffect):
    """命座2：大火宽油"""
    def __init__(self):
        super().__init__('大火宽油')

    def apply(self, character):
        super().apply(character)
        # 修改普通攻击最后一击
        original_on_finish = character.NormalAttack.on_finish
        def new_on_finish():
            original_on_finish()
            if character.constellation >= 2:
                # 创建内爆效果
                damage = Damage(
                    75,
                    element=('火', 1),
                    damageType=DamageType.NORMAL,
                    name='大火宽油 内爆'
                )
                effect = ExplosionEffect(character, damage)
                effect.apply()
        character.NormalAttack.on_finish = new_on_finish

class ConstellationEffect_3(ConstellationEffect):
    """命座3：武火急烹"""
    def __init__(self):
        super().__init__('武火急烹')

    def apply(self, character):
        skill_lv = character.Burst.lv + 3
        if skill_lv > 15:
            skill_lv = 15
        character.Burst = ElementalBurst(skill_lv,character)

class ConstellationEffect_4(ConstellationEffect):
    """命座4：文火慢煨"""
    def __init__(self):
        super().__init__('文火慢煨')

    def apply(self, character):
        pass  # 效果已在PyronadoObject中实现

class ConstellationEffect_5(ConstellationEffect):
    """命座5：锅巴凶猛"""
    def __init__(self):
        super().__init__('锅巴凶猛')

    def apply(self, character):
        skill_lv = character.Skill.lv + 3
        if skill_lv > 15:
            skill_lv = 15
        character.Skill = ElementalSkill(skill_lv)

class PyroDamageBoostEffect(Effect):
    """火元素伤害加成效果"""
    def __init__(self, source):
        super().__init__(source,0)
        self.name = "大龙卷旋火轮"
        self.bonus = 15
        self.duration = 0
        self.msg = f"""
        <p><span style="color: #faf8f0; font-size: 14pt;">{self.character.name} - {self.name}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">火元素伤害提升 {self.bonus:.2f}%</span></p>
        """

    def apply(self):
        super().apply()
        for member in Team.team:
            member.attributePanel['火元素伤害加成'] += self.bonus
            member.add_effect(self)
            print(f"{member.name} 获得 {self.name} 效果，火元素伤害提升 {self.bonus}%")

    def remove(self):
        for member in Team.team:
            member.attributePanel['火元素伤害加成'] -= self.bonus
            existing = next((e for e in member.active_effects 
                       if isinstance(e, PyroDamageBoostEffect) and e.name == self.name), None)
            if existing:
                existing.is_active = False
            print(f"{member.name} 的 {self.name} 效果结束")

    def update(self,target):
        pass

class ConstellationEffect_6(ConstellationEffect):
    """命座6：大龙卷旋火轮"""
    def __init__(self):
        super().__init__('大龙卷旋火轮')

    def apply(self, character):
        # 修改PyronadoObject以添加火伤加成
        original_init = PyronadoObject.__init__
        
        def new_init(self, caster, damage_multiplier, lv):
            original_init(self, caster, damage_multiplier, lv)
            if caster.constellation >= 6:
                self.pyro_boost = PyroDamageBoostEffect(caster)
                self.pyro_boost.apply()
                
        PyronadoObject.__init__ = new_init
        
        # 修改PyronadoObject的on_finish以移除效果
        original_finish = PyronadoObject.on_finish
        
        def new_finish(self, target):
            if hasattr(self, 'pyro_boost'):
                self.pyro_boost.remove()
            original_finish(self, target)
            
        PyronadoObject.on_finish = new_finish

# todo:
# 重击
# 添加一个控制参数，用于控制释放捡起辣椒
class XiangLing(Liyue):
    ID = 11
    def __init__(self,level,skill_params,constellation=0):
        super().__init__(XiangLing.ID,level,skill_params,constellation)
        self.association = "璃月"

    def _init_character(self):
        super()._init_character()
        self.elemental_energy = ElementalEnergy(self,('火',80))
        self.NormalAttack = NormalAttackSkill(self.skill_params[0])
        self.NormalAttack.segment_frames = [12,16,26,39,52]
        self.NormalAttack.damageMultipiler = {
            1:[42.05, 45.48, 48.9, 53.79, 57.21, 61.12, 66.5, 71.88, 77.26, 83.13, 89.85, 97.76, 105.67, 113.58, 122.2, ],
            2:[42.14, 45.57, 49, 53.9, 57.33, 61.25, 66.64, 72.03, 77.42, 83.3, 90.04, 97.96, 105.88, 113.81, 122.45, ],
            3:[26.06 + 26.06, 28.18 + 28.18, 30.3 + 30.3, 33.33 + 33.33, 35.45 + 35.45, 37.87 + 37.87, 41.21 + 41.21, 44.54 + 44.54, 47.87 + 47.87, 51.51 + 51.51, 55.68 + 55.68, 60.58 + 60.58, 65.48 + 65.48, 70.37 + 70.37, 75.72 + 75.72, ],
            4:[14.1*4, 15.25*4, 16.4*4, 18.04*4, 19.19*4, 20.5*4, 22.3*4, 24.11*4, 25.91*4, 27.88*4, 30.13*4, 32.79*4, 35.44*4, 38.09*4, 40.98*4, ],
            5:[71.04, 76.82, 82.6, 90.86, 96.64, 103.25, 112.34, 121.42, 130.51, 140.42, 151.78, 165.13, 178.49, 191.85, 206.42, ],
        }
        self.Skill = ElementalSkill(self.skill_params[1])
        self.Burst = ElementalBurst(self.skill_params[2],self)
        self.talent2 = PassiveSkillEffect_2()
        self.constellation_effects[0] = ConstellationEffect_1()
        self.constellation_effects[1] = ConstellationEffect_2()
        self.constellation_effects[2] = ConstellationEffect_3()
        self.constellation_effects[3] = ConstellationEffect_4()
        self.constellation_effects[4] = ConstellationEffect_5()
        self.constellation_effects[5] = ConstellationEffect_6()

xiangling_table  = {
    'id': XiangLing.ID,
    'name': '香菱',
    'type': '长柄武器',
    'association': '璃月',
    'element': '火',
    'rarity': 5,
    'normalAttack': {'攻击次数': 5},
    # 'chargedAttack': {},
    # 'plungingAttack': {'攻击距离':['高空', '低空']},
    'skill': {},
    'burst': {}
}

