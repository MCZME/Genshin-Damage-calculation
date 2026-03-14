"""
[V9.7] 审计计算类型定义

提供结构化的审计输出，支持 UI 进行图形化拆解展示。
"""
from dataclasses import dataclass
from typing import Literal
from enum import Enum


class ModifierZone(Enum):
    """修饰符所属乘区"""
    BASE = "base"        # 基础值区
    PERCENT = "percent"  # 百分比加成区 (累乘型专用)
    FLAT = "flat"        # 固定值加成区


@dataclass
class AuditResult:
    """审计计算结果结构化输出

    Attributes:
        paradigm: 计算范式 ("cumulative" 累乘型 / "pct_additive" 百分比累加型 / "additive" 纯累加型)
        base: 基础白值
        pct_sum: 百分比加成总和
        flat_sum: 固定值加成总和
        total: 最终结果
        formula: 公式字符串 (向后兼容)
        is_pct_stat: 是否为百分比属性
    """
    paradigm: Literal["cumulative", "pct_additive", "additive"]
    base: float
    pct_sum: float
    flat_sum: float
    total: float
    formula: str
    is_pct_stat: bool


@dataclass
class ZonedModifier:
    """带乘区标记的修饰符

    Attributes:
        name: 修饰符名称 (来源)
        stat: 修饰的属性名
        value: 修饰值
        op: 操作类型 (add/mul 等)
        zone: 所属乘区
        source_type: 来源类型 (如: Weapon, Artifact, Talent) [V9.9]
    """
    name: str
    stat: str
    value: float
    op: str
    zone: ModifierZone
    source_type: str = "Other"


# 累乘型属性集合 (基础值 × (1 + 百分比%) + 固定值)
CUMULATIVE_STATS: set[str] = {"攻击力", "生命值", "防御力"}

# 百分比累加型属性集合 (基础值 + 百分比%)
PCT_ADDITIVE_STATS: set[str] = {
    "元素充能效率",
    "暴击率", "暴击伤害",
    "治疗加成", "受治疗加成", "护盾强效",
}

# [V9.12] 默认展示属性列表
DEFAULT_STATS: list[str] = [
    "攻击力", "生命值", "防御力", "元素精通",
    "暴击率", "暴击伤害", "元素充能效率", "伤害加成"
]
