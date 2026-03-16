"""[V11.0] 伤害审计底部弹出面板模块

提供伤害审计详情的底部弹出面板组件。

模块结构：
- constants.py: 颜色方案和配置常量
- utils.py: 格式化工具函数
- selection_panel.py: 选择面板组件
- audit_panel.py: 审计面板组件
- main_panel.py: 主面板组件
"""
from .main_panel import DamageAuditBottomPanel
from .constants import BUCKET_COLORS, BUCKET_CONFIGS, PANEL_BG_COLOR
from .utils import format_val

__all__ = [
    "DamageAuditBottomPanel",
    "BUCKET_COLORS",
    "BUCKET_CONFIGS",
    "PANEL_BG_COLOR",
    "format_val",
]
