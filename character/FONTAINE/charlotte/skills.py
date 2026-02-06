from typing import Any
from core.skills.base import SkillBase, EnergySkill
from core.skills.common import NormalAttackSkill, ChargedAttackSkill
from core.action.damage import Damage, DamageType
from core.action.healing import Healing, HealingType
from core.event import DamageEvent, ActionEvent, HealEvent, EventType
from core.tool import GetCurrentTime, summon_energy
from core.mechanics.infusion import Infusion
from core.team import Team
from character.FONTAINE.charlotte.entities import FieldObject, DamageEffect

class NormalAttack(NormalAttackSkill, Infusion):
    def __init__(self, lv: int):
        super().__init__(lv=lv)
        Infusion.__init__(self)
        self.segment_frames = [13, 35, 41]
        self.end_action_frame = 43
        self.damage_multiplier = {
            1: [49.85, 53.58, 57.32, 62.31, 66.05, 69.78, 74.77, 79.75, 84.74, 89.72, 94.71, 99.69, 105.92, 112.15, 118.38],
            2: [43.38, 46.63, 49.88, 54.22, 57.47, 60.73, 65.06, 69.4, 73.74, 78.08, 82.41, 86.75, 92.17, 97.59, 103.02],
            3: [64.6, 69.45, 74.29, 80.75, 85.6, 90.44, 96.9, 103.36, 109.82, 116.28, 122.74, 129.2, 137.28, 145.35, 153.43]
        }

    def on_execute_hit(self, target: Any, hit_index: int):
        segment = hit_index + 1
        multiplier = self.damage_multiplier[segment][self.lv - 1]
        
        self.caster.event_engine.publish(ActionEvent(
            event_type=EventType.BEFORE_NORMAL_ATTACK,
            frame=GetCurrentTime(),
            source=self.caster,
            action_name="normal_attack",
            segment=segment
        ))

        damage = Damage(
            damage_multiplier=multiplier,
            element=('冰', self.apply_infusion()),
            damage_type=DamageType.NORMAL,
            name=f'普通攻击 第{segment}段'
        )
        self.caster.event_engine.publish(DamageEvent(self.caster, target, damage, GetCurrentTime()))

        self.caster.event_engine.publish(ActionEvent(
            event_type=EventType.AFTER_NORMAL_ATTACK,
            frame=GetCurrentTime(),
            source=self.caster,
            action_name="normal_attack",
            segment=segment
        ))

class ChargedAttack(ChargedAttackSkill):
    def __init__(self, lv: int):
        super().__init__(lv=lv, total_frames=79)
        self.hit_frame = 67
        self.damage_multiplier_list = [
            100.51, 108.05, 115.59, 125.64, 133.18, 140.72, 
            150.77, 160.82, 170.87, 180.92, 190.97, 201.02, 
            213.59, 226.15, 238.72
        ]
        self.last_arkhe_time = -360

    def on_execute_hit(self, target: Any, hit_index: int):
        self.caster.event_engine.publish(ActionEvent(
            event_type=EventType.BEFORE_CHARGED_ATTACK,
            frame=GetCurrentTime(),
            source=self.caster,
            action_name="charged_attack"
        ))

        # 基础重击伤害
        multiplier = self.damage_multiplier_list[self.lv - 1]
        damage = Damage(multiplier, ('冰', 1), DamageType.CHARGED, '重击')
        self.caster.event_engine.publish(DamageEvent(self.caster, target, damage, GetCurrentTime()))

        # 灵息之刺 (芒性)
        current_time = GetCurrentTime()
        if current_time - self.last_arkhe_time >= 360:
            self.last_arkhe_time = current_time
            self._trigger_arkhe(target)

        self.caster.event_engine.publish(ActionEvent(
            event_type=EventType.AFTER_CHARGED_ATTACK,
            frame=GetCurrentTime(),
            source=self.caster,
            action_name="charged_attack"
        ))

    def _trigger_arkhe(self, target):
        arkhe_mult = [11.17, 12.01, 12.84, 13.96, 14.8, 15.64, 16.75, 17.87, 18.99, 20.1, 21.22, 22.34, 23.73, 25.13, 26.52][self.lv-1]
        arkhe_dmg = Damage(arkhe_mult, ('冰', 1), DamageType.CHARGED, '灵息之刺')
        from core.entities.arkhe import ArkheObject
        ArkheObject('灵息之刺', self.caster, '芒性', arkhe_dmg, life_frame=1).apply()

