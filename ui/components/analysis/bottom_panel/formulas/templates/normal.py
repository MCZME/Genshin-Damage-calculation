"""[V20.0] 常规伤害模板

包含常规伤害路径的公式生成模板：
- CORE: 核心伤害（BASE + MULT 融合）
- BONUS: 增伤乘区
- CRIT: 暴击乘区
- REACT: 反应乘区
- DEF: 防御区
- RES: 抗性区
"""

from ..types import FormulaResult, FormulaPartData, domain_value, text


def build_core(
    bucket_data: dict,
    bucket_key: str,
    bucket_color: str,
) -> FormulaResult:
    """核心伤害模板：属性 × 倍率 的完整展示

    单属性：2000 × 120% = 2400
    多属性：攻击力×120% + 防御力×180%
    """
    from ...utils import format_val

    scaling_info = bucket_data.get("scaling_info", [])
    independent_pct = bucket_data.get("independent_pct", 0.0)
    bonus_pct = bucket_data.get("bonus_pct", 0.0)
    flat_val = bucket_data.get("flat", 0.0)

    parts: list[FormulaPartData] = []

    if not scaling_info:
        # 无 scaling_info，显示简化形式
        total = bucket_data.get("total", 0) * bucket_data.get("multiplier", 1.0)
        parts.append(
            domain_value(
                total,
                "core",
                bucket_key,
                bucket_color,
                False,
                ".0f",
            )
        )
        return FormulaResult(parts, format_val(total))

    # 构建 属性 × 倍率 展示
    if len(scaling_info) == 1:
        # 单属性：简洁显示
        info = scaling_info[0]
        total_val = info.get("total_val", 0.0)
        skill_mult = info.get("skill_mult", 0.0)

        parts.extend(
            [
                text(f"{total_val:.0f}", color="white70"),
                text(" × "),
                domain_value(
                    skill_mult,
                    "skill_mult",
                    bucket_key,
                    bucket_color,
                    False,
                    ".1f",
                ),
                text("%", size=9),
            ]
        )
        core_dmg = total_val * skill_mult / 100
    else:
        # 多属性：显示数值 × 倍率
        for i, info in enumerate(scaling_info):
            if i > 0:
                parts.append(text(" + ", color="white38"))

            attr_name = info.get("attr_name", "")
            total_val = info.get("total_val", 0.0)
            skill_mult = info.get("skill_mult", 0.0)

            parts.extend(
                [
                    text(f"{total_val:.0f}", color="white70"),
                    text("×"),
                    domain_value(
                        skill_mult,
                        f"skill_mult:{attr_name}",
                        bucket_key,
                        bucket_color,
                        False,
                        ".1f",
                    ),
                    text("%", size=9),
                ]
            )

        core_dmg = sum(
            info.get("total_val", 0) * info.get("skill_mult", 0) / 100
            for info in scaling_info
        )

    # 独立乘区
    if independent_pct > 0:
        parts.extend(
            [
                text("×(1+"),
                domain_value(
                    independent_pct,
                    "independent",
                    bucket_key,
                    bucket_color,
                ),
                text(")"),
            ]
        )
        core_dmg *= 1 + independent_pct / 100

    # 倍率加值
    if bonus_pct > 0:
        parts.extend(
            [
                text("+", color="white38"),
                domain_value(
                    bonus_pct,
                    "bonus_pct",
                    bucket_key,
                    bucket_color,
                ),
                text("%"),
            ]
        )
        core_dmg *= 1 + bonus_pct / 100

    # 固定值
    if flat_val > 0:
        parts.extend(
            [
                text("+", color="white38"),
                domain_value(
                    flat_val,
                    "flat",
                    bucket_key,
                    bucket_color,
                    format_spec=".0f",
                ),
            ]
        )
        core_dmg += flat_val

    total_text = format_val(core_dmg)
    return FormulaResult(parts, total_text)


