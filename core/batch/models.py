from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class BatchNodeKind(str, Enum):
    ROOT = "root"
    RULE = "rule"
    RANGE_ANCHOR = "range_anchor"


@dataclass
class MutationRule:
    """批处理变异规则。第一阶段仅支持 replace。"""

    type: str = "replace"
    target_path: list[str | int] = field(default_factory=list)
    value: Any = None
    label: str = ""


@dataclass
class RangeMutationConfig:
    """区间锚点定义。"""

    target_path: list[str | int] = field(default_factory=list)
    start: float = 0.0
    end: float = 0.0
    step: float = 1.0
    label: str = ""


@dataclass
class BatchNode:
    """批处理树节点。"""

    id: str
    name: str
    kind: BatchNodeKind = BatchNodeKind.RULE
    rule: MutationRule | None = None
    range_config: RangeMutationConfig | None = None
    children: list[BatchNode] = field(default_factory=list)
    generated_from_anchor_id: str | None = None

    def is_leaf(self) -> bool:
        return len(self.children) == 0

    @property
    def is_generated(self) -> bool:
        return self.generated_from_anchor_id is not None


@dataclass
class BatchProject:
    """批处理项目根对象。"""

    version: int = 1
    name: str = "新批处理项目"
    base_config: dict[str, Any] = field(default_factory=dict)
    root: BatchNode = field(
        default_factory=lambda: BatchNode(
            id="root", name="基准配置", kind=BatchNodeKind.ROOT
        )
    )


@dataclass
class BatchRunRequest:
    """单个叶子节点编译出的运行请求。"""

    request_id: str
    node_id: str
    node_name: str
    config: dict[str, Any]
    param_snapshot: dict[str, Any] = field(default_factory=dict)
    batch_run_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "node_id": self.node_id,
            "node_name": self.node_name,
            "config": self.config,
            "param_snapshot": self.param_snapshot,
            "batch_run_id": self.batch_run_id,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> BatchRunRequest:
        return cls(
            request_id=str(payload.get("request_id", "")),
            node_id=str(payload.get("node_id", "")),
            node_name=str(payload.get("node_name", "")),
            config=dict(payload.get("config", {})),
            param_snapshot=dict(payload.get("param_snapshot", {})),
            batch_run_id=payload.get("batch_run_id"),
        )


@dataclass
class BatchRunResult:
    """单个运行结果。"""

    request_id: str
    node_id: str
    node_name: str
    total_damage: float = 0.0
    dps: float = 0.0
    simulation_duration: int = 0
    param_snapshot: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "node_id": self.node_id,
            "node_name": self.node_name,
            "total_damage": self.total_damage,
            "dps": self.dps,
            "simulation_duration": self.simulation_duration,
            "param_snapshot": self.param_snapshot,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> BatchRunResult:
        return cls(
            request_id=str(payload.get("request_id", "")),
            node_id=str(payload.get("node_id", "")),
            node_name=str(payload.get("node_name", "")),
            total_damage=float(payload.get("total_damage", 0.0)),
            dps=float(payload.get("dps", 0.0)),
            simulation_duration=int(payload.get("simulation_duration", 0)),
            param_snapshot=dict(payload.get("param_snapshot", {})),
            error=payload.get("error"),
        )


@dataclass
class BatchRunSummary:
    """批量执行摘要。"""

    total_runs: int = 0
    completed_runs: int = 0
    failed_runs: int = 0
    avg_dps: float = 0.0
    max_dps: float = 0.0
    min_dps: float = 0.0
    std_dev_dps: float = 0.0
    p95_dps: float = 0.0
    results: list[BatchRunResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_runs": self.total_runs,
            "completed_runs": self.completed_runs,
            "failed_runs": self.failed_runs,
            "avg_dps": self.avg_dps,
            "max_dps": self.max_dps,
            "min_dps": self.min_dps,
            "std_dev_dps": self.std_dev_dps,
            "p95_dps": self.p95_dps,
            "results": [result.to_dict() for result in self.results],
            "errors": list(self.errors),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> BatchRunSummary:
        return cls(
            total_runs=int(payload.get("total_runs", 0)),
            completed_runs=int(payload.get("completed_runs", 0)),
            failed_runs=int(payload.get("failed_runs", 0)),
            avg_dps=float(payload.get("avg_dps", 0.0)),
            max_dps=float(payload.get("max_dps", 0.0)),
            min_dps=float(payload.get("min_dps", 0.0)),
            std_dev_dps=float(payload.get("std_dev_dps", 0.0)),
            p95_dps=float(payload.get("p95_dps", 0.0)),
            results=[
                BatchRunResult.from_dict(item)
                for item in payload.get("results", [])
            ],
            errors=[str(item) for item in payload.get("errors", [])],
        )


class BatchCompileError(ValueError):
    """批处理编译失败。"""


# --- Backward compatibility for legacy code paths ---

ModifierRule = MutationRule


@dataclass
class SimulationNode:
    """旧版分支宇宙节点，保留以避免遗留模块导入失败。"""

    id: str
    rule: ModifierRule | None = None
    children: list[SimulationNode] = field(default_factory=list)
    name: str = ""
    is_managed: bool = False
    managed_by: str | None = None

    def is_leaf(self) -> bool:
        return len(self.children) == 0


@dataclass
class SimulationMetrics:
    """旧版单次仿真结果摘要。"""

    total_damage: float = 0.0
    dps: float = 0.0
    simulation_duration: int = 0
    event_counts: dict[str, int] = field(default_factory=dict)
    character_damage_share: dict[str, float] = field(default_factory=dict)
    param_snapshot: dict[str, Any] = field(default_factory=dict)


@dataclass
class BatchSummary:
    """旧版批量统计摘要。"""

    total_runs: int = 0
    avg_dps: float = 0.0
    max_dps: float = 0.0
    min_dps: float = 0.0
    std_dev_dps: float = 0.0
    p95_dps: float = 0.0
    results: list[SimulationMetrics] = field(default_factory=list)
