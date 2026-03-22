"""[V20.0] 乘区公式生成器

按模板分类重构，返回数据结构而非组件。

[V20.0] 数据结构设计：
- FormulaPartData: 公式部分数据（TextPart | DomainValuePart）
- TextPart: 纯文本
- DomainValuePart: 可点击的域值
- FormulaResult: 公式生成结果（数据）

组件创建在渲染层完成，ViewModel 只持有数据。
"""

from dataclasses import dataclass, field
from collections.abc import Callable


# ============================================================
# 数据结构定义
# ============================================================


@dataclass
class TextPart:
    """文本部分数据"""

    content: str
    size: int = 10
    color: str = "white54"  # 默认颜色，组件层转换


@dataclass
class DomainValuePart:
    """域值部分数据（可点击）"""

    value: float
    domain_key: str
    bucket_key: str
    bucket_color: str
    show_sign: bool = False
    format_spec: str = ".1f"


# 公式部分类型
FormulaPartData = TextPart | DomainValuePart


@dataclass
class FormulaResult:
    """公式生成结果（纯数据）"""

    parts: list[FormulaPartData] = field(default_factory=list)
    total_text: str = ""
    total_color: str | None = None  # 总计颜色覆盖


# ============================================================
# 域值数据生成
# ============================================================


def _domain_value(
    value: float,
    domain_key: str,
    bucket_key: str,
    bucket_color: str,
    show_sign: bool = False,
    format_spec: str = ".1f",
) -> DomainValuePart:
    """创建域值数据"""
    return DomainValuePart(
        value=value,
        domain_key=domain_key,
        bucket_key=bucket_key,
        bucket_color=bucket_color,
        show_sign=show_sign,
        format_spec=format_spec,
    )


def _text(content: str, size: int = 10, color: str = "white54") -> TextPart:
    """创建文本数据"""
    return TextPart(content=content, size=size, color=color)


# ============================================================
# 模板 1: CORE - 核心伤害（BASE + MULT 融合）
# ============================================================


