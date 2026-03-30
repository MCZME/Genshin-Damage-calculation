"""反应系统模块。

提供反应处理相关的类：
- ReactionSystem: 反应系统入口
- ICDManager: 受击 ICD 管理器
- LunarConverter: 月曜反应转换器
- TransformativeHandler: 剧变反应处理器
- StatusHandler: 状态类反应处理器
- LunarHandler: 月曜反应处理器
"""

from .system import ReactionSystem
from .icd import ICDManager
from .converter import LunarConverter
from .handlers import TransformativeHandler, StatusHandler, LunarHandler

__all__ = [
    "ReactionSystem",
    "ICDManager",
    "LunarConverter",
    "TransformativeHandler",
    "StatusHandler",
    "LunarHandler",
]
