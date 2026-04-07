"""[V17.0] 月曜反应模板

包含月曜反应路径的公式生成模板：
- LUNAR_BASE: 基础伤害
- ASCENSION: 擢升区
"""

from ..types import FormulaResult, FormulaPartData, domain_value, text
from .normal import build_bonus_crit, build_res


def build_lunar_base(
    bucket_data: dict,
    bucket_key: str,
    bucket_color: str,
) -> FormulaResult:
    """月曜基础伤害模板

    [V17.0] 新增月曜反应支持
    [V23.0] 修复公式显示，与伤害系统计算顺序一致
    [V24.0] 支持角色伤害路径显示

    公式：
    - 反应伤害路径：等级系数 × 反应倍率 × (1 + 基础伤害提升%) × 反应提升 + 附加伤害
    - 角色伤害路径：属性值 × 技能倍率% × 反应倍率 × (1 + 基础伤害提升%) × 反应提升 + 附加伤害

    反应提升 = 1 + 月曜精通加成% + 月曜反应伤害提升%
    """
    reaction_type = bucket_data.get("reaction_type", "")
    damage_type = bucket_data.get("damage_type", "reaction")  # [V24.0]

    # 角色伤害路径数据
    scaling_stat = bucket_data.get("scaling_stat", "")
    attr_val = bucket_data.get("attr_val", 0.0)
    skill_mult = bucket_data.get("skill_mult", 0.0)

    # 反应伤害路径数据
    level_coeff = bucket_data.get("level_coeff", 0.0)

    # 通用数据
    reaction_mult = bucket_data.get("reaction_mult", 1.0)
    base_bonus = bucket_data.get("base_bonus", 0.0)
    em_bonus_pct = bucket_data.get("em_bonus_pct", 0.0)
    reaction_bonus = bucket_data.get("reaction_bonus", 0.0)
    extra_damage = bucket_data.get("extra_damage", 0.0)
    multiplier = bucket_data.get("multiplier", 1.0)
    contributions = bucket_data.get("contributions", [])

    parts: list[FormulaPartData] = []

    # 显示反应类型标签（如「月绽放」）
    if reaction_type:
        parts.append(text(f"{reaction_type} ", size=10, color=bucket_color))

    # [V24.0] 根据伤害类型显示不同的公式开头
    if damage_type == "character" and attr_val > 0:
        # 角色伤害路径：显示属性值和技能倍率
        if scaling_stat:
            parts.append(text(f"{scaling_stat}", size=9, color="white70"))
            parts.append(text(" ", size=9))
        parts.append(
            domain_value(
                attr_val,
                "attr_val",
                bucket_key,
                bucket_color,
                format_spec=".0f",
            )
        )
        parts.append(text("×", size=9, color="white38"))
        parts.append(
            domain_value(
                skill_mult,
                "skill_mult",
                bucket_key,
                bucket_color,
                format_spec=".1f",
            )
        )
        parts.append(text("%", size=9, color="white70"))
        parts.append(text("×", size=9, color="white38"))
    elif level_coeff > 0:
        # 反应伤害路径：显示等级系数
        parts.append(
            domain_value(
                level_coeff,
                "level_coeff",
                bucket_key,
                bucket_color,
                format_spec=".0f",
            )
        )
        parts.append(text("×", size=9, color="white38"))

    # 反应倍率
    parts.append(
        domain_value(
            reaction_mult,
            "reaction_mult",
            bucket_key,
            bucket_color,
            format_spec=".1f",
        )
    )

    # 第一组加成：基础伤害提升 (影响核心基础伤害)
    if base_bonus > 0:
        parts.append(text("×(1+", size=9))
        parts.extend(
            [
                domain_value(
                    base_bonus,
                    "base_bonus",
                    bucket_key,
                    bucket_color,
                ),
                text("%)"),
            ]
        )

    # 第二组加成：反应提升 (影响最终基础伤害区)
    reaction_boost_total = em_bonus_pct + reaction_bonus
    if reaction_boost_total > 0:
        parts.append(text("×(1+", size=9))

        # 月曜精通加成
        if em_bonus_pct > 0:
            parts.extend(
                [
                    domain_value(
                        em_bonus_pct,
                        "em_bonus",
                        bucket_key,
                        bucket_color,
                    ),
                    text("%"),
                ]
            )

        # 月曜反应伤害提升
        if reaction_bonus > 0:
            if em_bonus_pct > 0:
                parts.append(text("+", color="white38"))
            parts.extend(
                [
                    domain_value(
                        reaction_bonus,
                        "reaction_bonus",
                        bucket_key,
                        bucket_color,
                    ),
                    text("%"),
                ]
            )

        parts.append(text(")"))

    # 附加伤害
    if extra_damage > 0:
        parts.extend(
            [
                text("+", color="white38"),
                domain_value(
                    extra_damage,
                    "extra_damage",
                    bucket_key,
                    bucket_color,
                    format_spec=".0f",
                ),
            ]
        )

    # 角色贡献列表（加权求和展示）
    parts_line2: list[FormulaPartData] = []
    if contributions:
        for contrib in contributions:
            name = contrib.get("character_name", "")
            dmg = contrib.get("damage_component", 0.0)
            pct = contrib.get("weight_percentage", 0.0)

            if name and dmg > 0:
                parts_line2.extend(
                    [
                        text(f"├ {name}: ", size=9, color="white54"),
                        domain_value(
                            dmg,
                            f"contrib:{name}",
                            bucket_key,
                            bucket_color,
                            format_spec=".0f",
                        ),
                        text(f" ({pct:.0f}%)", size=9, color="white38"),
                    ]
                )

    return FormulaResult(parts, f"{multiplier:.2f}", parts_line2=parts_line2)


def build_ascension(
    bucket_data: dict,
    bucket_key: str,
    bucket_color: str,
) -> FormulaResult:
    """擢升区模板：1 + 擢升%

    月曜独立的增伤区，与常规增伤区分离。

    [V17.0] 新增月曜反应支持
    """
    mult_val = bucket_data.get("multiplier", 1.0)
    bonus_pct = bucket_data.get("bonus_pct", 0.0)

    parts: list[FormulaPartData] = []

    if bonus_pct > 0:
        parts.extend(
            [
                text("1+"),
                domain_value(
                    bonus_pct,
                    "ascension_pct",
                    bucket_key,
                    bucket_color,
                ),
                text("%"),
            ]
        )
        total_text = f"{mult_val:.2f}"
    else:
        parts.append(text("1.00", color="white70"))
        total_text = "1.00"

    return FormulaResult(parts, total_text)


# 月曜反应路径模板映射
LUNAR_TEMPLATE_MAP = {
    "LUNAR_BASE": build_lunar_base,
    "CRIT": build_bonus_crit,  # 复用暴击模板
    "RES": build_res,          # 复用抗性模板
    "ASCENSION": build_ascension,
}
