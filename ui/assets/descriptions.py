"""
[V9.6] 状态效果描述资产

提供效果名称到描述模板的映射，支持格式化字符串注入动态数值。
动态数值来自 simulation_mechanism_metrics 表，通过 entity_snapshot["metrics"] 访问。

使用方式：
    template = EFFECT_DESCRIPTIONS["普世欢腾"]
    description = template.format(**metrics)  # metrics 包含 {"气氛值": 150, ...}
"""

EFFECT_DESCRIPTIONS: dict[str, str] = {
    # 芙宁娜 - 普世欢腾
    "普世欢腾": (
        "累计气氛值，提升造成的伤害与受治疗加成。\n"
        "当前气氛值: {气氛值:.0f}"
    ),
    # 钟离 - 玉璋护盾
    "玉璋护盾": "处于护盾保护下，降低周围敌人 20% 所有元素抗性与物理抗性。",
    # 可持续扩展...
}
