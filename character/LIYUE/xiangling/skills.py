from typing import Any
from core.skills.base import SkillBase, EnergySkill
from core.skills.common import NormalAttackSkill
from core.action.damage import Damage, DamageType
from core.action.action_data import ActionFrameData, AttackConfig
from core.mechanics.aura import Element
from character.LIYUE.xiangling.entities import GuobaEntity, PyronadoEntity

class NormalAttack(NormalAttackSkill):
    def __init__(self, lv: int):
        super().__init__(lv=lv)
        self.damage_multiplier = {
            1: [42.05, 45.48, 48.9, 53.79, 57.21, 61.12, 66.5, 71.88, 77.26, 83.13, 89.85, 97.76, 105.67, 113.58, 122.2],
            2: [42.14, 45.57, 49, 53.9, 57.33, 61.25, 66.64, 72.03, 77.42, 83.3, 90.04, 97.96, 105.88, 113.81, 122.45],
            3: [26.06*2, 28.18*2, 30.3*2, 33.33*2, 35.45*2, 37.87*2, 41.21*2, 44.54*2, 47.87*2, 51.51*2, 55.68*2, 60.58*2, 65.48*2, 70.37*2, 75.72*2],
            4: [14.1*4, 15.25*4, 16.4*4, 18.04*4, 19.19*4, 20.5*4, 22.3*4, 24.11*4, 25.91*4, 27.88*4, 30.13*4, 32.79*4, 35.44*4, 38.09*4, 40.98*4],
            5: [71.04, 76.82, 82.6, 90.86, 96.64, 103.25, 112.34, 121.42, 130.51, 140.42, 151.78, 165.13, 178.49, 191.85, 206.42]
        }
        self.segment_frames = [12, 16, 26, 39, 52]

    def on_execute_hit(self, target: Any, hit_index: int):
        segment = hit_index + 1
        multiplier = self.damage_multiplier[segment][self.lv - 1]
        # 普攻默认共享 ICD 计数
        config = AttackConfig(icd_tag="NormalAttack", element_u=1.0)
        damage = Damage(
            damage_multiplier=multiplier,
            element=(Element.PHYSICAL, 0),
            damage_type=DamageType.NORMAL,
            name=f"普攻 第{segment}段",
            aoe_shape='CYLINDER',
            radius=0.5,
            config=config
        )
        self.caster.ctx.space.broadcast_damage(self.caster, damage)

class ElementalSkill(SkillBase):
    def __init__(self, lv: int):
        super().__init__("锅巴出击", 45, 12 * 60, lv, (Element.PYRO, 1))
        self.summon_frame = 40

    def to_action_data(self, params: Any = None) -> ActionFrameData:
        data = ActionFrameData(name="E_SUMMON", total_frames=45, hit_frames=[self.summon_frame])
        setattr(data, "runtime_skill_obj", self)
        return data

    def on_frame_update(self):
        if self.current_frame == self.summon_frame:
            guoba = GuobaEntity(self.caster, self.lv)
            self.caster.ctx.space.register(guoba)

class ElementalBurst(EnergySkill):
    def __init__(self, lv: int, caster: Any):
        super().__init__("旋火轮", 80, 20 * 60, lv, (Element.PYRO, 1), caster=caster)
        self.swing_frames = [18, 33, 56]
        self.swing_multipliers = {
            1: [72, 77.4, 82.8, 90, 95.4, 100.8, 108, 115.2, 122.4, 129.6, 136.8, 144, 153, 162, 171],
            2: [88, 94.6, 101.2, 110, 116.6, 123.2, 132, 140.8, 149.6, 158.4, 167.2, 176, 187, 198, 209],
            3: [109.6, 117.82, 126.04, 137, 145.22, 153.44, 164.4, 175.36, 186.32, 197.28, 208.24, 219.2, 232.9, 246.6, 260.3]
        }
        # 大招独立附着规则
        self.burst_config = AttackConfig(icd_tag="Independent", element_u=2.0)

    def to_action_data(self, params: Any = None) -> ActionFrameData:
        data = ActionFrameData(name="Q_CAST", total_frames=80, hit_frames=self.swing_frames)
        # 将配置透传给动作
        data.attack_config = self.burst_config
        setattr(data, "runtime_skill_obj", self)
        return data

    def on_execute_hit(self, target: Any, hit_index: int):
        segment = hit_index + 1
        multiplier = self.swing_multipliers[segment][self.lv - 1]
        damage = Damage(
            damage_multiplier=multiplier,
            element=(Element.PYRO, 2.0),
            damage_type=DamageType.BURST,
            name=f"旋火轮 挥舞第{segment}段",
            aoe_shape='CYLINDER',
            radius=3.0,
            config=self.burst_config
        )
        self.caster.ctx.space.broadcast_damage(self.caster, damage)

    def on_frame_update(self):
        if self.current_frame == 56:
            pyronado = PyronadoEntity(self.caster, self.lv)
            self.caster.ctx.space.register(pyronado)
