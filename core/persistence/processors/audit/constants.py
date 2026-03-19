"""[V7.2] 审计处理常量定义

提供审计处理器的映射表和常量。
"""

# 核心映射表：从中文字段映射到 7 个 UI 审计桶
# [V2.5.5] 适配脱水存储机制：新增独立乘区%、倍率加值%、无视防御%
BUCKET_MAP: dict[str, list[str]] = {
    "BASE": ["攻击力", "生命值", "防御力", "元素精通"],
    "MULTIPLIER": ["技能倍率%", "独立乘区%", "倍率加值%", "固定伤害值加成", "倍率"],
    "BONUS": ["伤害加成", "动作类型增伤"],
    "CRIT": ["暴击乘数"],  # [V2.5.5] 替代 "暴击伤害"，直接存储乘数值
    "REACTION": ["反应基础倍率", "反应加成系数", "剧变反应基础"],
    "DEFENSE": ["防御区系数", "无视防御%"],
    "RESISTANCE": ["抗性区系数"]
}

# 来源类型映射表 [V10.0]
SOURCE_TYPE_MAP: dict[str, str] = {
    "武器": "Weapon",
    "圣遗物": "Artifact",
    "套装": "Artifact",
    "天赋": "Talent",
    "命座": "Constellation",
    "共鸣": "Resonance",
    "元素共鸣": "Resonance",
}

# 来源类型展示顺序
SOURCE_ORDER: list[str] = [
    "Weapon", "Artifact", "Talent", "Constellation", "Resonance", "Other"
]

# 基础属性列表（用于从帧快照提取）
BASE_STATS: list[str] = ["攻击力", "生命值", "防御力", "元素精通", "攻击力%", "生命值%", "防御力%", "固定攻击力", "固定生命值", "固定防御力"]