def build_bonus_crit(
    bucket_data: dict,
    bucket_key: str,
    bucket_color: str,
) -> FormulaResult:
    """增伤/暴击模板：1 + XX%

    BONUS: 1 + 增伤%（可点击查看来源）
    CRIT: 1 + 暴伤%（可点击查看来源），暴击时总计带星号并使用金色
    """
    mult_val = bucket_data.get("multiplier", 1.0)
    parts: list[FormulaPartData] = []
    total_color: str | None = None

    if bucket_key == "CRIT":
        # 暴击区：显示暴击率和暴击伤害
        crit_rate = bucket_data.get("crit_rate", 0.0)
        cd_pct = (mult_val - 1) * 100

        if mult_val > 1.0:
            # 暴击：显示 CR: XX% | 1+CD%，添加星号，使用金色
            parts.extend(
                [
                    text("CR:"),
                    domain_value(
                        crit_rate,
                        "crit_rate",
                        bucket_key,
                        bucket_color,
                    ),
                    text("% | 1+"),
                    domain_value(
                        cd_pct,
                        "crit_dmg",
                        bucket_key,
                        bucket_color,
                    ),
                    text("%"),
                ]
            )
            total_text = f"{mult_val:.2f}*"
            total_color = "amber400"  # 暴击时使用金色
        else:
            # 未暴击
            parts.extend(
                [
                    text("CR:"),
                    domain_value(
                        crit_rate,
                        "crit_rate",
                        bucket_key,
                        bucket_color,
                    ),
                    text("% | 1+"),
                    domain_value(
                        0.0,
                        "crit_dmg",
                        bucket_key,
                        bucket_color,
                    ),
                    text("%"),
                ]
            )
            total_text = "1.00"
    else:
        # 增伤区
        bonus_pct = (mult_val - 1) * 100
        parts.extend(
            [
                text("1+"),
                domain_value(
                    bonus_pct,
                    "bonus_pct",
                    bucket_key,
                    bucket_color,
                ),
                text("%"),
            ]
        )
        total_text = f"{mult_val:.2f}" if bonus_pct != 0 else "1.00"

    return FormulaResult(parts, total_text, total_color)


def build_react(
    bucket_data: dict,
    bucket_key: str,
    bucket_color: str,
) -> FormulaResult:
    """反应区模板：反应类型 + 基础倍率 × (1 + 加成%)

    显示反应类型（如蒸发、融化）和基础倍率，精通加成可点击查看来源
    无反应时显示简洁的 1.00
    """
    mult_val = bucket_data.get("multiplier", 1.0)
    reaction_type = bucket_data.get("reaction_type", "")
    reaction_base = bucket_data.get("reaction_base", 1.0)
    em_bonus = bucket_data.get("em_bonus", 0.0)
    other_bonus = bucket_data.get("other_bonus", 0.0)

    parts: list[FormulaPartData] = []

    # 逻辑区分：如果总倍率为 1.0 (包括无反应或仅触发剧变反应的情况)，显示简洁的 1.00
    if mult_val == 1.0:
        return FormulaResult([text("1.00", color="white70")], "1.00")

    # 有反应且有加成（如增幅反应 VAPORIZE/MELT）
    if reaction_type:
        parts.extend(
            [
                text(f"{reaction_type}", size=10, color=bucket_color),
                domain_value(
                    reaction_base,
                    "reaction_base",
                    bucket_key,
                    bucket_color,
                    format_spec=".1f",
                ),
            ]
        )

        # 仅在有加成时显示后缀部分
        bonus = em_bonus + other_bonus
        if bonus > 0:
            parts.append(text("×(1+", size=9))

            # 精通加成
            if em_bonus > 0:
                parts.extend(
                    [
                        domain_value(
                            em_bonus,
                            "em_bonus",
                            bucket_key,
                            bucket_color,
                        ),
                        text("%"),
                    ]
                )

            # 其他加成
            if other_bonus > 0:
                if em_bonus > 0:
                    parts.append(text("+", color="white38"))
                parts.extend(
                    [
                        domain_value(
                            other_bonus,
                            "other_bonus",
                            bucket_key,
                            bucket_color,
                        ),
                        text("%"),
                    ]
                )

            parts.append(text(")"))

        return FormulaResult(parts, f"{mult_val:.2f}")

    return FormulaResult(parts, f"{mult_val:.2f}")


