from dataclasses import dataclass


@dataclass
class ModifierRecord:
    """修饰符记录条目，用于属性或伤害的审计。"""

    source: str  # 来源 (如 "芙宁娜-气氛值", "基础攻击力")
    stat: str  # 属性名 (如 "伤害加成", "生命值%")
    value: float  # 数值
    op: str = "ADD"  # 操作: ADD, MULT, SET
