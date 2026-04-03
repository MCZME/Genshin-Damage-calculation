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
    """月曜基础伤害模板：等级系数 × 反应倍率 × (1+精通加成%+反应加成%)

    显示格式：月绽放1.0×(1+15%)

    [V17.0] 新增月曜反应支持
    """
    reaction_type = bucket_data.get("reaction_type", "")
    reaction_mult = bucket_data.get("reaction_mult", 1.0)
    base_bonus = bucket_data.get("base_bonus", 0.0)
    em_bonus_pct = bucket_data.get("em_bonus_pct", 0.0)
    reaction_bonus = bucket_data.get("reaction_bonus", 0.0)
    extra_damage = bucket_data.get("extra_damage", 0.0)
    multiplier = bucket_data.get("multiplier", 1.0)
    contributions = bucket_data.get("contributions", [])

    parts: list[FormulaPartData] = []

    # 显示反应类型 + 基础倍率（如「月绽放1.0」）
    if reaction_type:
        parts.append(text(f"{reaction_type}", size=10, color=bucket_color))

    parts.append(
        domain_value(
            reaction_mult,
            "reaction_mult",
            bucket_key,
            bucket_color,
            format_spec=".1f",
        )
    )

    # 仅在有加成时显示括号部分
    total_bonus = base_bonus + em_bonus_pct + reaction_bonus
    if total_bonus > 0:
        parts.append(text("×(1+", size=9))

        # 基础伤害提升
        if base_bonus > 0:
            parts.extend(
                [
                    domain_value(
                        base_bonus,
                        "base_bonus",
                        bucket_key,
                        bucket_color,
                    ),
                    text("%"),
                ]
            )

        # 月曜精通加成
        if em_bonus_pct > 0:
            if base_bonus > 0:
                parts.append(text("+", color="white38"))
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

        # 月曜反应加成
        if reaction_bonus > 0:
            if base_bonus > 0 or em_bonus_pct > 0:
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
