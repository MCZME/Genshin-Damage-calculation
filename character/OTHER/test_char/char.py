from typing import List, Dict, Any, Tuple
from character.character import Character
from core.registry import register_character
from core.skills.movement import DashSkill
from core.skills.common import SkipSkill
from character.OTHER.test_char.skills import (
    TestCharNormalAttack,
    TestCharChargedAttack,
    TestCharPlungingAttack,
    TestCharElementalSkill,
    TestCharElementalBurst,
)
from character.OTHER.test_char.data import BASE_STATS, MECHANISM_CONFIG

@register_character("Test")
class TestChar(Character):
    def __init__(
        self,
        id: int = 1,
        level: int = 90,
        skill_params: List[int] = None,
        constellation: int = 0,
        base_data: Dict[str, Any] = None,
        pos: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    ):
        if base_data is None:
            base_data = {
                "name": "测试角色",
                "element": MECHANISM_CONFIG["element"],
                "type": MECHANISM_CONFIG["weapon"],
                "base_hp": BASE_STATS[level]["hp"],
                "base_atk": BASE_STATS[level]["atk"],
                "base_def": BASE_STATS[level]["def"],
            }
        
        super().__init__(
            id=id,
            level=level,
            skill_params=skill_params,
            constellation=constellation,
            base_data=base_data,
            pos=pos,
        )
        self.max_combo = 3

    def _setup_character_components(self) -> None:
        self.skills = {
            "normal_attack": TestCharNormalAttack(self.skill_params[0], self),
            "charged_attack": TestCharChargedAttack(self.skill_params[0], self),
            "plunging_attack": TestCharPlungingAttack(self.skill_params[0], self),
            "elemental_skill": TestCharElementalSkill(self.skill_params[1], self),
            "elemental_burst": TestCharElementalBurst(self.skill_params[2], self),
            "dash": DashSkill(caster=self),
            "skip": SkipSkill(caster=self),
        }

    def _setup_effects(self) -> None:
        self.talents = []
        self.constellations = [None] * 6

    @classmethod
    def get_action_metadata(cls) -> Dict[str, Any]:
        """暴露测试模式给 UI。"""
        return {
            "normal_attack": {
                "label": "普通攻击",
                "params": [
                    {"key": "count", "label": "连招次数", "type": "int", "min": 1, "max": 3, "default": 1}
                ]
            },
            "elemental_skill": {
                "label": "元素战技 (审计验证)",
                "params": [
                    {
                        "key": "test_mode", 
                        "label": "测试模式", 
                        "type": "select", 
                        "options": {
                            "基础计算": "基础计算",
                            "多属性点积": "多属性点积",
                            "攻防倍率测试": "攻防倍率测试",
                            "全乘区Buff": "全乘区Buff",
                            "极致穿透": "极致穿透"
                        },
                        "default": "基础计算"
                    }
                ]
            },
            "elemental_burst": {
                "label": "元素爆发 (路径验证)",
                "params": [
                    {
                        "key": "test_mode", 
                        "label": "公式路径", 
                        "type": "select", 
                        "options": {
                            "基础计算": "常规伤害路径", 
                            "剧变反应测试": "剧变反应路径",
                            "增幅反应测试": "增幅反应路径"
                        },
                        "default": "基础计算"
                    }
                ]
            },
            "skip": {
                "label": "等待",
                "params": [
                    {"key": "frames", "label": "帧数", "type": "int", "min": 1, "max": 3600, "default": 60}
                ]
            }
        }
