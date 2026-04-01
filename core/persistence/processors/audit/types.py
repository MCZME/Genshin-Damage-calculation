"""[V11.0] 审计处理数据类型定义

提供审计处理器的数据结构定义。
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


class DamageType(Enum):
    """[V12.0] 伤害类型枚举

    区分常规伤害路径和剧变反应路径：
    - NORMAL: 常规伤害路径，使用 6 乘区模型
    - TRANSFORMATIVE: 剧变反应路径，使用 3 桶模型
    - LUNAR: 月曜反应路径，使用 4 桶模型
    """
    NORMAL = "normal"
    TRANSFORMATIVE = "transformative"
    LUNAR = "lunar"


@dataclass
class ComponentDamageData:
    """[V18.0] 月反应组分伤害数据

    存储每个组分的独立审计数据，用于UI多行展示。

    设计决策：
    - 暴击区：各组分独立判定，独立存储
    - 擢升区：所有组分共享，不在此存储
    - 抗性区：所有组分共享目标抗性

    Attributes:
        character_name: 角色名称
        damage_value: 该组分的最终伤害值
        weight: 权重系数 (1.0, 0.5, 或 1/12)
        base_damage: 基础伤害区（乘区乘法前的值）
        crit_multiplier: 暴击乘数（独立判定）
        resistance_multiplier: 抗性系数（共享）
        audit_steps: 该组分的审计步骤（用于域详情展示）
        is_crit: 是否暴击
        crit_rate: 暴击率
        crit_dmg: 暴击伤害
    """
    character_name: str = ""
    damage_value: float = 0.0
    weight: float = 1.0
    base_damage: float = 0.0
    crit_multiplier: float = 1.0
    resistance_multiplier: float = 1.0
    audit_steps: list[dict] = field(default_factory=list)
    is_crit: bool = False
    crit_rate: float = 0.0
    crit_dmg: float = 0.0


@dataclass
class CharacterContribution:
    """[V17.0] 角色贡献数据

    用于月曜反应加权求和的伤害贡献展示。

    Attributes:
        character_name: 角色名称
        damage_component: 该角色的伤害分量
        weight_percentage: 权重百分比（用于展示）
        component_data: 组分独立乘区数据（V18.0 新增）
    """
    character_name: str = ""
    damage_component: float = 0.0
    weight_percentage: float = 0.0
    component_data: ComponentDamageData | None = None


@dataclass
class DamageTypeContext:
    """[V12.0] 伤害类型上下文

    存储伤害类型及其相关元数据，用于 UI 展示路径选择。

    Attributes:
        damage_type: 伤害类型（常规/剧变/月曜）
        attack_tag: 攻击标签（如 "超载", "感电", "扩散"）
        level_coeff: 等级系数（剧变反应专用）
        reaction_coeff: 反应系数（剧变反应专用，如超载 2.75、超导 0.5）
        elemental_mastery: 元素精通值
        special_bonus: 特殊加成（如魔女套等）
        ascension_bonus: 擢升区加成（月曜专用）
        base_bonus: 基础伤害提升（月曜专用）
        extra_damage: 附加伤害（月曜专用）
        contributing_characters: 角色贡献列表（月曜加权求和专用）
    """
    damage_type: DamageType = DamageType.NORMAL
    attack_tag: str = ""
    level_coeff: float = 0.0
    reaction_coeff: float = 1.0
    elemental_mastery: float = 0.0
    special_bonus: float = 0.0
    # 月曜专用字段
    ascension_bonus: float = 0.0
    base_bonus: float = 0.0
    extra_damage: float = 0.0
    contributing_characters: list[CharacterContribution] = field(default_factory=list)


@dataclass
class ScalingAttributeInfo:
    """[V13.0] 单属性缩放信息

    用于混合倍率技能（如阿贝多 E、诺艾尔 Q）的属性-倍率对应展示。

    Attributes:
        attr_name: 属性名（如 "攻击力", "防御力"）
        base_val: 基础值（角色面板基础属性）
        pct_bonus: 百分比加成总和
        flat_bonus: 固定值加成总和
        total_val: 最终属性值 = base_val * (1 + pct_bonus/100) + flat_bonus
        skill_mult: 技能倍率%（百分比形式，如 120.0 表示 120%）
        contribution: 对核心伤害的贡献值 = total_val * skill_mult / 100
        pct_modifiers: 百分比加成修饰符列表
        flat_modifiers: 固定值加成修饰符列表
    """
    attr_name: str = ""
    base_val: float = 0.0
    pct_bonus: float = 0.0
    flat_bonus: float = 0.0
    total_val: float = 0.0
    skill_mult: float = 0.0
    contribution: float = 0.0
    pct_modifiers: list = field(default_factory=list)
    flat_modifiers: list = field(default_factory=list)


@dataclass
class DomainValues:
    """[V11.0] 域值数据结构

    用于乘区公式中的三个域值展示。

    Attributes:
        domain1: 固定值域（不带 % 的属性修饰符总和）
        domain2: 百分比域（带 % 的属性修饰符总和）
        domain3: 其他域（预留）
        domain1_modifiers: 固定值修饰符列表
        domain2_modifiers: 百分比修饰符列表
    """
    domain1: float = 0.0
    domain2: float = 0.0
    domain3: float = 0.0
    domain1_modifiers: list[dict] | None = None
    domain2_modifiers: list[dict] | None = None

    def __post_init__(self):
        if self.domain1_modifiers is None:
            self.domain1_modifiers = []
        if self.domain2_modifiers is None:
            self.domain2_modifiers = []
