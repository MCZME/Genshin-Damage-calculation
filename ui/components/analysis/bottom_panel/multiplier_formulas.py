"""[V13.0] 乘区公式生成器

按模板分类重构，大幅简化代码结构。

模板分类：
- CORE: BASE + MULT 融合（核心伤害，混合倍率）
- BONUS_CRIT: BONUS, CRIT（1 + XX% 简单形式）
- REACT: REACT（反应类型 + 基础×(1+加成)）
- DEF: DEF（系数 + 减防/无视分量）
- RES: RES（系数 + 减抗/穿透分量）
- LEVEL_REACT_BASE: LEVEL, REACT_BASE（固定值显示）
- EM_BONUS: EM_BONUS（精通加成）
"""
import flet as ft
from dataclasses import dataclass
from collections.abc import Callable

from .utils import format_val


# ============================================================
# 类型定义
# ============================================================

@dataclass
class FormulaResult:
    """公式生成结果"""
    formula_parts: list[ft.Control]
    total_text: str
    total_color: str | None = None  # 总计颜色覆盖，None 时使用 bucket_color


# ============================================================
# 基础组件
# ============================================================

def _domain_value(
    value: float,
    domain_key: str,
    bucket_key: str,
    bucket_color: str,
    selected_domain: str | None,
    on_domain_click: Callable[[str, str], None],
    show_sign: bool = False,
    format_spec: str = ".1f",
) -> ft.Control:
    """可点击的域值组件"""
    formatted = f"{value:{format_spec}}"
    text = f"+{formatted}" if show_sign and value >= 0 else formatted
    is_selected = selected_domain == domain_key

    return ft.GestureDetector(
        content=ft.Container(
            content=ft.Text(
                text,
                size=11,
                color=bucket_color if is_selected else ft.Colors.WHITE_70,
                weight=ft.FontWeight.BOLD if is_selected else ft.FontWeight.NORMAL,
            ),
            bgcolor=ft.Colors.with_opacity(0.2, bucket_color) if is_selected else ft.Colors.with_opacity(0.05, bucket_color),
            border_radius=4,
            padding=ft.Padding(left=4, right=4, top=2, bottom=2),
        ),
        on_tap=lambda _: on_domain_click(bucket_key, domain_key)
    )


def _text(content: str, size: int = 10, color: str = ft.Colors.WHITE_54) -> ft.Text:
    """快捷创建文本组件"""
    return ft.Text(content, size=size, color=color)


# ============================================================
# 模板 1: CORE - 核心伤害（BASE + MULT 融合）
# ============================================================

def build_core(
    bucket_data: dict,
    bucket_key: str,
    bucket_color: str,
    selected_domain: str | None,
    on_domain_click: Callable[[str, str], None]
) -> FormulaResult:
    """核心伤害模板：属性 × 倍率 的完整展示

    单属性：2000 × 120% = 2400
    多属性：攻击力×120% + 防御力×180%
    """
    scaling_info = bucket_data.get('scaling_info', [])
    independent_pct = bucket_data.get('independent_pct', 0.0)
    bonus_pct = bucket_data.get('bonus_pct', 0.0)
    flat_val = bucket_data.get('flat', 0.0)

    formula_parts: list[ft.Control] = []

    if not scaling_info:
        # 无 scaling_info，显示简化形式
        total = bucket_data.get('total', 0) * bucket_data.get('multiplier', 1.0)
        formula_parts.append(_domain_value(total, "core", bucket_key, bucket_color, selected_domain, on_domain_click, False, ".0f"))
        return FormulaResult(formula_parts, format_val(total))

    # 构建 属性 × 倍率 展示
    if len(scaling_info) == 1:
        # 单属性：简洁显示
        info = scaling_info[0]
        total_val = info.get('total_val', 0.0)
        skill_mult = info.get('skill_mult', 0.0)

        formula_parts.extend([
            _text(f"{total_val:.0f}", color=ft.Colors.WHITE_70),
            _text(" × "),
            _domain_value(skill_mult, "skill_mult", bucket_key, bucket_color, selected_domain, on_domain_click, False, ".1f"),
            _text("%", size=9),
        ])
        core_dmg = total_val * skill_mult / 100
    else:
        # 多属性：显示数值 × 倍率
        for i, info in enumerate(scaling_info):
            if i > 0:
                formula_parts.append(_text(" + ", color=ft.Colors.WHITE_38))

            attr_name = info.get('attr_name', '')
            total_val = info.get('total_val', 0.0)
            skill_mult = info.get('skill_mult', 0.0)

            formula_parts.extend([
                _text(f"{total_val:.0f}", color=ft.Colors.WHITE_70),
                _text("×"),
                _domain_value(skill_mult, f"skill_mult:{attr_name}", bucket_key, bucket_color, selected_domain, on_domain_click, False, ".1f"),
                _text("%", size=9),
            ])

        core_dmg = sum(info.get('total_val', 0) * info.get('skill_mult', 0) / 100 for info in scaling_info)

    # 独立乘区
    if independent_pct > 0:
        formula_parts.extend([
            _text("×(1+"),
            _domain_value(independent_pct, "independent", bucket_key, bucket_color, selected_domain, on_domain_click),
            _text(")"),
        ])
        core_dmg *= (1 + independent_pct / 100)

    # 倍率加值
    if bonus_pct > 0:
        formula_parts.extend([
            _text("+", color=ft.Colors.WHITE_38),
            _domain_value(bonus_pct, "bonus_pct", bucket_key, bucket_color, selected_domain, on_domain_click),
            _text("%"),
        ])
        core_dmg *= (1 + bonus_pct / 100)

    # 固定值
    if flat_val > 0:
        formula_parts.extend([
            _text("+", color=ft.Colors.WHITE_38),
            _domain_value(flat_val, "flat", bucket_key, bucket_color, selected_domain, on_domain_click, format_spec=".0f"),
        ])
        core_dmg += flat_val

    total_text = format_val(core_dmg)
    return FormulaResult(formula_parts, total_text)


