from typing import Dict, Any, List
from core.registry import register_character
from character.FONTAINE.fontaine import Fontaine
from core.mechanics.energy import ElementalEnergy
from character.FONTAINE.charlotte.skills import NormalAttack, ChargedAttack, ElementalSkill, ElementalBurst
from character.FONTAINE.charlotte.talents import (
    PassiveSkillEffect_1, PassiveSkillEffect_2,
    ConstellationEffect_1, ConstellationEffect_2, ConstellationEffect_3,
    ConstellationEffect_4, ConstellationEffect_5, ConstellationEffect_6
)

@register_character("夏洛蒂")
class CHARLOTTE(Fontaine):
    """
    夏洛蒂 - 核心角色类
    已适配 ASM 与新规目录结构。
    """
    def __init__(self, level: int = 1, skill_params: List[int] = None, constellation: int = 0, base_data: Dict[str, Any] = None):
        super().__init__(id=74, level=level, skill_params=skill_params, constellation=constellation, base_data=base_data)
        self.association = '枫丹'

    def _setup_character_components(self):
        """V2 架构组件初始化"""
        self.arkhe = "芒性"
        self.elemental_energy = ElementalEnergy(self, ('冰', 80))
        
        # 实例化技能并注册到标准字典
        self.skills = {
            "normal_attack": NormalAttack(self.skill_params[0]),
            "charged_attack": ChargedAttack(self.skill_params[0]),
            "elemental_skill": ElementalSkill(self.skill_params[1]),
            "elemental_burst": ElementalBurst(self.skill_params[2])
        }

    def _setup_effects(self):
        """V2 架构效果初始化"""
        self.talents = [
            PassiveSkillEffect_1(),
            PassiveSkillEffect_2()
        ]
        
        self.constellations = [
            ConstellationEffect_1(),
            ConstellationEffect_2(),
            ConstellationEffect_3(),
            ConstellationEffect_4(),
            ConstellationEffect_5(),
            ConstellationEffect_6()
        ]

    def get_action_metadata(self) -> Dict[str, Any]:
        """
        定义夏洛蒂 E 技能的参数 Schema。
        """
        return {
            "elemental_skill": {
                "label": "取景·冰点构图法",
                "params": [
                    {
                        "key": "type", 
                        "label": "施放方式", 
                        "type": "select", 
                        "options": [
                            {"label": "点按", "value": "Press"}, 
                            {"label": "长按", "value": "Hold"}
                        ], 
                        "default": "Press"
                    }
                ]
            }
        }
