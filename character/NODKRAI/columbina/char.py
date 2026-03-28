"""哥伦比娅 - 少女 (Damselette)。"""

from typing import Any

from character.NODKRAI.nodkrai import NodKrai
from core.registry import register_character
from core.skills.movement import DashSkill, JumpSkill
from core.skills.common import SkipSkill
from character.NODKRAI.columbina.skills import (
    ColumbinaNormalAttack,
    ColumbinaChargedAttack,
    ColumbinaPlungingAttack,
    ColumbinaElementalSkill,
    ColumbinaElementalBurst,
)
from character.NODKRAI.columbina.talents import (
    LunarInducement,
    MoonsDomainGrace,
    LunarGuidance,
)
from character.NODKRAI.columbina.constellations import (
    ColumbinaC1,
    ColumbinaC2,
    ColumbinaC3,
    ColumbinaC4,
    ColumbinaC5,
    ColumbinaC6,
)


@register_character("哥伦比娅")
class Columbina(NodKrai):
    """
    哥伦比娅 (Columbina) - 少女。
    愚人众执行官第四席，水元素法器角色。

    核心机制：
    - 月曜反应转化：将感电/绽放/水结晶转为月曜变体
    - 引力值系统：通过月曜反应积攒，触发引力干涉
    - 草露机制：特殊重击消耗草露造成月绽放伤害
    """

    # 月曜反应触发能力由月兆天赋 LunarGuidance 提供
    # lunar_triggers 已移至 MoonsignTalent

    def __init__(
        self,
        id: int = 103,
        level: int = 90,
        skill_params: list[Any] | None = None,
        constellation: int = 0,
        base_data: dict[Any, Any] | None = None,
    ):
        super().__init__(
            id=id,
            level=level,
            skill_params=skill_params or [1, 1, 1],
            constellation=constellation,
            base_data=base_data,
        )

        # 引力值系统
        self.gravity_value: int = 0
        self.gravity_max: int = 60

        # 引力值积攒类型计数
        self.gravity_sources: dict[str, int] = {
            "月感电": 0,
            "月绽放": 0,
            "月结晶": 0,
        }

        # 月之领域状态
        self.lunar_domain_active: bool = False

        # 普攻段数
        self.max_combo = 3

    def _setup_character_components(self) -> None:
        """实例化并配置全量技能组件。"""
        self.skills = {
            "normal_attack": ColumbinaNormalAttack(self.skill_params[0], self),
            "charged_attack": ColumbinaChargedAttack(self.skill_params[0], self),
            "plunging_attack": ColumbinaPlungingAttack(self.skill_params[0], self),
            "elemental_skill": ColumbinaElementalSkill(self.skill_params[1], self),
            "elemental_burst": ColumbinaElementalBurst(self.skill_params[2], self),
        }

        # 通用移动与辅助组件
        self.skills["dash"] = DashSkill(caster=self)
        self.skills["jump"] = JumpSkill(caster=self)
        self.skills["skip"] = SkipSkill(caster=self)

    def _setup_effects(self) -> None:
        """挂载天赋与命座组件。"""
        self.talents = [
            LunarInducement(),     # 固有天赋1：月诱
            MoonsDomainGrace(),    # 固有天赋2：月之眷顾
            LunarGuidance(),       # 固有天赋3：月引（月兆天赋）
        ]

        # 命座
        self.constellations = [
            ColumbinaC1(),
            ColumbinaC2(),
            ColumbinaC3(),
            ColumbinaC4(),
            ColumbinaC5(),
            ColumbinaC6(),
        ]

    @classmethod
    def get_action_metadata(cls) -> dict[str, Any]:
        """UI 元数据。"""
        return {
            "normal_attack": {
                "label": "普通攻击",
                "params": [
                    {
                        "key": "count",
                        "label": "攻击次数",
                        "type": "int",
                        "min": 1,
                        "max": 3,
                        "default": 1,
                    }
                ],
            },
            "charged_attack": {"label": "重击", "params": []},
            "plunging_attack": {"label": "下落攻击", "params": []},
            "elemental_skill": {"label": "元素战技", "params": []},
            "elemental_burst": {"label": "元素爆发", "params": []},
            "dash": {"label": "冲刺", "params": []},
            "jump": {"label": "跳跃", "params": []},
            "skip": {
                "label": "等待",
                "params": [
                    {"key": "frames", "label": "帧数", "type": "int", "default": 60}
                ],
            },
        }

    def add_gravity(self, amount: int, source_type: str) -> None:
        """
        增加引力值。

        Args:
            amount: 增加数量
            source_type: 来源类型 ("月感电"/"月绽放"/"月结晶")
        """
        # 命座2加成：积攒速度提升34%
        if self.constellation_level >= 2:
            amount = int(amount * 1.34)

        self.gravity_value = min(self.gravity_value + amount, self.gravity_max)

        # 记录来源类型
        if source_type in self.gravity_sources:
            self.gravity_sources[source_type] += amount

    def get_dominant_gravity_type(self) -> str:
        """
        获取积攒最多引力值的月曜反应类型。

        Returns:
            最多的类型名称，默认返回 "月绽放"
        """
        max_type = "月绽放"
        max_val = 0
        for src_type, val in self.gravity_sources.items():
            if val > max_val:
                max_val = val
                max_type = src_type
        return max_type

    def reset_gravity(self) -> None:
        """重置引力值系统。"""
        self.gravity_value = 0
        self.gravity_sources = {
            "月感电": 0,
            "月绽放": 0,
            "月结晶": 0,
        }