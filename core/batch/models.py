from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

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
    avg_dps: float = 0.0
    max_dps: float = 0.0
    min_dps: float = 0.0
    std_dev_dps: float = 0.0
    p95_dps: float = 0.0
    results: List[SimulationMetrics] = field(default_factory=list)
