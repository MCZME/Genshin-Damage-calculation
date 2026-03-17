"""[V10.0] 审计域计算器

负责将步骤按来源分组并计算域值。

[V15.0] 移除对 UI 层类型的依赖，使用本地类型定义
"""

from __future__ import annotations
from dataclasses import dataclass, field

from .constants import SOURCE_TYPE_MAP, SOURCE_ORDER
from .types import DomainValues


# ============================================================
# [V15.0] 本地类型定义（替代 UI 层依赖）
# ============================================================


@dataclass
class MultiplierDomain:
    """乘区域数据

    [V15.0] 从 ui.view_models.analysis.tile_vms.types 移动到处理器层
    """

    name: str  # 域名称
    source_type: str  # 来源类型（Weapon, Artifact, Talent 等）
    steps: list[dict] = field(default_factory=list)  # 步骤列表
    total: float = 0.0  # 域小计


def get_source_type(source: str) -> str:
    """[V10.0] 从来源名称推断来源类型

    Args:
        source: 来源名称

    Returns:
        来源类型（Weapon, Artifact, Talent, Constellation, Resonance, Other）
    """
    for keyword, stype in SOURCE_TYPE_MAP.items():
        if keyword in source:
            return stype
    return "Other"


def group_steps_by_source(steps: list[dict]) -> list[MultiplierDomain]:
    """[V10.0] 将步骤按来源分组为域

    Args:
        steps: 单个乘区的计算步骤列表

    Returns:
        按来源分组的域列表
    """
    if not steps:
        return []

    # 按来源类型分组
    grouped: dict[str, list[dict]] = {}
    for step in steps:
        source = step.get("source", "未知来源")
        stype = get_source_type(source)

        if stype not in grouped:
            grouped[stype] = []
        grouped[stype].append(step)

    # 构建域列表
    domains: list[MultiplierDomain] = []

    for stype in SOURCE_ORDER:
        if stype not in grouped:
            continue

        domain_steps = grouped[stype]
        # 计算域小计
        total = sum(s.get("value", 0) for s in domain_steps)

        # 获取域显示名称
        domain_name = stype
        if domain_steps:
            # 使用第一个步骤的来源名称作为域名称
            first_source = domain_steps[0].get("source", stype)
            if len(first_source) <= 8:
                domain_name = first_source
            else:
                domain_name = f"{first_source[:6]}..."

        domains.append(
            MultiplierDomain(
                name=domain_name, source_type=stype, steps=domain_steps, total=total
            )
        )

    return domains


def calculate_domains(steps: list[dict]) -> DomainValues:
    """[V11.0] 计算域值并分组修饰符

    根据属性名是否包含 % 来区分固定值域和百分比域。

    Args:
        steps: 单个乘区的计算步骤列表

    Returns:
        DomainValues: 包含三个域值和对应修饰符列表
    """
    if not steps:
        return DomainValues()

    flat_modifiers = []
    pct_modifiers = []

    for step in steps:
        stat = step.get("stat", "")

        if "%" in stat:
            pct_modifiers.append(step)
        else:
            flat_modifiers.append(step)

    return DomainValues(
        domain1=sum(s.get("value", 0) for s in flat_modifiers),
        domain2=sum(s.get("value", 0) for s in pct_modifiers),
        domain3=0.0,
        domain1_modifiers=flat_modifiers,
        domain2_modifiers=pct_modifiers,
    )
