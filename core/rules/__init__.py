"""模拟规则配置模块。"""

# 基类与枚举
from core.rules.base import RuleTypeBase, ApplyMode

# 注册表（从 core.registry 导入）
from core.registry import register_rule_type, RuleTypeMap

# 实例
from core.rules.instance import RuleInstance

# 规则类型（导入以触发注册）
from core.rules.types import EnergySetRule, StatEffectRule

__all__ = [
    # 基类
    "RuleTypeBase",
    "ApplyMode",
    # 注册表
    "register_rule_type",
    "RuleTypeMap",
    # 实例
    "RuleInstance",
    # 规则类型
    "EnergySetRule",
    "StatEffectRule",
]
