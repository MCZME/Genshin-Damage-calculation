from __future__ import annotations

import copy
from typing import Any, Dict, List

from core.batch.models import (
    BatchCompileError,
    BatchNode,
    BatchNodeKind,
    BatchProject,
    BatchRunRequest,
)


class BatchProjectCompiler:
    """将批处理项目编译为可执行任务列表。"""

    @classmethod
    def compile(cls, project: BatchProject) -> List[BatchRunRequest]:
        requests: List[BatchRunRequest] = []
        base_config = copy.deepcopy(project.base_config)

        def walk(
            node: BatchNode,
            config_so_far: Dict[str, Any],
            snapshot_so_far: Dict[str, Any],
        ) -> None:
            current_config = copy.deepcopy(config_so_far)
            current_snapshot = dict(snapshot_so_far)

            if node.kind == BatchNodeKind.RULE and node.rule:
                cls._apply_rule(current_config, node.rule.target_path, node.rule.value)
                label = node.rule.label or ".".join(map(str, node.rule.target_path))
                current_snapshot[label] = node.rule.value

            if node.kind == BatchNodeKind.RANGE_ANCHOR and not node.children:
                return

            if not node.children:
                requests.append(
                    BatchRunRequest(
                        request_id=f"req_{node.id}",
                        node_id=node.id,
                        node_name=node.name,
                        config=current_config,
                        param_snapshot=current_snapshot,
                    )
                )
                return

            for child in node.children:
                walk(child, current_config, current_snapshot)

        walk(project.root, base_config, {})
        return requests

    @staticmethod
    def _apply_rule(config: Dict[str, Any], path: List[Any], value: Any) -> None:
        if not path:
            raise BatchCompileError("变异路径不能为空。")

        current: Any = config
        for key in path[:-1]:
            if isinstance(current, list):
                try:
                    current = current[int(key)]
                except (ValueError, IndexError) as exc:
                    raise BatchCompileError(f"无效列表索引: {key}") from exc
            else:
                if key not in current:
                    raise BatchCompileError(f"路径不存在: {'.'.join(map(str, path))}")
                current = current[key]

        last_key = path[-1]
        if isinstance(current, list):
            try:
                last_key = int(last_key)
                current[last_key] = copy.deepcopy(value)
            except (ValueError, IndexError) as exc:
                raise BatchCompileError(f"无效列表索引: {last_key}") from exc
            return

        if last_key not in current:
            raise BatchCompileError(f"路径不存在: {'.'.join(map(str, path))}")
        current[last_key] = copy.deepcopy(value)
