from typing import Dict, Any, List
from core.registry import register_character
from character.LIYUE.liyue import Liyue
from core.mechanics.energy import ElementalEnergy
from character.LIYUE.xiangling.skills import NormalAttack, ElementalSkill, ElementalBurst
from character.LIYUE.xiangling.talents import Talent_1, Talent_2, C1, C3, C5

@register_character(11)
class XIANG_LING(Liyue):
    """
    香菱 - 标准模块化实现 (V2)
    """
    def __init__(self, level: int = 1, skill_params: List[int] = None, constellation: int = 0, base_data: Dict[str, Any] = None):
        super().__init__(id=11, level=level, skill_params=skill_params, constellation=constellation, base_data=base_data)
        self.association = '璃月'

    def _setup_character_components(self) -> None:
        """组装核心战斗组件"""
        # 1. 能量系统 (火元素, 80能量)
        self.elemental_energy = ElementalEnergy(self, ('火', 80))
        
        # 2. 技能组 (存储在 self.skills 字典)
        self.skills = {
            "normal": NormalAttack(self.skill_params[0]),
            "skill": ElementalSkill(self.skill_params[1]),
            "burst": ElementalBurst(self.skill_params[2], self)
        }

    def _setup_effects(self) -> None:
        """组装天赋与命座效果"""
        # 填充动态天赋列表
        self.talents = [Talent_1(), Talent_2()]
        
        # 填充固定命座槽位
        self.constellations[0] = C1()
        self.constellations[2] = C3()
        self.constellations[4] = C5()
