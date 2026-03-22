from __future__ import annotations

from typing import Any, cast

import flet as ft

from core.batch import BatchRunSummary


@ft.observable
class BatchAnalysisState:
    """批处理分析页面状态。"""

    def __init__(self) -> None:
        self.page: Any = None
        self.last_summary: BatchRunSummary | None = None

    def notify_update(self) -> None:
        cast(Any, self).notify()  # type: ignore

    def clear(self) -> None:
        self.last_summary = None
        self.notify_update()

    def apply_summary(self, summary: BatchRunSummary | None) -> None:
        self.last_summary = summary
        self.notify_update()
