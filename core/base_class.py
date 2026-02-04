# ---------------------------------------------------------
# 兼容性导出 (Backward Compatibility Shim)
# ---------------------------------------------------------
# 该文件用于 re-export 新模块中的类，以保持旧代码的兼容性。
# 请在新代码中直接 import 对应的子模块。

from core.effect.common import TalentEffect, ConstellationEffect
from core.mechanics.energy import ElementalEnergy
from core.mechanics.infusion import Infusion
from core.skills.base import SkillBase, EnergySkill
from core.skills.movement import DashSkill, JumpSkill
from core.skills.common import (
    NormalAttackSkill, 
    ChargedAttackSkill, 
    PolearmChargedAttackSkill, 
    PlungingAttackSkill
)
from core.skills.generic import GenericSkill

__all__ = [
    'TalentEffect', 'ConstellationEffect',
    'ElementalEnergy', 'Infusion',
    'SkillBase', 'EnergySkill',
    'DashSkill', 'JumpSkill',
    'NormalAttackSkill', 'ChargedAttackSkill', 
    'PolearmChargedAttackSkill', 'PlungingAttackSkill',
    'GenericSkill'
]