# ============================================================
# 模板 2: BONUS_CRIT - 增伤/暴击区
# ============================================================

def build_bonus_crit(
    bucket_data: dict,
    bucket_key: str,
    bucket_color: str,
    selected_domain: str | None,
    on_domain_click: Callable[[str, str], None]
) -> FormulaResult:
    """增伤/暴击模板：1 + XX%

    BONUS: 1 + 增伤%（可点击查看来源）
    CRIT: 1 + 暴伤%（可点击查看来源），暴击时总计带星号并使用金色
    """
    mult_val = bucket_data.get('multiplier', 1.0)
    formula_parts: list[ft.Control] = []
    total_color: str | None = None

    if bucket_key == "CRIT":
        # [V4.2] 暴击区：显示暴击率和暴击伤害
        crit_rate = bucket_data.get('crit_rate', 0.0)
        cd_pct = (mult_val - 1) * 100

        if mult_val > 1.0:
            # 暴击：显示 CR: XX% | 1+CD%，添加星号，使用金色
            formula_parts.extend([
                _text("CR:"),
                _domain_value(crit_rate, "crit_rate", bucket_key, bucket_color, selected_domain, on_domain_click),
                _text("% | 1+"),
                _domain_value(cd_pct, "crit_dmg", bucket_key, bucket_color, selected_domain, on_domain_click),
                _text("%"),
            ])
            total_text = f"{mult_val:.2f}*"
            total_color = ft.Colors.AMBER_400  # 暴击时使用金色
        else:
            # 未暴击：仍显示可点击的域值（0%），允许查看暴击修饰符来源
            formula_parts.extend([
                _text("CR:"),
                _domain_value(crit_rate, "crit_rate", bucket_key, bucket_color, selected_domain, on_domain_click),
                _text("% | 1+"),
                _domain_value(0.0, "crit_dmg", bucket_key, bucket_color, selected_domain, on_domain_click),
                _text("%"),
            ])
            total_text = "1.00"
    else:
        # 增伤区
        bonus_pct = (mult_val - 1) * 100
        # 始终显示可点击的域值，允许查看增伤修饰符来源
        formula_parts.extend([
            _text("1+"),
            _domain_value(bonus_pct, "bonus_pct", bucket_key, bucket_color, selected_domain, on_domain_click),
            _text("%"),
        ])
        total_text = f"{mult_val:.2f}" if bonus_pct != 0 else "1.00"

    return FormulaResult(formula_parts, total_text, total_color)


# ============================================================
# 模板 3: REACT - 反应区
# ============================================================

def build_react(
    bucket_data: dict,
    bucket_key: str,
    bucket_color: str,
    selected_domain: str | None,
    on_domain_click: Callable[[str, str], None]
) -> FormulaResult:
    """反应区模板：基础 × (1 + 加成%)

    显示反应类型（如蒸发、融化）和加成系数
    """
    mult_val = bucket_data.get('multiplier', 1.0)
    em_bonus = bucket_data.get('em_bonus', 0.0)
    other_bonus = bucket_data.get('other_bonus', 0.0)
    reaction_type = bucket_data.get('reaction_type', '')

    formula_parts: list[ft.Control] = []

    # 反应类型标签
    if reaction_type:
        formula_parts.append(_text(f"{reaction_type} ", size=9))

    formula_parts.append(_text("基础×(1+"))

    # 精通加成
    if em_bonus > 0:
        formula_parts.extend([
            _domain_value(em_bonus, "em_bonus", bucket_key, bucket_color, selected_domain, on_domain_click),
            _text("%"),
        ])

    # 其他加成
    if other_bonus > 0:
        if em_bonus > 0:
            formula_parts.append(_text("+", color=ft.Colors.WHITE_38))
        formula_parts.extend([
            _domain_value(other_bonus, "other_bonus", bucket_key, bucket_color, selected_domain, on_domain_click),
            _text("%"),
        ])

    formula_parts.append(_text(")"))

    return FormulaResult(formula_parts, f"{mult_val:.2f}")


