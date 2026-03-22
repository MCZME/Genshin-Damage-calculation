from __future__ import annotations

import flet as ft
import json
import os
import uuid
from typing import Any, cast

from core.batch import (
    BRANCH_RUN_BATCH_REQUEST,
    BatchCompileError,
    BatchExecutionService,
    BatchNode,
    BatchNodeKind,
    BatchProject,
    BatchProjectCompiler,
    BatchProjectStorage,
    BatchRunSummary,
    MutationRule,
    MAIN_BATCH_FINISHED,
    MAIN_BATCH_PROGRESS,
    MAIN_BATCH_REJECTED,
    RangeMutationConfig,
)
from core.logger import get_ui_logger
from ui.view_models.universe import (
    MindMapCanvasData,
    NodeInspectorPanelViewModel,
    NodeViewModel,
)


@ft.observable
class BatchEditorState:
    """独立批处理编辑器状态。"""

    def __init__(self) -> None:
        self.page : Any = None
        self.storage = BatchProjectStorage()
        self.executor = BatchExecutionService()
        self.branch_to_main_queue = None
        self.project = BatchProject()
        self.selected_node_id = self.project.root.id
        self.node_vms: dict[str, NodeViewModel] = {}
        self.inspector_vm = NodeInspectorPanelViewModel()
        self.drawer_open = False
        self.drawer_parent_id = "root"
        self.drawer_anchor_x = 0.0
        self.drawer_anchor_y = 0.0
        self.canvas_data = MindMapCanvasData(
            root=self.project.root,
            selected_node_id=self.selected_node_id,
            node_index=self.node_vms,
            drawer_open=self.drawer_open,
            drawer_parent_id=self.drawer_parent_id,
            drawer_anchor_x=self.drawer_anchor_x,
            drawer_anchor_y=self.drawer_anchor_y,
        )
        self.status_text = "等待初始化"
        self.progress = 0.0
        self.is_running = False
        self.active_run_id: str | None = None
        self.error_message = ""
        self.last_summary: BatchRunSummary | None = None
        self._sync_view_models()

    @property
    def selected_node(self) -> BatchNode:
        node = self.find_node(self.selected_node_id)
        return node or self.project.root

    @property
    def leaf_count(self) -> int:
        try:
            return len(BatchProjectCompiler.compile(self.project))
        except BatchCompileError:
            return 0
        
    def notify_update(self):
        cast(Any, self).notify()  # type: ignore

    def initialize_project(self, base_config: dict[str, Any], name: str = "批处理项目") -> None:
        self.project = BatchProject(name=name, base_config=base_config or {})
        self.selected_node_id = self.project.root.id
        self.status_text = "已加载基准配置"
        self.progress = 0.0
        self.error_message = ""
        self.last_summary = None
        self._sync_view_models()
        self.notify_update()

    def list_projects(self) -> list[str]:
        return self.storage.list_projects()

    def save_project(self, path: str) -> str:
        """保存项目到指定路径。"""
        if path:
            self.project.name = os.path.splitext(os.path.basename(path))[0]
        saved_path = self.storage.save_to_path(self.project, path)
        self.status_text = f"已保存: {os.path.basename(saved_path)}"
        self._sync_view_models()
        self.notify_update()
        return saved_path

    def load_project(self, path: str) -> None:
        """从指定路径加载项目。"""
        self.project = self.storage.load_from_path(path)
        self.selected_node_id = self.project.root.id
        self.status_text = f"已加载: {os.path.basename(path)}"
        self.error_message = ""
        self.last_summary = None
        self._sync_view_models()
        self.notify_update()

    def select_node(self, node_id: str) -> None:
        self.selected_node_id = node_id
        self.error_message = ""
        self._sync_view_models()
        self.notify_update()

    def rename_selected_node(self, name: str) -> None:
        node = self.selected_node
        node.name = name or node.name
        self._sync_view_models()
        self.notify_update()

    def add_rule_child(self, parent_id: str | None = None) -> None:
        self.add_child(parent_id=parent_id, kind=BatchNodeKind.RULE)

    def add_range_anchor(self, parent_id: str | None = None) -> None:
        self.add_child(parent_id=parent_id, kind=BatchNodeKind.RANGE_ANCHOR)

    def add_child(self, parent_id: str | None, kind: BatchNodeKind) -> None:
        parent = self.find_node(parent_id or self.selected_node_id)
        if not parent:
            return
        default_names = {
            BatchNodeKind.RULE: "新规则节点",
            BatchNodeKind.RANGE_ANCHOR: "新区间锚点",
        }
        new_node = BatchNode(
            id=self._new_id(),
            name=default_names.get(kind, "新节点"),
            kind=kind,
        )
        parent.children.append(new_node)
        self.selected_node_id = new_node.id
        self._sync_view_models()
        self.notify_update()

    def open_add_drawer(self, parent_id: str, x: float, y: float) -> None:
        self.drawer_parent_id = parent_id
        self.drawer_anchor_x = x
        self.drawer_anchor_y = y
        self.drawer_open = True
        self._sync_view_models()
        self.notify_update()

    def close_add_drawer(self) -> None:
        self.drawer_open = False
        self._sync_view_models()
        self.notify_update()

    def delete_selected_node(self) -> None:
        target = self.selected_node
        if target.kind == BatchNodeKind.ROOT or target.is_generated:
            return

        def prune(parent: BatchNode) -> bool:
            for child in list(parent.children):
                if child.id == target.id:
                    parent.children.remove(child)
                    return True
                if prune(child):
                    return True
            return False

        prune(self.project.root)
        self.selected_node_id = self.project.root.id
        self._sync_view_models()
        self.notify_update()

    def update_rule(self, path_text: str, value_text: str, label: str) -> None:
        node = self.selected_node
        if node.kind != BatchNodeKind.RULE:
            return
        node.rule = MutationRule(
            target_path=self._parse_path(path_text),
            value=self._parse_value(value_text),
            label=label.strip(),
        )
        if label.strip():
            node.name = label.strip()
        self.error_message = ""
        self._sync_view_models()
        self.notify_update()

    def configure_range_anchor(
        self,
        path_text: str,
        start_text: str,
        end_text: str,
        step_text: str,
        label: str,
    ) -> None:
        node = self.selected_node
        if node.kind != BatchNodeKind.RANGE_ANCHOR:
            return

        start = float(start_text)
        end = float(end_text)
        step = float(step_text)
        if step == 0:
            raise ValueError("区间步长不能为 0。")

        node.range_config = RangeMutationConfig(
            target_path=self._parse_path(path_text),
            start=start,
            end=end,
            step=step,
            label=label.strip(),
        )
        node.name = label.strip() or "区间锚点"
        node.children = self._build_range_children(node)
        self.error_message = ""
        self._sync_view_models()
        self.notify_update()

    async def run_batch(self) -> BatchRunSummary | None:
        if self.is_running:
            return None

        self.is_running = True
        self.progress = 0.0
        self.status_text = "编译批处理任务中..."
        self.error_message = ""
        self.last_summary = None
        self.notify_update()

        try:
            requests = BatchProjectCompiler.compile(self.project)
            if not requests:
                self.status_text = "没有可执行的叶子任务"
                self.is_running = False
                self.notify_update()
                return None
            if self.branch_to_main_queue is None:
                raise RuntimeError("IPC 未连接，无法提交到主进程执行。")

            run_id = uuid.uuid4().hex
            self.active_run_id = run_id
            payload = {
                "type": BRANCH_RUN_BATCH_REQUEST,
                "run_id": run_id,
                "project_name": self.project.name,
                "requests": [request.to_dict() for request in requests],
            }
            self.branch_to_main_queue.put(payload)
            self.status_text = f"已提交主进程执行（{len(requests)} 个任务）"
            self.notify_update()
            return None
        except (BatchCompileError, ValueError) as exc:
            self.error_message = str(exc)
            self.status_text = "批处理执行失败"
            self.is_running = False
            self.active_run_id = None
            self.notify_update()
            raise
        except Exception as exc:
            self.error_message = str(exc)
            self.status_text = "批处理提交失败"
            self.is_running = False
            self.active_run_id = None
            self.notify_update()
            raise

    def handle_main_message(self, message: dict[str, Any]) -> BatchRunSummary | None:
        msg_type = str(message.get("type", ""))
        run_id = str(message.get("run_id", ""))

        if not run_id or run_id != self.active_run_id:
            return None

        if msg_type == MAIN_BATCH_PROGRESS:
            done = int(message.get("done", 0))
            total = int(message.get("total", 0))
            status_text = str(message.get("status_text", f"批处理执行中 {done}/{total}"))
            self.progress = done / total if total else 0.0
            self.status_text = status_text
            self.notify_update()
            return None

        if msg_type == MAIN_BATCH_REJECTED:
            reason = str(message.get("reason", "unknown"))
            detail = str(message.get("message", "主进程拒绝执行请求。"))
            self.error_message = detail
            self.status_text = f"执行被拒绝（{reason}）"
            self.is_running = False
            self.active_run_id = None
            self.notify_update()
            return None

        if msg_type == MAIN_BATCH_FINISHED:
            summary_payload = message.get("summary", {})
            summary = BatchRunSummary.from_dict(summary_payload)
            self.last_summary = summary
            self.progress = 1.0
            first_error = str(message.get("first_error", "") or "")
            if summary.failed_runs > 0:
                self.error_message = first_error or "批处理中存在失败任务，请检查日志。"
            self.status_text = (
                f"完成 {summary.completed_runs}/{summary.total_runs}，"
                f"失败 {summary.failed_runs}，平均 DPS {int(summary.avg_dps)}"
            )
            self.is_running = False
            self.active_run_id = None
            self.notify_update()
            return summary

        return None

    def handle_main_error(self, run_id: str | None, error_text: str) -> None:
        if not run_id or run_id != self.active_run_id:
            return
        get_ui_logger().log_error(f"Batch editor main-side error: {error_text}")
        self.error_message = error_text
        self.status_text = "主进程执行失败"
        self.is_running = False
        self.active_run_id = None
        self.notify_update()

    def find_node(self, node_id: str) -> BatchNode | None:
        def walk(current: BatchNode) -> BatchNode | None:
            if current.id == node_id:
                return current
            for child in current.children:
                found = walk(child)
                if found:
                    return found
            return None

        return walk(self.project.root)

    def _sync_view_models(self) -> None:
        selected = self.find_node(self.selected_node_id)
        if not selected:
            selected = self.project.root
            self.selected_node_id = selected.id

        node_vms: dict[str, NodeViewModel] = {}

        def walk(node: BatchNode) -> None:
            rule_label = node.rule.label if node.rule and node.rule.label else ""

            # 格式化路径和值
            target_path = ""
            value_text = ""
            range_info = ""

            if node.kind == BatchNodeKind.RULE and node.rule:
                target_path = self._format_path(node.rule.target_path)
                value_text = self._format_value(node.rule.value)
            elif node.kind == BatchNodeKind.RANGE_ANCHOR and node.range_config:
                target_path = self._format_path(node.range_config.target_path)
                cfg = node.range_config
                range_info = f"{cfg.start}~{cfg.end} (步长 {cfg.step})"

            vm = NodeViewModel(
                id=node.id,
                name=node.name,
                kind=node.kind,
                is_generated=node.is_generated,
                children_count=len(node.children),
                rule_label=rule_label,
                range_child_count=len(node.children)
                if node.kind == BatchNodeKind.RANGE_ANCHOR
                else 0,
                target_path=target_path,
                value_text=value_text,
                range_info=range_info,
            )
            node_vms[node.id] = vm
            for child in node.children:
                walk(child)

        walk(self.project.root)
        self.node_vms = node_vms
        self.canvas_data = MindMapCanvasData(
            root=self.project.root,
            selected_node_id=self.selected_node_id,
            node_index=self.node_vms,
            drawer_open=self.drawer_open,
            drawer_parent_id=self.drawer_parent_id,
            drawer_anchor_x=self.drawer_anchor_x,
            drawer_anchor_y=self.drawer_anchor_y,
        )
        self.inspector_vm = self._build_inspector_vm(selected)

    def _build_inspector_vm(self, node: BatchNode) -> NodeInspectorPanelViewModel:
        config = node.range_config
        return NodeInspectorPanelViewModel(
            node_id=node.id,
            node_name=node.name,
            node_kind=node.kind,
            is_generated=node.is_generated,
            rule_path_text=self.get_rule_path_text(node),
            rule_value_text=self.get_rule_value_text(node),
            range_path_text=self.get_range_path_text(node),
            range_start_text=str(config.start) if config else "0",
            range_end_text=str(config.end) if config else "10",
            range_step_text=str(config.step) if config else "1",
            range_label_text=config.label if config else node.name,
            range_children_count=len(node.children),
            can_delete=node.kind != BatchNodeKind.ROOT and not node.is_generated,
            show_rule_form=node.kind == BatchNodeKind.RULE,
            show_range_form=node.kind == BatchNodeKind.RANGE_ANCHOR,
            help_text=(
                "根节点仅代表当前工作台导出的基准配置，右侧只负责定义结构和规则。"
                if node.kind == BatchNodeKind.ROOT
                else ""
            ),
            base_config=self.project.base_config,
        )

    def get_rule_path_text(self, node: BatchNode) -> str:
        if not node.rule:
            return ""
        return ".".join(map(str, node.rule.target_path))

    def get_rule_value_text(self, node: BatchNode) -> str:
        if not node.rule:
            return ""
        value = node.rule.value
        if isinstance(value, (dict, list, bool, int, float)):
            return json.dumps(value, ensure_ascii=False)
        return str(value)

    def get_range_path_text(self, node: BatchNode) -> str:
        if not node.range_config:
            return ""
        return ".".join(map(str, node.range_config.target_path))

    def _build_range_children(self, anchor: BatchNode) -> list[BatchNode]:
        assert anchor.range_config is not None
        config = anchor.range_config
        values: list[float] = []
        current = config.start
        if config.step > 0:
            while current <= config.end + 1e-9:
                values.append(round(current, 10))
                current += config.step
        else:
            while current >= config.end - 1e-9:
                values.append(round(current, 10))
                current += config.step

        children = []
        for value in values:
            text_value = int(value) if float(value).is_integer() else value
            child = BatchNode(
                id=self._new_id(),
                name=str(text_value),
                kind=BatchNodeKind.RULE,
                rule=MutationRule(
                    target_path=list(config.target_path),
                    value=text_value,
                    label=f"{config.label or 'range'}={text_value}",
                ),
                generated_from_anchor_id=anchor.id,
            )
            children.append(child)
        return children

    @staticmethod
    def _parse_path(path_text: str) -> list[Any]:
        pieces = [piece.strip() for piece in path_text.split(".") if piece.strip()]
        parsed: list[Any] = []
        for piece in pieces:
            if piece.isdigit():
                parsed.append(int(piece))
            else:
                parsed.append(piece)
        return parsed

    @staticmethod
    def _parse_value(value_text: str) -> Any:
        stripped = value_text.strip()
        if not stripped:
            return ""
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            return stripped

    @staticmethod
    def _new_id() -> str:
        return uuid.uuid4().hex[:10]

    @staticmethod
    def _format_path(path: list[str | int], max_segments: int = 3) -> str:
        """将路径列表格式化为可读字符串，默认只显示最后三个字段。

        数组索引不算独立字段，而是附加在前面的字段上。
        例如: ["context_config", "team", 0, "character", "level"] -> "team[0].character.level"
        """
        # 先格式化完整路径
        formatted_segments: list[str] = []
        for p in path:
            if isinstance(p, int):
                if formatted_segments:
                    formatted_segments[-1] += f"[{p}]"
                else:
                    formatted_segments.append(f"[{p}]")
            else:
                formatted_segments.append(str(p))

        # 只取最后 max_segments 个字段
        segments = formatted_segments[-max_segments:] if len(formatted_segments) > max_segments else formatted_segments
        return ".".join(segments)

    @staticmethod
    def _format_value(value: Any) -> str:
        """将值格式化为可读字符串。"""
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        return str(value)
