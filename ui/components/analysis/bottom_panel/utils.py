"""[V11.0] 底部面板工具函数

提供格式化等工具函数。
"""


def format_val(val: float, is_percent: bool = False) -> str:
    """格式化数值显示

    Args:
        val: 数值
        is_percent: 是否为百分比形式

    Returns:
        格式化后的字符串
    """
    if val >= 1_000_000:
        return f"{val / 1_000_000:.1f}M"
    if val >= 1_000:
        return f"{val / 1_000:.1f}k"
    if is_percent:
        return f"+{val*100:.1f}%"
    return f"{val:,.0f}"