class ElementalSkill(SkillBase):
    def __init__(self, lv: int):
        super().__init__("取景·冰点构图法", 42, 12 * 60, lv, ('冰', 1))
        self.hold_mode = False
        self.damage_table = {
            '点按': [67.2, 72.24, 77.28, 84, 89.04, 94.08, 100.8, 107.52, 114.24, 120.96, 127.68, 134.4, 142.8, 151.2, 159.6],
            '长按': [139.2, 149.64, 160.08, 174, 184.44, 194.88, 208.8, 222.72, 236.64, 250.56, 264.48, 278.4, 295.8, 313.2, 330.6],
            '瞬时剪影': [39.2, 42.14, 45.08, 49, 51.94, 54.88, 58.8, 62.72, 66.64, 70.56, 74.48, 78.4, 83.3, 88.2, 93.1],
            '聚焦印象': [40.6, 43.65, 46.69, 50.75, 53.8, 56.84, 60.9, 64.96, 69.02, 73.08, 77.14, 81.2, 86.28, 91.35, 96.43]
        }

    def to_action_data(self, hold=False) -> Any:
        self.hold_mode = hold
        config = {'命中帧': 31, '总帧数': 42} if not hold else {'命中帧': 111, '总帧数': 132}
        self.total_frames = config['总帧数']
        self.cd = 12 * 60 if not hold else 18 * 60
        
        from core.action.action_data import ActionFrameData
        data = ActionFrameData(name="elemental_skill", total_frames=self.total_frames, hit_frames=[config['命中帧']])
        setattr(data, "runtime_skill_obj", self)
        return data

    def on_execute_hit(self, target: Any, hit_index: int):
        self.caster.event_engine.publish(ActionEvent(
            event_type=EventType.BEFORE_SKILL,
            frame=GetCurrentTime(),
            source=self.caster,
            action_name="elemental_skill"
        ))

        key = '长按' if self.hold_mode else '点按'
        multiplier = self.damage_table[key][self.lv-1]
        damage = Damage(multiplier, ('冰', 1), DamageType.SKILL, f"{self.name} {key}")
        self.caster.event_engine.publish(DamageEvent(self.caster, target, damage, GetCurrentTime()))
        
        # 应用印记与产球
        if self.hold_mode:
            DamageEffect('聚焦印象', self.caster, target, self.damage_table['聚焦印象'][self.lv-1], 1.5 * 60, 12 * 60).apply()
            summon_energy(3, self.caster, ('冰', 2))
        else:
            DamageEffect('瞬时剪影', self.caster, target, self.damage_table['瞬时剪影'][self.lv-1], 1.5 * 60, 6 * 60).apply()
            summon_energy(5, self.caster, ('冰', 2))

        self.caster.event_engine.publish(ActionEvent(
            event_type=EventType.AFTER_SKILL,
            frame=GetCurrentTime(),
            source=self.caster,
            action_name="elemental_skill"
        ))

class ElementalBurst(EnergySkill):
    def __init__(self, lv: int):
        super().__init__("定格·全方位确证", 68, 20 * 60, lv, ('冰', 1))
        self.hit_frame = 53
        self.multipliers = {
            'damage': [77.62, 83.44, 89.26, 97.02, 102.84, 108.66, 116.42, 124.19, 131.95, 139.71, 147.47, 155.23, 164.93, 174.64, 184.34],
            'heal_init': [256.57, 275.82, 295.06, 320.72, 339.96, 359.2, 384.86, 410.52, 436.17, 461.83, 487.49, 513.15, 545.22, 577.29, 609.36],
            'field_heal': [9.22, 9.91, 10.6, 11.52, 12.21, 12.9, 13.82, 14.75, 15.67, 16.59, 17.51, 18.43, 19.58, 20.74, 21.89],
            'camera': [6.47, 6.95, 7.44, 8.09, 8.57, 9.06, 9.7, 10.35, 11, 11.64, 12.29, 12.94, 13.74, 14.55, 15.36]
        }

    def to_action_data(self) -> Any:
        from core.action.action_data import ActionFrameData
        data = ActionFrameData(name="elemental_burst", total_frames=self.total_frames, hit_frames=[self.hit_frame])
        setattr(data, "runtime_skill_obj", self)
        return data

    def on_execute_hit(self, target: Any, hit_index: int):
        self.caster.event_engine.publish(ActionEvent(
            event_type=EventType.BEFORE_BURST,
            frame=GetCurrentTime(),
            source=self.caster,
            action_name="elemental_burst"
        ))

        # 初始爆发伤害
        damage = Damage(self.multipliers['damage'][self.lv-1], ('冰', 2), DamageType.BURST, f"{self.name} 初始伤害")
        self.caster.event_engine.publish(DamageEvent(self.caster, target, damage, GetCurrentTime()))
        
        # 初始爆发治疗
        healing = Healing(self.multipliers['heal_init'][self.lv-1], HealingType.BURST, f"{self.name}·施放治疗")
        healing.base_value = '攻击力'
        self.caster.event_engine.publish(HealEvent(self.caster, Team.current_character, healing, GetCurrentTime()))
        
        # 创建临事场域
        FieldObject(self.caster, self.multipliers['camera'][self.lv-1], self.multipliers['field_heal'][self.lv-1]).apply()

        self.caster.event_engine.publish(ActionEvent(
            event_type=EventType.AFTER_BURST,
            frame=GetCurrentTime(),
            source=self.caster,
            action_name="elemental_burst"
        ))