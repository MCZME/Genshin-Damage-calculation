"""[V7.2 Pro] 伤害审计处理器模块

负责将离散的审计记录聚合为标准的 7 乘区模型，适配全 ADD 增量逻辑。

[V12.0] 支持两种伤害路径：
- 常规伤害路径：7 桶模型
- 剧变反应路径：4 桶模型

模块结构：
- types.py: 数据类型定义
- constants.py: 常量映射表
- bucket_processor.py: 桶分类与处理逻辑
- domain_calculator.py: 域计算逻辑
- processor.py: AuditProcessor 类定义
"""
from .processor import AuditProcessor
from .types import DomainValues, DamageType, DamageTypeContext
from .constants import BUCKET_MAP, SOURCE_TYPE_MAP, SOURCE_ORDER, BASE_STATS

# 导出公共接口
__all__ = [
    "AuditProcessor",
    "DomainValues",
    "DamageType",
    "DamageTypeContext",
    "BUCKET_MAP",
    "SOURCE_TYPE_MAP",
    "SOURCE_ORDER",
    "BASE_STATS",
]