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

@register_character(74)
class CHARLOTTE(Fontaine):
    """
    夏洛蒂 - 核心角色类
    已适配 ASM 与新规目录结构。
    """
    def __init__(self, level: int = 1, skill_params: List[int] = None, constellation: int = 0, base_data: Dict[str, Any] = None):
        super().__init__(id=74, level=level, skill_params=skill_params, constellation=constellation, base_data=base_data)
        self.association = '枫丹'

    def _init_character(self):
        # 1. 基础属性与资源
        self.arkhe = "芒性"
        self.elemental_energy = ElementalEnergy(self, ('冰', 80))
        
        # 2. 实例化技能 (适配 ASM)
        self.NormalAttack = NormalAttack(self.skill_params[0])
        self.ChargedAttack = ChargedAttack(self.skill_params[0])
        self.Skill = ElementalSkill(self.skill_params[1])
        self.Burst = ElementalBurst(self.skill_params[2])
        
        # 3. 实例化天赋与命座
        self.talent1 = PassiveSkillEffect_1()
        self.talent2 = PassiveSkillEffect_2()
        
        self.constellation_effects = [
            ConstellationEffect_1(),
            ConstellationEffect_2(),
            ConstellationEffect_3(),
            ConstellationEffect_4(),
            ConstellationEffect_5(),
            ConstellationEffect_6()
        ]

    # 注意：基类中的 normal_attack, elemental_skill 等方法现在会自动调用 
    # self._get_action_data 并通过 ASM 执行，因此子类无需再重写这些方法。
    
    def _get_action_data(self, name: str, params: Any) -> Any:
        """重写动作元数据获取逻辑，支持 Skill 对象的参数化导出"""
        if name == "elemental_skill":
            # 夏洛蒂的 E 技能支持长按/点按参数
            hold = params == "长按" if params else False
            return self.Skill.to_action_data(hold=hold)
        
        # 其他动作使用基类通用逻辑 (自动寻找 self.NormalAttack 等)
        return super()._get_action_data(name, params)