# ============================================================
# 模板 4: DEF - 防御区
# ============================================================

def build_def(
    bucket_data: dict,
    bucket_key: str,
    bucket_color: str,
    selected_domain: str | None,
    on_domain_click: Callable[[str, str], None]
) -> FormulaResult:
    """防御区模板：系数 + (减防% + 无视%)

    显示防御系数及修正来源
    """
    mult_val = bucket_data.get('multiplier', 1.0)
    def_reduction = bucket_data.get('def_reduction_pct', 0.0)
    def_ignore = bucket_data.get('def_ignore_pct', 0.0)

    formula_parts: list[ft.Control] = [
        _text(f"{mult_val:.2f}", color=ft.Colors.WHITE_70),
    ]

    if def_reduction > 0 or def_ignore > 0:
        formula_parts.append(_text(" ("))

        if def_reduction > 0:
            formula_parts.extend([
                _domain_value(def_reduction, "def_reduction", bucket_key, bucket_color, selected_domain, on_domain_click),
                _text("%减防", size=8, color=ft.Colors.WHITE_38),
            ])

        if def_ignore > 0:
            if def_reduction > 0:
                formula_parts.append(_text("+", color=ft.Colors.WHITE_38))
            formula_parts.extend([
                _domain_value(def_ignore, "def_ignore", bucket_key, bucket_color, selected_domain, on_domain_click),
                _text("%无视", size=8, color=ft.Colors.WHITE_38),
            ])

        formula_parts.append(_text(")"))

    return FormulaResult(formula_parts, f"{mult_val:.2f}")


# ============================================================
# 模板 5: RES - 抗性区
# ============================================================

def build_res(
    bucket_data: dict,
    bucket_key: str,
    bucket_color: str,
    selected_domain: str | None,
    on_domain_click: Callable[[str, str], None]
) -> FormulaResult:
    """抗性区模板：系数 + (减抗% + 穿透%)

    显示抗性系数及修正来源
    """
    mult_val = bucket_data.get('multiplier', 1.0)
    res_reduction = bucket_data.get('res_reduction_pct', 0.0)
    res_penetration = bucket_data.get('res_penetration_pct', 0.0)

    formula_parts: list[ft.Control] = [
        _text(f"{mult_val:.2f}", color=ft.Colors.WHITE_70),
    ]

    if res_reduction > 0 or res_penetration > 0:
        formula_parts.append(_text(" ("))

        if res_reduction > 0:
            formula_parts.extend([
                _domain_value(res_reduction, "res_reduction", bucket_key, bucket_color, selected_domain, on_domain_click),
                _text("%减抗", size=8, color=ft.Colors.WHITE_38),
            ])

        if res_penetration > 0:
            if res_reduction > 0:
                formula_parts.append(_text("+", color=ft.Colors.WHITE_38))
            formula_parts.extend([
                _domain_value(res_penetration, "res_penetration", bucket_key, bucket_color, selected_domain, on_domain_click),
                _text("%穿透", size=8, color=ft.Colors.WHITE_38),
            ])

        formula_parts.append(_text(")"))

    return FormulaResult(formula_parts, f"{mult_val:.2f}")


# ============================================================
# 模板 6: LEVEL_REACT_BASE - 等级系数/反应系数
# ============================================================

def build_level_react_base(
    bucket_data: dict,
    bucket_key: str,
    bucket_color: str,
    selected_domain: str | None,
    on_domain_click: Callable[[str, str], None]
) -> FormulaResult:
    """等级系数/反应系数模板：固定值显示

    LEVEL: 等级系数（如 1446）
    REACT_BASE: 反应系数（如超载 2.75）
    """
    value = bucket_data.get('value', 0.0)

    if bucket_key == "LEVEL":
        # 等级系数：整数显示
        formula_parts = [_text(f"{value:.0f}", color=ft.Colors.WHITE_70)]
        total_text = f"{value:.0f}"
    else:
        # 反应系数：两位小数
        formula_parts = [
            _domain_value(value, "react_coeff", bucket_key, bucket_color, selected_domain, on_domain_click, False, ".2f"),
        ]
        total_text = f"{value:.2f}"

    return FormulaResult(formula_parts, total_text)


