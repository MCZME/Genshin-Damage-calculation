from __future__ import annotations

from typing import Any

from core.batch import BatchRunSummary
from ui.states.batch_analysis_state import BatchAnalysisState
from ui.states.batch_editor_state import BatchEditorState
from ui.states.batch_run_state import BatchRunState


class BatchUniverseState:
    """分支宇宙子应用的状态协调器。"""

    def __init__(self) -> None:
        self.editor_state = BatchEditorState()
        self.run_state = BatchRunState()
        self.analysis_state = BatchAnalysisState()

    def attach_page(self, page: Any) -> None:
        self.editor_state.page = page
        self.run_state.page = page
        self.analysis_state.page = page

    def attach_branch_queue(self, branch_to_main_queue: Any) -> None:
        self.run_state.branch_to_main_queue = branch_to_main_queue

    def initialize_project(
        self, base_config: dict[str, Any], name: str = "批处理项目"
    ) -> None:
        self.editor_state.initialize_project(base_config, name)
        self.run_state.reset("已加载基准配置")
        self.analysis_state.clear()

    def load_project(self, path: str) -> None:
        self.editor_state.load_project(path)
        self.run_state.reset("已加载批处理项目")
        self.analysis_state.clear()

    async def run_batch(self) -> BatchRunSummary | None:
        self.analysis_state.clear()
        return await self.run_state.run_batch(self.editor_state.project)

    def handle_main_message(self, message: dict[str, Any]) -> BatchRunSummary | None:
        summary = self.run_state.handle_main_message(message)
        if summary is not None:
            self.analysis_state.apply_summary(summary)
        return summary

    def handle_main_error(self, run_id: str | None, error_text: str) -> None:
        self.run_state.handle_main_error(run_id, error_text)