def build_def(
    bucket_data: dict,
    bucket_key: str,
    bucket_color: str,
) -> FormulaResult:
    """防御区模板：计算公式 + 系数

    两行显示：
    - 上：分子 (攻击者等级×5+500)
    - 下：分母 (攻击者等级×5+500+目标防御×(1-减防%))
    - 总计：系数
    """
    mult_val = bucket_data.get("multiplier", 1.0)
    raw_data = bucket_data.get("raw_data", {})

    attacker_level = raw_data.get("attacker_level", 90)
    target_defense = raw_data.get("target_defense", 500)
    def_reduction_pct = raw_data.get("def_reduction_pct", 0.0)

    parts: list[FormulaPartData] = []
    parts_line2: list[FormulaPartData] = []

    if raw_data:
        # 第一行：分子
        K = attacker_level * 5 + 500
        parts.append(text(f"({K})"))

        # 第二行：分母
        parts_line2.extend([
            text(f"({K}+"),
            domain_value(
                target_defense,
                "target_def",
                bucket_key,
                bucket_color,
                format_spec=".0f",
            ),
        ])

        # 有减防时显示减防部分
        if def_reduction_pct > 0:
            parts_line2.extend([
                text("×(1-"),
                domain_value(
                    def_reduction_pct,
                    "def_reduce",
                    bucket_key,
                    bucket_color,
                    format_spec=".0f",
                ),
                text("%)"),
            ])

        parts_line2.append(text(")"))
    else:
        # 无数据时简洁显示系数
        parts.append(
            domain_value(
                mult_val,
                "def_coeff",
                bucket_key,
                bucket_color,
                format_spec=".2f",
            )
        )

    total_text = f"{mult_val:.2f}"
    return FormulaResult(parts, total_text, parts_line2=parts_line2)


def build_res(
    bucket_data: dict,
    bucket_key: str,
    bucket_color: str,
) -> FormulaResult:
    """抗性区模板：计算公式 + 系数

    两行显示：
    - 上：计算公式（如 1 - 10% = 0.90）
    - 下：系数（如 0.90）

    根据抗性区间使用不同公式：
    - R < 0:   系数 = 1 - R/2      （负抗性收益递减）
    - R <= 75: 系数 = 1 - R        （正常区间）
    - R > 75:  系数 = 1 / (1 + 4R) （高抗性惩罚）
    """
    mult_val = bucket_data.get("multiplier", 1.0)
    raw_data = bucket_data.get("raw_data", {})

    final_res = raw_data.get("final_resistance", 0.0)
    R = final_res / 100.0  # 转为小数

    parts: list[FormulaPartData] = []

    # 根据抗性区间构建公式
    if R < 0:
        # 负抗性：1 - R/2
        parts.extend([
            text("1 - ("),
            domain_value(
                final_res,
                "final_res",
                bucket_key,
                bucket_color,
                show_sign=True,
                format_spec=".0f",
            ),
            text("%)/2"),
        ])
    elif R > 0.75:
        # 高抗性：1 / (1 + 4R)
        parts.extend([
            text("1 / (1 + 4×"),
            domain_value(
                final_res,
                "final_res",
                bucket_key,
                bucket_color,
                format_spec=".0f",
            ),
            text("%)"),
        ])
    else:
        # 正常区间：1 - R
        parts.extend([
            text("1 - "),
            domain_value(
                final_res,
                "final_res",
                bucket_key,
                bucket_color,
                format_spec=".0f",
            ),
            text("%"),
        ])

    total_text = f"{mult_val:.2f}"
    return FormulaResult(parts, total_text)


# 常规伤害路径模板映射
NORMAL_TEMPLATE_MAP = {
    "CORE": build_core,
    "BONUS": build_bonus_crit,
    "CRIT": build_bonus_crit,
    "REACT": build_react,
    "DEF": build_def,
    "RES": build_res,
}

# 桶到模板的映射
BUCKET_TO_TEMPLATE = {
    "BASE": "CORE",
    "MULT": "CORE",
    "BONUS": "BONUS",
    "CRIT": "CRIT",
    "REACT": "REACT",
    "DEF": "DEF",
    "RES": "RES",
}