# ============================================================
# 模板 7: EM_BONUS - 精通加成
# ============================================================

def build_em_bonus(
    bucket_data: dict,
    bucket_key: str,
    bucket_color: str,
    selected_domain: str | None,
    on_domain_click: Callable[[str, str], None]
) -> FormulaResult:
    """精通加成模板：1 + 精通收益% + 特殊加成%

    公式：1 + 16×EM/(EM+2000) + 特殊加成
    """
    em = bucket_data.get('em', 0.0)
    em_bonus_pct = bucket_data.get('em_bonus_pct', 0.0)
    special_bonus = bucket_data.get('special_bonus', 0.0)
    total_value = bucket_data.get('value', 1.0)

    formula_parts: list[ft.Control] = [_text("1+")]

    if em > 0:
        formula_parts.extend([
            _domain_value(em_bonus_pct, "em_bonus", bucket_key, bucket_color, selected_domain, on_domain_click),
            _text("%"),
        ])

    if special_bonus > 0:
        if em > 0:
            formula_parts.append(_text("+", color=ft.Colors.WHITE_38))
        formula_parts.extend([
            _domain_value(special_bonus, "special", bucket_key, bucket_color, selected_domain, on_domain_click),
            _text("%"),
        ])

    total_text = f"{total_value:.2f} (EM:{em:.0f})" if em > 0 else f"{total_value:.2f}"

    return FormulaResult(formula_parts, total_text)


# ============================================================
# 模板映射与入口函数
# ============================================================

# 常规伤害路径模板映射
NORMAL_TEMPLATE_MAP: dict[str, Callable] = {
    "CORE": build_core,           # BASE + MULT 融合
    "BONUS": build_bonus_crit,
    "CRIT": build_bonus_crit,
    "REACT": build_react,
    "DEF": build_def,
    "RES": build_res,
}

# 剧变反应路径模板映射
TRANSFORMATIVE_TEMPLATE_MAP: dict[str, Callable] = {
    "LEVEL": build_level_react_base,
    "REACT_BASE": build_level_react_base,
    "EM_BONUS": build_em_bonus,
    "RES": build_res,  # 复用常规的 RES 模板
}

# 桶到模板的映射（用于 BASE/MULT 融合场景）
# 当需要将 BASE 和 MULT 显示为一个 CORE 时使用
BUCKET_TO_TEMPLATE: dict[str, str] = {
    "BASE": "CORE",
    "MULT": "CORE",
    "BONUS": "BONUS",  # 直接映射到 NORMAL_TEMPLATE_MAP 的键
    "CRIT": "CRIT",    # 直接映射到 NORMAL_TEMPLATE_MAP 的键
    "REACT": "REACT",
    "DEF": "DEF",
    "RES": "RES",
}


def build_formula(
    bucket_key: str,
    bucket_data: dict,
    bucket_color: str,
    selected_domain: str | None,
    on_domain_click: Callable[[str, str], None]
) -> FormulaResult:
    """构建常规伤害桶公式

    Args:
        bucket_key: 乘区键（BASE/MULT/BONUS/CRIT/REACT/DEF/RES）
        bucket_data: 乘区数据
        bucket_color: 乘区颜色
        selected_domain: 选中的域
        on_domain_click: 域点击回调
    """
    template_name = BUCKET_TO_TEMPLATE.get(bucket_key, bucket_key)
    builder = NORMAL_TEMPLATE_MAP.get(template_name)

    if not builder:
        # 默认：显示系数值
        mult_val = bucket_data.get('multiplier', 1.0)
        return FormulaResult([_text(f"{mult_val:.2f}", color=ft.Colors.WHITE_70)], f"{mult_val:.2f}")

    return builder(bucket_data, bucket_key, bucket_color, selected_domain, on_domain_click)


def build_transformative_formula(
    bucket_key: str,
    bucket_data: dict,
    bucket_color: str,
    selected_domain: str | None,
    on_domain_click: Callable[[str, str], None]
) -> FormulaResult:
    """构建剧变反应桶公式

    Args:
        bucket_key: 乘区键（LEVEL/REACT_BASE/EM_BONUS/RES）
        bucket_data: 乘区数据
        bucket_color: 乘区颜色
        selected_domain: 选中的域
        on_domain_click: 域点击回调
    """
    builder = TRANSFORMATIVE_TEMPLATE_MAP.get(bucket_key)

    if not builder:
        mult_val = bucket_data.get('multiplier', 1.0)
        return FormulaResult([_text(f"{mult_val:.2f}", color=ft.Colors.WHITE_70)], f"{mult_val:.2f}")

    return builder(bucket_data, bucket_key, bucket_color, selected_domain, on_domain_click)
