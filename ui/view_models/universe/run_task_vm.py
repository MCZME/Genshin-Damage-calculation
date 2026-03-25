from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import flet as ft

from core.batch.models import TaskRunState


@ft.observable
@dataclass
class RunTaskViewModel:
    """单个运行任务的视图模型。

    使用 @ft.observable 装饰器，属性修改时会自动触发 UI 更新。
    """

    request_id: str
    node_id: str
    node_name: str
    state: TaskRunState = TaskRunState.PENDING
    total_damage: float = 0.0
    dps: float = 0.0
    simulation_duration: int = 0
    param_snapshot: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    is_expanded: bool = False

    def set_state(self, state: TaskRunState) -> None:
        """设置任务状态。"""
        self.state = state
        # @ft.observable 会自动在 __setattr__ 时调用 notify()

    def set_result(
        self,
        total_damage: float,
        dps: float,
        simulation_duration: int,
        param_snapshot: dict[str, Any],
    ) -> None:
        """设置任务成功结果。"""
        self.total_damage = total_damage
        self.dps = dps
        self.simulation_duration = simulation_duration
        self.param_snapshot = param_snapshot
        self.state = TaskRunState.SUCCESS

    def set_error(self, error: str) -> None:
        """设置任务错误。"""
        self.error = error
        self.state = TaskRunState.ERROR

    def toggle_expanded(self) -> None:
        """切换展开状态。"""
        self.is_expanded = not self.is_expanded
