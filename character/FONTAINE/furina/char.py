from typing import Any, Dict, Optional

from character.FONTAINE.fontaine import Fontaine
from core.registry import register_character
from core.skills.movement import DashSkill, JumpSkill
from core.skills.common import SkipSkill
from character.FONTAINE.furina.skills import (
    FurinaNormalAttack, FurinaChargedAttack, FurinaPlungingAttack,
    FurinaElementalSkill, FurinaElementalBurst
)
from character.FONTAINE.furina.talents import EndlessWaltz, UnheardConfession
from character.FONTAINE.furina.constellations import (
    FurinaC1, FurinaC2, FurinaC3, FurinaC4, FurinaC5, FurinaC6
)


@register_character("芙宁娜")
class Furina(Fontaine):
    """
    芙宁娜 (Furina) - 不休独舞。
    """

    def __init__(
        self, 
        id: int = 75, 
        level: int = 90, 
        skill_params: list = None, 
        constellation: int = 0, 
        base_data: dict = None
    ):
        super().__init__(
            id=id, 
            level=level, 
            skill_params=skill_params or [1, 1, 1], 
            constellation=constellation, 
            base_data=base_data
        )
        
        # 初始形态
        self.arkhe_mode = "荒"
        self.arkhe = "荒性"
        
        self.singer_interval_override: Optional[int] = None
        self.max_combo = 4 # 芙宁娜普攻为 4 段

    def _setup_character_components(self) -> None:
        """实例化并配置全量技能组件。"""
        # 1. 核心战斗技能
        self.skills = {
            "normal_attack": FurinaNormalAttack(self.skill_params[0], self),
            "charged_attack": FurinaChargedAttack(self.skill_params[0], self),
            "plunging_attack": FurinaPlungingAttack(self.skill_params[0], self),
            "elemental_skill": FurinaElementalSkill(self.skill_params[1], self),
            "elemental_burst": FurinaElementalBurst(self.skill_params[2], self)
        }
        
        # 2. 通用移动与辅助组件
        self.skills["dash"] = DashSkill(caster=self)
        self.skills["jump"] = JumpSkill(caster=self)
        self.skills["skip"] = SkipSkill(caster=self)

    def _setup_effects(self) -> None:
        """挂载天赋与命座组件。"""
        self.talents = [
            EndlessWaltz(),      
            UnheardConfession()  
        ]
        
        self.constellations = [
            FurinaC1(), FurinaC2(), FurinaC3(),
            FurinaC4(), FurinaC5(), FurinaC6()
        ]

    @classmethod
    def get_action_metadata(cls) -> Dict[str, Any]:
        """UI 元数据。"""
        return {
            "normal_attack": {
                "label": "普通攻击",
                "params": [
                    {"key": "count", "label": "攻击次数", "type": "int", "min": 1, "max": 4, "default": 1}
                ]
            },
            "charged_attack": {
                "label": "重击",
                "params": []
            },
            "plunging_attack": {
                "label": "下落攻击",
                "params": []
            },
            "elemental_skill": {
                "label": "元素战技",
                "params": [] 
            },
            "elemental_burst": {
                "label": "元素爆发",
                "params": []
            },
            "dash": { "label": "冲刺", "params": [] },
            "jump": { "label": "跳跃", "params": [] },
            "skip": { 
                "label": "等待", 
                "params": [
                    {"key": "frames", "label": "帧数", "type": "int", "default": 60}
                ] 
            }
        }
