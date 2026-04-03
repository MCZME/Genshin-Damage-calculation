"""[V20.0] 剧变反应模板

包含剧变反应路径的公式生成模板：
- LEVEL: 等级系数
- REACT: 反应乘区
"""

from ..types import FormulaResult, FormulaPartData, domain_value, text


def build_level_react_base(
    bucket_data: dict,
    bucket_key: str,
    bucket_color: str,
) -> FormulaResult:
    """等级系数模板：固定值显示

    LEVEL: 等级系数（如 1446）
    """
    value = bucket_data.get("value", 0.0)

    parts: list[FormulaPartData] = [text(f"{value:.0f}", color="white70")]
    total_text = f"{value:.0f}"

    return FormulaResult(parts, total_text)


def build_transformative_react(
    bucket_data: dict,
    bucket_key: str,
    bucket_color: str,
) -> FormulaResult:
    """剧变反应反应乘区模板：反应类型 + 反应系数×(1+精通加成%)

    显示格式：超载2.75×(1+15%)
    """
    reaction_type = bucket_data.get("reaction_type", "")
    reaction_base = bucket_data.get("reaction_base", 1.0)
    em_bonus_pct = bucket_data.get("em_bonus_pct", 0.0)
    special_bonus = bucket_data.get("special_bonus", 0.0)
    multiplier = bucket_data.get("multiplier", 1.0)

    parts: list[FormulaPartData] = []

    # 显示反应类型 + 基础倍率（如「超载2.75」）
    if reaction_type:
        parts.append(text(f"{reaction_type}", size=10, color=bucket_color))

    parts.append(
        domain_value(
            reaction_base,
            "reaction_base",
            bucket_key,
            bucket_color,
            format_spec=".2f",
        )
    )

    # 仅在有加成时显示括号部分
    bonus = em_bonus_pct + special_bonus
    if bonus > 0:
        parts.append(text("×(1+", size=9))

        # 精通加成（可点击）
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

        # 特殊加成
        if special_bonus > 0:
            if em_bonus_pct > 0:
                parts.append(text("+", color="white38"))
            parts.extend(
                [
                    domain_value(
                        special_bonus,
                        "special",
                        bucket_key,
                        bucket_color,
                    ),
                    text("%"),
                ]
            )

        parts.append(text(")"))

    return FormulaResult(parts, f"{multiplier:.2f}")


# 剧变反应路径模板映射
TRANSFORMATIVE_TEMPLATE_MAP = {
    "LEVEL": build_level_react_base,
    "REACT": build_transformative_react,
}
