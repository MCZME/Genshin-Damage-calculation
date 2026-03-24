import pytest

from core.batch import (
    MAIN_BATCH_FINISHED,
    MAIN_BATCH_PROGRESS,
    MAIN_BATCH_TASK_RESULT,
)
from core.batch.models import BatchNodeKind, BatchRunRequest, BatchRunResult, TaskRunState
from ui.states.batch_editor_state import BatchEditorState
from ui.states.batch_run_state import BatchRunState
from ui.states.batch_universe_state import BatchUniverseState
from ui.view_models.universe.run_task_vm import RunTaskViewModel


def _base_config():
    return {
        "context_config": {
            "team": [{"character": {"level": 80}}],
            "environment": {"weather": "sunny"},
        }
    }


def test_state_add_delete_and_range_generation(tmp_path):
    state = BatchEditorState()
    state.storage.base_dir = str(tmp_path)
    state.initialize_project(_base_config())
    assert state.canvas_data.root.id == "root"
    assert state.inspector_vm.node_id == "root"

    state.add_range_anchor("root")
    state.rename_selected_node("等级扫描")
    state.configure_range_anchor(
        "context_config.team.0.character.level",
        "80",
        "90",
        "10",
        "等级",
    )

    anchor = state.selected_node
    assert anchor.kind.value == "range_anchor"
    assert len(anchor.children) == 2
    assert state.inspector_vm.show_range_form is True
    assert state.inspector_vm.range_children_count == 2

    state.select_node(anchor.children[0].id)
    assert state.canvas_data.selected_node_id == anchor.children[0].id
    assert anchor.children[0].id in state.node_vms
    state.delete_selected_node()
    assert len(anchor.children) == 2

    state.select_node(anchor.id)
    state.delete_selected_node()
    assert state.leaf_count == 1
    assert state.inspector_vm.node_id == "root"


def test_state_save_and_load_project(tmp_path):
    state = BatchEditorState()
    state.storage.base_dir = str(tmp_path)
    state.initialize_project(_base_config(), "save_test")
    state.add_rule_child("root")
    state.update_rule(
        "context_config.environment.weather",
        '"rainy"',
        "天气",
    )

    save_path = str(tmp_path / "save_test.json")
    state.save_project(save_path)

    loaded = BatchEditorState()
    loaded.load_project(save_path)

    assert loaded.project.name == "save_test"
    assert loaded.leaf_count == 1
    assert loaded.canvas_data.root.id == "root"
    assert loaded.inspector_vm.node_id == "root"
    child = loaded.project.root.children[0]
    assert child.rule is not None
    assert child.rule.value == "rainy"


@pytest.mark.asyncio
async def test_state_run_batch_updates_summary_and_progress():
    state = BatchUniverseState()
    state.initialize_project(_base_config())
    state.editor_state.add_rule_child("root")
    state.editor_state.update_rule(
        "context_config.team.0.character.level",
        "90",
        "等级90",
    )

    class FakeQueue:
        def __init__(self):
            self.items = []

        def put(self, payload):
            self.items.append(payload)

    queue = FakeQueue()
    state.attach_branch_queue(queue)
    summary = await state.run_batch()

    assert summary is None
    assert state.run_state.is_running is True
    assert len(queue.items) == 1
    run_id = queue.items[0]["run_id"]

    state.handle_main_message(
        {
            "type": MAIN_BATCH_PROGRESS,
            "run_id": run_id,
            "done": 1,
            "total": 1,
            "status_text": "批处理执行中 1/1",
        }
    )
    final_summary = state.handle_main_message(
        {
            "type": MAIN_BATCH_FINISHED,
            "run_id": run_id,
            "summary": {
                "total_runs": 1,
                "completed_runs": 1,
                "failed_runs": 0,
                "avg_dps": 600,
                "max_dps": 600,
                "min_dps": 600,
                "std_dev_dps": 0,
                "p95_dps": 600,
                "results": [],
                "errors": [],
            },
            "first_error": "",
        }
    )

    assert final_summary is not None
    assert final_summary.completed_runs == 1
    assert state.run_state.progress == 1.0
    assert state.run_state.last_summary is final_summary
    assert state.analysis_state.last_summary is final_summary
    assert state.run_state.is_running is False


def test_state_add_child_unified_api_and_compat():
    state = BatchEditorState()
    state.initialize_project(_base_config())

    state.add_child("root", BatchNodeKind.RULE)
    assert state.selected_node.kind == BatchNodeKind.RULE
    assert state.selected_node.name == "新规则节点"
    first_child_id = state.selected_node.id
    assert state.project.root.children[0].id == first_child_id

    state.select_node("root")
    state.add_child("root", BatchNodeKind.RANGE_ANCHOR)
    assert state.selected_node.kind == BatchNodeKind.RANGE_ANCHOR
    assert state.selected_node.name == "新区间锚点"

    state.select_node("root")
    state.add_rule_child("root")
    assert state.selected_node.kind == BatchNodeKind.RULE

    state.select_node("root")
    state.add_range_anchor("root")
    assert state.selected_node.kind == BatchNodeKind.RANGE_ANCHOR


