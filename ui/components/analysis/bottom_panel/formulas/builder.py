"""[V20.0] 公式生成器入口

提供统一的公式生成接口，按伤害类型选择对应的模板。
"""

from .types import FormulaResult, text
from .templates import (
    NORMAL_TEMPLATE_MAP,
    TRANSFORMATIVE_TEMPLATE_MAP,
    LUNAR_TEMPLATE_MAP,
    BUCKET_TO_TEMPLATE,
)


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
        return FormulaResult([text(f"{mult_val:.2f}", color="white70")], f"{mult_val:.2f}")

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
        return FormulaResult([text(f"{mult_val:.2f}", color="white70")], f"{mult_val:.2f}")

    return builder(bucket_data, bucket_key, bucket_color)


def build_lunar_formula(
    bucket_key: str,
    bucket_data: dict,
    bucket_color: str,
) -> FormulaResult:
    """构建月曜反应桶公式（返回数据结构）

    [V17.0] 新增月曜反应支持

    Args:
        bucket_key: 乘区键
        bucket_data: 乘区数据
        bucket_color: 乘区颜色
    """
    builder = LUNAR_TEMPLATE_MAP.get(bucket_key)

    if not builder:
        mult_val = bucket_data.get("multiplier", 1.0)
        return FormulaResult([text(f"{mult_val:.2f}", color="white70")], f"{mult_val:.2f}")

    return builder(bucket_data, bucket_key, bucket_color)
