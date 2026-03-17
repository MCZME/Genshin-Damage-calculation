"""[V11.0] 底部面板常量定义

提供颜色方案和配置常量。
"""
import flet as ft

# 乘区颜色方案
BUCKET_COLORS: dict[str, str] = {
    # [V13.0] 常规伤害 6 桶
    "CORE": ft.Colors.AMBER_400,      # 核心伤害（BASE + MULT 融合）
    "BONUS": ft.Colors.CYAN_400,      # 增伤乘区
    "CRIT": ft.Colors.RED_400,        # 暴击乘区
    "REACT": ft.Colors.PURPLE_400,    # 反应乘区
    "DEF": ft.Colors.BLUE_400,        # 防御减免
    "RES": ft.Colors.TEAL_400,        # 抗性削减
    # [V12.0] 剧变反应专用颜色
    "LEVEL": ft.Colors.INDIGO_400,    # 等级系数
    "REACT_BASE": ft.Colors.PINK_400, # 反应系数
    "EM_BONUS": ft.Colors.LIME_400,   # 精通加成
}

# 乘区配置: (显示键, 标签, 数据键)
BUCKET_CONFIGS = [
    ("BASE", "基础属性", "base"),
    ("MULT", "倍率加值", "multiplier"),
    ("BONUS", "增伤乘区", "bonus"),
    ("CRIT", "暴击乘区", "crit"),
    ("REACT", "反应乘区", "reaction"),
    ("DEF", "防御减免", "defense"),
    ("RES", "抗性削减", "resistance"),
]

# [V16.0] 剧变反应 3 桶配置
# 公式：等级系数 × 反应系数×(1+精通收益+特殊加成) × 抗性区
TRANSFORMATIVE_BUCKET_CONFIGS = [
    ("LEVEL", "等级系数", "level_coeff"),
    ("REACT", "反应乘区", "reaction"),
    ("RES", "抗性区", "resistance"),
]

# [V12.0] 常规伤害 6 桶配置（合并 BASE+MULT 为 CORE）
# 公式：Core_DMG × 增伤区 × 暴击区 × 反应区 × 防御区 × 抗性区
NORMAL_BUCKET_CONFIGS = [
    ("CORE", "核心伤害", "core_dmg"),
    ("BONUS", "增伤乘区", "bonus"),
    ("CRIT", "暴击乘区", "crit"),
    ("REACT", "反应乘区", "reaction"),
    ("DEF", "防御减免", "defense"),
    ("RES", "抗性削减", "resistance"),
]

# 面板背景色
PANEL_BG_COLOR = "#2B2738"