def test_run_task_view_model():
    """测试 RunTaskViewModel 的基本功能。"""
    vm = RunTaskViewModel(
        request_id="test-1",
        node_id="node-1",
        node_name="测试节点",
    )

    # 初始状态
    assert vm.state == TaskRunState.PENDING
    assert vm.dps == 0.0
    assert vm.error is None
    assert vm.is_expanded is False

    # 设置运行中
    vm.set_state(TaskRunState.RUNNING)
    assert vm.state == TaskRunState.RUNNING

    # 设置成功结果
    vm.set_result(
        total_damage=100000.0,
        dps=5000.0,
        simulation_duration=1200,
        param_snapshot={"level": 90},
    )
    assert vm.state == TaskRunState.SUCCESS
    assert vm.dps == 5000.0
    assert vm.total_damage == 100000.0

    # 切换展开
    vm.toggle_expanded()
    assert vm.is_expanded is True
    vm.toggle_expanded()
    assert vm.is_expanded is False


def test_batch_run_state_task_management():
    """测试 BatchRunState 的任务列表管理。"""
    state = BatchRunState()

    # 初始化任务列表
    requests = [
        BatchRunRequest(
            request_id="req-1",
            node_id="node-1",
            node_name="任务1",
            config={},
        ),
        BatchRunRequest(
            request_id="req-2",
            node_id="node-2",
            node_name="任务2",
            config={},
        ),
    ]
    state.initialize_tasks(requests)

    # 验证初始化
    assert state.total_count == 2
    assert state.pending_count == 2
    assert state.success_count == 0
    assert state.error_count == 0
    assert len(state.task_order) == 2

    # 设置第一个任务为运行中
    state.set_task_running("req-1")
    assert state.tasks["req-1"].state == TaskRunState.RUNNING
    assert state.current_running_id == "req-1"

    # 更新第一个任务结果（成功）
    result = BatchRunResult(
        request_id="req-1",
        node_id="node-1",
        node_name="任务1",
        total_damage=100000.0,
        dps=5000.0,
    )
    state.update_task_result(result)
    assert state.tasks["req-1"].state == TaskRunState.SUCCESS
    assert state.success_count == 1

    # 更新第二个任务结果（失败）
    error_result = BatchRunResult(
        request_id="req-2",
        node_id="node-2",
        node_name="任务2",
        error="执行失败",
    )
    state.update_task_result(error_result)
    assert state.tasks["req-2"].state == TaskRunState.ERROR
    assert state.error_count == 1


def test_batch_run_state_console():
    """测试 BatchRunState 的控制台管理。"""
    state = BatchRunState()

    # 初始状态
    assert state.console_visible is False
    assert len(state.console_logs) == 0

    # 追加日志
    state.append_log("[INFO] 开始执行")
    state.append_log("[ERROR] 执行失败")
    assert len(state.console_logs) == 2
    assert state.console_logs[0] == "[INFO] 开始执行"

    # 切换控制台显示
    state.toggle_console()
    assert state.console_visible is True
    state.hide_console()
    assert state.console_visible is False
    state.show_console()
    assert state.console_visible is True


def test_batch_run_state_handle_task_result_message():
    """测试处理 MAIN_BATCH_TASK_RESULT 消息。"""
    state = BatchRunState()
    state.active_run_id = "run-1"

    # 初始化任务
    requests = [
        BatchRunRequest(
            request_id="req-1",
            node_id="node-1",
            node_name="任务1",
            config={},
        ),
    ]
    state.initialize_tasks(requests)

    # 发送任务结果消息
    message = {
        "type": MAIN_BATCH_TASK_RESULT,
        "run_id": "run-1",
        "result": {
            "request_id": "req-1",
            "node_id": "node-1",
            "node_name": "任务1",
            "total_damage": 100000.0,
            "dps": 5000.0,
        },
    }
    state.handle_main_message(message)

    # 验证结果
    assert state.tasks["req-1"].state == TaskRunState.SUCCESS
    assert state.tasks["req-1"].dps == 5000.0


def test_batch_run_state_task_result_before_progress():
    """测试 TASK_RESULT 先于 PROGRESS 到达时状态不被覆盖。"""
    state = BatchRunState()
    state.active_run_id = "run-1"

    # 初始化任务
    requests = [
        BatchRunRequest(
            request_id="req-1",
            node_id="node-1",
            node_name="任务1",
            config={},
        ),
    ]
    state.initialize_tasks(requests)

    # 1. 先发送 TASK_RESULT（模拟任务完成）
    result_message = {
        "type": MAIN_BATCH_TASK_RESULT,
        "run_id": "run-1",
        "result": {
            "request_id": "req-1",
            "node_id": "node-1",
            "node_name": "任务1",
            "total_damage": 100000.0,
            "dps": 5000.0,
        },
    }
    state.handle_main_message(result_message)
    assert state.tasks["req-1"].state == TaskRunState.SUCCESS

    # 2. 后发送 PROGRESS（模拟延迟到达）
    progress_message = {
        "type": MAIN_BATCH_PROGRESS,
        "run_id": "run-1",
        "done": 1,
        "total": 1,
        "running_request_id": "req-1",  # 尝试设置为 RUNNING
        "status_text": "批处理执行中 1/1",
    }
    state.handle_main_message(progress_message)

    # 3. 验证状态仍然是 SUCCESS，没有被覆盖为 RUNNING
    assert state.tasks["req-1"].state == TaskRunState.SUCCESS
    assert state.tasks["req-1"].dps == 5000.0
