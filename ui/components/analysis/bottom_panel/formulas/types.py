"""[V20.0] 乘区公式数据结构定义

提供公式生成的基础数据类型。
"""

from dataclasses import dataclass, field


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
    parts_line2: list[FormulaPartData] = field(default_factory=list)  # 第二行公式（可选）


# ============================================================
# 辅助函数
# ============================================================


def domain_value(
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


def text(content: str, size: int = 10, color: str = "white54") -> TextPart:
    """创建文本数据"""
    return TextPart(content=content, size=size, color=color)
