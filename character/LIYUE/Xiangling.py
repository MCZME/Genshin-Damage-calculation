from character.character import Character
from setup.BaseClass import NormalAttackSkill, SkillBase, SkillSate
from setup.BaseObject import baseObject
from setup.DamageCalculation import Damage, DamageType
from setup.Event import DamageEvent, EventBus
from setup.Tool import GetCurrentTime

class GuobaObject(baseObject):
    """锅巴对象"""
    def __init__(self, caster, damage):
        super().__init__(name="锅巴", life_frame=420)  # 存在7秒（420帧）
        self.caster = caster
        self.damage = damage
        self.interval = 96  # 1.6秒攻击间隔（96帧）
        self.last_attack_time = GetCurrentTime() + 86  # 第126帧（40+86）开始第一次攻击

    def update(self, target):
        super().update(target)
        current_time = GetCurrentTime()
        if current_time - self.last_attack_time >= self.interval:
            self._attack(target)
            self.last_attack_time = current_time

    def _attack(self, target):
        event = DamageEvent(self.caster, target, self.damage, GetCurrentTime())
        EventBus.publish(event)
        print(f"🔥 {self.name}喷火造成{self.damage.damage:.2f}火元素伤害")

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
            state=SkillSate.OffField
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
        super().__init__(name="旋火轮", life_frame=600)  # 存在10秒（600帧）
        character = Character(id=caster.id, level=caster.level, skill_params=caster.skill_params, constellation=caster.constellation)
        character.attributePanel = caster.attributePanel.copy()
        self.caster = character
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
        event = DamageEvent(self.caster, target, damage, GetCurrentTime())
        EventBus.publish(event)

    def on_finish(self, target):
        del self.caster
        return super().on_finish(target)

class ElementalBurst(SkillBase):
    """元素爆发：旋火轮"""
    def __init__(self, lv):
        super().__init__(
            name="旋火轮",
            total_frames=80,  # 技能动画帧数
            cd=20 * 60,  # 20秒冷却
            lv=lv,
            element=('火', 2),
            interruptible=False,
            state=SkillSate.OnField
        )
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
            event = DamageEvent(self.caster, target, damage, GetCurrentTime())
            EventBus.publish(event)

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

class XiangLing(Character):
    ID = 11
    def __init__(self,lv,skill_params,constellation=0):
        super().__init__(XiangLing.ID,lv,skill_params,constellation)
        self.association = "璃月"

    def _init_character(self):
        super()._init_character()
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
        self.Burst = ElementalBurst(self.skill_params[2])
