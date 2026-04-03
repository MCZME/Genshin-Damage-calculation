"""[V20.0] 公式模板包

按伤害类型分类的模板函数：
- normal: 常规伤害模板
- transformative: 剧变反应模板
- lunar: 月曜反应模板
"""

from .normal import (
    build_core,
    build_bonus_crit,
    build_react,
    build_def,
    build_res,
    NORMAL_TEMPLATE_MAP,
    BUCKET_TO_TEMPLATE,
)
from .transformative import (
    build_level_react_base,
    build_transformative_react,
    TRANSFORMATIVE_TEMPLATE_MAP,
)
from .lunar import (
    build_lunar_base,
    build_ascension,
    LUNAR_TEMPLATE_MAP,
)

__all__ = [
    # 常规伤害
    "build_core",
    "build_bonus_crit",
    "build_react",
    "build_def",
    "build_res",
    "NORMAL_TEMPLATE_MAP",
    "BUCKET_TO_TEMPLATE",
    # 剧变反应
    "build_level_react_base",
    "build_transformative_react",
    "TRANSFORMATIVE_TEMPLATE_MAP",
    # 月曜反应
    "build_lunar_base",
    "build_ascension",
    "LUNAR_TEMPLATE_MAP",
]
