"""[V20.0] 乘区公式生成器

按模板分类重构，返回数据结构而非组件。

[V20.0] 数据结构设计：
- FormulaPartData: 公式部分数据（TextPart | DomainValuePart）
- TextPart: 纯文本
- DomainValuePart: 可点击的域值
- FormulaResult: 公式生成结果（数据）

组件创建在渲染层完成，ViewModel 只持有数据。

[V21.0] 模块拆分：
- types.py: 数据结构定义
- templates/: 模板函数（按伤害类型分类）
- builder.py: 入口函数
"""

# 从子模块导出公共接口
from .types import (
    TextPart,
    DomainValuePart,
    FormulaPartData,
    FormulaResult,
    domain_value,
    text,
)
from .builder import (
    build_formula,
    build_transformative_formula,
    build_lunar_formula,
)
from .templates import (
    # 常规伤害模板
    build_core,
    build_bonus_crit,
    build_react,
    build_def,
    build_res,
    # 剧变反应模板
    build_level_react_base,
    build_transformative_react,
    # 月曜反应模板
    build_lunar_base,
    build_ascension,
    # 模板映射
    NORMAL_TEMPLATE_MAP,
    TRANSFORMATIVE_TEMPLATE_MAP,
    LUNAR_TEMPLATE_MAP,
    BUCKET_TO_TEMPLATE,
)

__all__ = [
    # 数据类型
    "TextPart",
    "DomainValuePart",
    "FormulaPartData",
    "FormulaResult",
    # 辅助函数
    "domain_value",
    "text",
    # 入口函数
    "build_formula",
    "build_transformative_formula",
    "build_lunar_formula",
    # 常规伤害模板
    "build_core",
    "build_bonus_crit",
    "build_react",
    "build_def",
    "build_res",
    # 剧变反应模板
    "build_level_react_base",
    "build_transformative_react",
    # 月曜反应模板
    "build_lunar_base",
    "build_ascension",
    # 模板映射
    "NORMAL_TEMPLATE_MAP",
    "TRANSFORMATIVE_TEMPLATE_MAP",
    "LUNAR_TEMPLATE_MAP",
    "BUCKET_TO_TEMPLATE",
]
