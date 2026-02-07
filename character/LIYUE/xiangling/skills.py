from typing import Any
from core.skills.base import SkillBase, EnergySkill
from core.skills.common import NormalAttackSkill
from core.action.damage import Damage, DamageType
from core.event import DamageEvent, EventBus
from core.tool import GetCurrentTime
from character.LIYUE.xiangling.entities import GuobaEntity, PyronadoEntity

class NormalAttack(NormalAttackSkill):
    def __init__(self, lv: int):
        super().__init__(lv=lv)
        self.damage_multiplier = {
            1: [42.05, 45.48, 48.9, 53.79, 57.21, 61.12, 66.5, 71.88, 77.26, 83.13, 89.85, 97.76, 105.67, 113.58, 122.2],
            2: [42.14, 45.57, 49, 53.9, 57.33, 61.25, 66.64, 72.03, 77.42, 83.3, 90.04, 97.96, 105.88, 113.81, 122.45]
        }

    def on_execute_hit(self, target: Any, hit_index: int):
        pass

class ElementalSkill(SkillBase):
    def __init__(self, lv: int):
        super().__init__("锅巴出击", 45, 12 * 60, lv, ('火', 1))
        self.summon_frame = 40

    def on_frame_update(self):
        """
        注意：current_frame 由 ActionManager 每帧注入。
        """
        if self.current_frame == self.summon_frame:
            guoba = GuobaEntity(self.caster, self.lv)
            self.caster.ctx.space.register(guoba)

class ElementalBurst(EnergySkill):
    def __init__(self, lv: int, caster: Any):
        super().__init__("旋火轮", 80, 20 * 60, lv, ('火', 1), caster=caster)
        self.summon_frame = 56

    def on_frame_update(self):
        if self.current_frame == self.summon_frame:
            pyronado = PyronadoEntity(self.caster, self.lv)
            self.caster.ctx.space.register(pyronado)