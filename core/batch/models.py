from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union
from enum import Enum

class ModifierMode(Enum):
    SWEEP = "SWEEP"     # 区间扫描 [start, end, step]
    REPLACE = "REPLACE" # 列表替换 [val1, val2, ...]
    RANDOM = "RANDOM"   # 随机波动 [min, max]

@dataclass
class ModifierRule:
    """基准修改规则"""
    target_path: List[Union[str, int]] # 路径，如 ["context_config", "team", 0, "character", "level"]
    mode: ModifierMode
    values: List[Any]                  # 生成的候选值列表
    label: str = ""                    # 易读名称

@dataclass
class SimulationNode:
    """分支宇宙树节点"""
    id: str
    rule: Optional[ModifierRule] = None
    children: List['SimulationNode'] = field(default_factory=list)
    name: str = "" # 可读名称

    def is_leaf(self) -> bool:
        return len(self.children) == 0

@dataclass
class SimulationMetrics:
    """单次仿真结果摘要"""
    total_damage: float = 0.0
    dps: float = 0.0
    simulation_duration: int = 0 # 帧
    event_counts: Dict[str, int] = field(default_factory=dict)
    character_damage_share: Dict[str, float] = field(default_factory=dict)
    # 用于识别该结果对应的参数
    param_snapshot: Dict[str, Any] = field(default_factory=dict)

@dataclass
class BatchSummary:
    """批量处理统计摘要"""
    total_runs: int = 0
    rules: List[ModifierRule] = field(default_factory=list) # 本次运行采用的规则
    avg_dps: float = 0.0
    max_dps: float = 0.0
    min_dps: float = 0.0
    std_dev_dps: float = 0.0
    p95_dps: float = 0.0
    results: List[SimulationMetrics] = field(default_factory=list)
