import pytest

from core.batch import MAIN_BATCH_FINISHED, MAIN_BATCH_PROGRESS
from core.batch.models import BatchNodeKind
from ui.states.batch_editor_state import BatchEditorState


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

    state.save_project("save_test")

    loaded = BatchEditorState()
    loaded.storage.base_dir = str(tmp_path)
    loaded.load_project("save_test.json")

    assert loaded.project.name == "save_test"
    assert loaded.leaf_count == 1
    assert loaded.canvas_data.root.id == "root"
    assert loaded.inspector_vm.node_id == "root"
    child = loaded.project.root.children[0]
    assert child.rule is not None
    assert child.rule.value == "rainy"


@pytest.mark.asyncio
async def test_state_run_batch_updates_summary_and_progress():
    state = BatchEditorState()
    state.initialize_project(_base_config())
    state.add_rule_child("root")
    state.update_rule(
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
    state.branch_to_main_queue = queue
    summary = await state.run_batch()

    assert summary is None
    assert state.is_running is True
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
    assert state.progress == 1.0
    assert state.last_summary is final_summary
    assert state.is_running is False


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
