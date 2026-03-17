"""[V14.1] 防御区/抗性区系数计算工具类

为 UI 端提供防御区和抗性区的系数计算功能。

背景：
- damage_system.py 中计算防御区/抗性区系数时设置 audit=False，不入库
- bucket_processor.py 的 aggregate_buckets 从审计链提取系数失败，默认为 1.0
- 本工具类在 UI 端根据原始参数重新计算系数
"""


def calculate_defense_coefficient(raw_data: dict) -> float:
    """计算防御区系数

    公式：系数 = K / (K + Def')
    其中：
    - K = 攻击者等级 * 5 + 500
    - Def' = 目标面板防御力 * (1 - (减防% + 无视防御%) / 100)

    Args:
        raw_data: 原始数据字典，包含：
            - attacker_level: 攻击者等级（默认 90）
            - target_defense: 目标面板防御力（默认 500）
            - def_reduction_pct: 减防百分比（默认 0）
            - def_ignore_pct: 无视防御百分比（默认 0）

    Returns:
        防御区系数（0~1 之间）
    """
    attacker_level = raw_data.get("attacker_level", 90)
    target_defense = raw_data.get("target_defense", 500)
    def_reduction_pct = raw_data.get("def_reduction_pct", 0.0)
    def_ignore_pct = raw_data.get("def_ignore_pct", 0.0)

    # K = 攻击者等级 * 5 + 500
    K = attacker_level * 5 + 500

    # 计算总减防比例
    total_reduction = (def_reduction_pct + def_ignore_pct) / 100.0

    # 计算有效防御力
    final_def = target_defense * (1.0 - total_reduction)

    # 防御系数 = K / (K + Def')
    if final_def > 0:
        return K / (K + final_def)
    return 1.0


def calculate_resistance_coefficient(raw_data: dict) -> float:
    """计算抗性区系数

    分段函数：
    - R < 0:       系数 = 1 - R/2  （负抗性收益递减）
    - 0 <= R <= 0.75: 系数 = 1 - R  （正常区间）
    - R > 0.75:    系数 = 1 / (1 + 4R)  （高抗性惩罚）

    其中 R 为最终抗性值（小数形式，如 0.1 表示 10%）

    Args:
        raw_data: 原始数据字典，包含：
            - final_resistance: 最终抗性值（百分比形式，如 10 表示 10%，默认 0）
            - element_type: 元素类型（用于日志，不影响计算）

    Returns:
        抗性区系数
    """
    final_resistance = raw_data.get("final_resistance", 0.0)

    # 将百分比转换为小数形式
    R = final_resistance / 100.0

    if R < 0:
        # 负抗性：收益递减
        return 1.0 - R / 2.0
    elif R > 0.75:
        # 高抗性：惩罚
        return 1.0 / (1.0 + 4.0 * R)
    else:
        # 正常区间
        return 1.0 - R
