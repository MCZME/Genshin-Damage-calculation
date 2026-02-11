from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union

@dataclass
class ModifierRule:
    """变异规则：目前仅支持替换 (REPLACE)"""
    target_path: List[Union[str, int]] 
    value: Any                         # 单一具体值
    label: str = ""                    # 易读名称

@dataclass
class SimulationNode:
    """分支宇宙树节点"""
    id: str
    rule: Optional[ModifierRule] = None
    children: List['SimulationNode'] = field(default_factory=list)
    name: str = "" 
    
    # 扩展属性
    is_managed: bool = False           # 是否为受控节点 (不可手动修改/删除)
    managed_by: Optional[str] = None   # 父级区间节点的 ID
    
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