def build_core(
    bucket_data: dict,
    bucket_key: str,
    bucket_color: str,
) -> FormulaResult:
    """核心伤害模板：属性 × 倍率 的完整展示

    单属性：2000 × 120% = 2400
    多属性：攻击力×120% + 防御力×180%
    """
    from .utils import format_val

    scaling_info = bucket_data.get("scaling_info", [])
    independent_pct = bucket_data.get("independent_pct", 0.0)
    bonus_pct = bucket_data.get("bonus_pct", 0.0)
    flat_val = bucket_data.get("flat", 0.0)

    parts: list[FormulaPartData] = []

    if not scaling_info:
        # 无 scaling_info，显示简化形式
        total = bucket_data.get("total", 0) * bucket_data.get("multiplier", 1.0)
        parts.append(
            _domain_value(
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
                _text(f"{total_val:.0f}", color="white70"),
                _text(" × "),
                _domain_value(
                    skill_mult,
                    "skill_mult",
                    bucket_key,
                    bucket_color,
                    False,
                    ".1f",
                ),
                _text("%", size=9),
            ]
        )
        core_dmg = total_val * skill_mult / 100
    else:
        # 多属性：显示数值 × 倍率
        for i, info in enumerate(scaling_info):
            if i > 0:
                parts.append(_text(" + ", color="white38"))

            attr_name = info.get("attr_name", "")
            total_val = info.get("total_val", 0.0)
            skill_mult = info.get("skill_mult", 0.0)

            parts.extend(
                [
                    _text(f"{total_val:.0f}", color="white70"),
                    _text("×"),
                    _domain_value(
                        skill_mult,
                        f"skill_mult:{attr_name}",
                        bucket_key,
                        bucket_color,
                        False,
                        ".1f",
                    ),
                    _text("%", size=9),
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
                _text("×(1+"),
                _domain_value(
                    independent_pct,
                    "independent",
                    bucket_key,
                    bucket_color,
                ),
                _text(")"),
            ]
        )
        core_dmg *= 1 + independent_pct / 100

    # 倍率加值
    if bonus_pct > 0:
        parts.extend(
            [
                _text("+", color="white38"),
                _domain_value(
                    bonus_pct,
                    "bonus_pct",
                    bucket_key,
                    bucket_color,
                ),
                _text("%"),
            ]
        )
        core_dmg *= 1 + bonus_pct / 100

    # 固定值
    if flat_val > 0:
        parts.extend(
            [
                _text("+", color="white38"),
                _domain_value(
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


# ============================================================
# 模板 2: BONUS_CRIT - 增伤/暴击区
# ============================================================


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
                    _text("CR:"),
                    _domain_value(
                        crit_rate,
                        "crit_rate",
                        bucket_key,
                        bucket_color,
                    ),
                    _text("% | 1+"),
                    _domain_value(
                        cd_pct,
                        "crit_dmg",
                        bucket_key,
                        bucket_color,
                    ),
                    _text("%"),
                ]
            )
            total_text = f"{mult_val:.2f}*"
            total_color = "amber400"  # 暴击时使用金色
        else:
            # 未暴击
            parts.extend(
                [
                    _text("CR:"),
                    _domain_value(
                        crit_rate,
                        "crit_rate",
                        bucket_key,
                        bucket_color,
                    ),
                    _text("% | 1+"),
                    _domain_value(
                        0.0,
                        "crit_dmg",
                        bucket_key,
                        bucket_color,
                    ),
                    _text("%"),
                ]
            )
            total_text = "1.00"
    else:
        # 增伤区
        bonus_pct = (mult_val - 1) * 100
        parts.extend(
            [
                _text("1+"),
                _domain_value(
                    bonus_pct,
                    "bonus_pct",
                    bucket_key,
                    bucket_color,
                ),
                _text("%"),
            ]
        )
        total_text = f"{mult_val:.2f}" if bonus_pct != 0 else "1.00"

    return FormulaResult(parts, total_text, total_color)


# ============================================================
# 模板 3: REACT - 反应区
# ============================================================


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
        return FormulaResult([_text("1.00", color="white70")], "1.00")

    # 有反应且有加成（如增幅反应 VAPORIZE/MELT）
    if reaction_type:
        parts.extend(
            [
                _text(f"{reaction_type}", size=10, color=bucket_color),
                _domain_value(
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
            parts.append(_text("×(1+", size=9))

            # 精通加成
            if em_bonus > 0:
                parts.extend(
                    [
                        _domain_value(
                            em_bonus,
                            "em_bonus",
                            bucket_key,
                            bucket_color,
                        ),
                        _text("%"),
                    ]
                )

            # 其他加成
            if other_bonus > 0:
                if em_bonus > 0:
                    parts.append(_text("+", color="white38"))
                parts.extend(
                    [
                        _domain_value(
                            other_bonus,
                            "other_bonus",
                            bucket_key,
                            bucket_color,
                        ),
                        _text("%"),
                    ]
                )

            parts.append(_text(")"))

        return FormulaResult(parts, f"{mult_val:.2f}")

    return FormulaResult(parts, f"{mult_val:.2f}")


# ============================================================
# 模板 4: DEF - 防御区
# ============================================================


def build_def(
    bucket_data: dict,
    bucket_key: str,
    bucket_color: str,
) -> FormulaResult:
    """防御区模板：系数

    简洁显示：仅显示防御系数，修饰符详情通过点击查看
    系数计算在处理器层完成，UI 层只负责展示
    """
    mult_val = bucket_data.get("multiplier", 1.0)

    parts: list[FormulaPartData] = [
        _domain_value(
            mult_val,
            "def_coeff",
            bucket_key,
            bucket_color,
            format_spec=".2f",
        ),
    ]

    return FormulaResult(parts, f"{mult_val:.2f}")


# ============================================================
# 模板 5: RES - 抗性区
# ============================================================


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
            _text("1 - ("),
            _domain_value(
                final_res,
                "final_res",
                bucket_key,
                bucket_color,
                show_sign=True,
                format_spec=".0f",
            ),
            _text("%)/2"),
        ])
    elif R > 0.75:
        # 高抗性：1 / (1 + 4R)
        parts.extend([
            _text("1 / (1 + 4×"),
            _domain_value(
                final_res,
                "final_res",
                bucket_key,
                bucket_color,
                format_spec=".0f",
            ),
            _text("%)"),
        ])
    else:
        # 正常区间：1 - R
        parts.extend([
            _text("1 - "),
            _domain_value(
                final_res,
                "final_res",
                bucket_key,
                bucket_color,
                format_spec=".0f",
            ),
            _text("%"),
        ])

    total_text = f"{mult_val:.2f}"
    return FormulaResult(parts, total_text)


# ============================================================
# 模板 6: LEVEL_REACT_BASE - 等级系数/反应系数
# ============================================================


def build_level_react_base(
    bucket_data: dict,
    bucket_key: str,
    bucket_color: str,
) -> FormulaResult:
    """等级系数模板：固定值显示

    LEVEL: 等级系数（如 1446）
    """
    value = bucket_data.get("value", 0.0)

    parts: list[FormulaPartData] = [_text(f"{value:.0f}", color="white70")]
    total_text = f"{value:.0f}"

    return FormulaResult(parts, total_text)


# ============================================================
# 模板 7: TRANSFORMATIVE_REACT - 剧变反应反应乘区
# ============================================================


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
        parts.append(_text(f"{reaction_type}", size=10, color=bucket_color))

    parts.append(
        _domain_value(
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
        parts.append(_text("×(1+", size=9))

        # 精通加成（可点击）
        if em_bonus_pct > 0:
            parts.extend(
                [
                    _domain_value(
                        em_bonus_pct,
                        "em_bonus",
                        bucket_key,
                        bucket_color,
                    ),
                    _text("%"),
                ]
            )

        # 特殊加成
        if special_bonus > 0:
            if em_bonus_pct > 0:
                parts.append(_text("+", color="white38"))
            parts.extend(
                [
                    _domain_value(
                        special_bonus,
                        "special",
                        bucket_key,
                        bucket_color,
                    ),
                    _text("%"),
                ]
            )

        parts.append(_text(")"))

    return FormulaResult(parts, f"{multiplier:.2f}")


# ============================================================
# 模板映射与入口函数
# ============================================================

# 常规伤害路径模板映射
NORMAL_TEMPLATE_MAP: dict[str, Callable] = {
    "CORE": build_core,
    "BONUS": build_bonus_crit,
    "CRIT": build_bonus_crit,
    "REACT": build_react,
    "DEF": build_def,
    "RES": build_res,
}

# 剧变反应路径模板映射
TRANSFORMATIVE_TEMPLATE_MAP: dict[str, Callable] = {
    "LEVEL": build_level_react_base,
    "REACT": build_transformative_react,
    "RES": build_res,
}

# 桶到模板的映射
BUCKET_TO_TEMPLATE: dict[str, str] = {
    "BASE": "CORE",
    "MULT": "CORE",
    "BONUS": "BONUS",
    "CRIT": "CRIT",
    "REACT": "REACT",
    "DEF": "DEF",
    "RES": "RES",
}


def build_formula(
    bucket_key: str,
    bucket_data: dict,
    bucket_color: str,
) -> FormulaResult:
    """构建常规伤害桶公式（返回数据结构）

    Args:
        bucket_key: 乘区键
        bucket_data: 乘区数据
        bucket_color: 乘区颜色
    """
    template_name = BUCKET_TO_TEMPLATE.get(bucket_key, bucket_key)
    builder = NORMAL_TEMPLATE_MAP.get(template_name)

    if not builder:
        mult_val = bucket_data.get("multiplier", 1.0)
        return FormulaResult([_text(f"{mult_val:.2f}", color="white70")], f"{mult_val:.2f}")

    return builder(bucket_data, bucket_key, bucket_color)


def build_transformative_formula(
    bucket_key: str,
    bucket_data: dict,
    bucket_color: str,
) -> FormulaResult:
    """构建剧变反应桶公式（返回数据结构）

    Args:
        bucket_key: 乘区键
        bucket_data: 乘区数据
        bucket_color: 乘区颜色
    """
    builder = TRANSFORMATIVE_TEMPLATE_MAP.get(bucket_key)

    if not builder:
        mult_val = bucket_data.get("multiplier", 1.0)
        return FormulaResult([_text(f"{mult_val:.2f}", color="white70")], f"{mult_val:.2f}")

    return builder(bucket_data, bucket_key, bucket_color)