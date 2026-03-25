from core.batch.compiler import BatchProjectCompiler
from core.batch.models import (
    BatchCompileError,
    BatchNode,
    BatchNodeKind,
    BatchProject,
    MutationRule,
    RangeMutationConfig,
)


def _base_project() -> BatchProject:
    return BatchProject(
        name="test",
        base_config={
            "context_config": {
                "team": [{"character": {"level": 80, "constellation": 0}}],
                "environment": {"weather": "sunny"},
            }
        },
    )


def test_compile_root_only_generates_single_baseline_request():
    project = _base_project()

    requests = BatchProjectCompiler.compile(project)

    assert len(requests) == 1
    assert requests[0].config["context_config"]["team"][0]["character"]["level"] == 80


def test_compile_applies_parent_child_rules_in_order():
    project = _base_project()
    parent = BatchNode(
        id="node_1",
        name="level",
        kind=BatchNodeKind.RULE,
        rule=MutationRule(
            target_path=["context_config", "team", 0, "character", "level"],
            value=90,
            label="level=90",
        ),
    )
    child = BatchNode(
        id="node_2",
        name="constellation",
        kind=BatchNodeKind.RULE,
        rule=MutationRule(
            target_path=["context_config", "team", 0, "character", "constellation"],
            value=2,
            label="c2",
        ),
    )
    parent.children.append(child)
    project.root.children.append(parent)

    requests = BatchProjectCompiler.compile(project)

    assert len(requests) == 1
    config = requests[0].config
    assert config["context_config"]["team"][0]["character"]["level"] == 90
    assert config["context_config"]["team"][0]["character"]["constellation"] == 2
    assert requests[0].param_snapshot == {"level=90": 90, "c2": 2}


def test_compile_range_anchor_uses_generated_leaf_nodes():
    project = _base_project()
    anchor = BatchNode(
        id="anchor",
        name="range",
        kind=BatchNodeKind.RANGE_ANCHOR,
        range_config=RangeMutationConfig(
            target_path=["context_config", "team", 0, "character", "level"],
            start=80,
            end=90,
            step=10,
            label="等级",
        ),
    )
    anchor.children = [
        BatchNode(
            id="child_1",
            name="80",
            kind=BatchNodeKind.RULE,
            generated_from_anchor_id="anchor",
            rule=MutationRule(
                target_path=["context_config", "team", 0, "character", "level"],
                value=80,
                label="等级=80",
            ),
        ),
        BatchNode(
            id="child_2",
            name="90",
            kind=BatchNodeKind.RULE,
            generated_from_anchor_id="anchor",
            rule=MutationRule(
                target_path=["context_config", "team", 0, "character", "level"],
                value=90,
                label="等级=90",
            ),
        ),
    ]
    project.root.children.append(anchor)

    requests = BatchProjectCompiler.compile(project)

    assert [request.config["context_config"]["team"][0]["character"]["level"] for request in requests] == [80, 90]


def test_compile_invalid_path_raises_batch_compile_error():
    project = _base_project()
    project.root.children.append(
        BatchNode(
            id="bad",
            name="bad",
            kind=BatchNodeKind.RULE,
            rule=MutationRule(
                target_path=["context_config", "team", 3, "character", "level"],
                value=90,
                label="bad",
            ),
        )
    )

    try:
        BatchProjectCompiler.compile(project)
    except BatchCompileError as exc:
        assert "无效列表索引" in str(exc)
    else:
        raise AssertionError("expected BatchCompileError")
