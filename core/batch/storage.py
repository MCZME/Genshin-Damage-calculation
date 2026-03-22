from __future__ import annotations

import json
import os
from dataclasses import asdict

from core.batch.models import (
    BatchNode,
    BatchNodeKind,
    BatchProject,
    MutationRule,
    RangeMutationConfig,
)


class BatchProjectStorage:
    """批处理项目存储。"""

    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = base_dir or os.path.join("data", "batch_projects")
        os.makedirs(self.base_dir, exist_ok=True)

    def list_projects(self) -> list[str]:
        return sorted(
            entry
            for entry in os.listdir(self.base_dir)
            if entry.endswith(".json")
        )

    def save(self, project: BatchProject, filename: str) -> str:
        if not filename.endswith(".json"):
            filename += ".json"
        path = os.path.join(self.base_dir, filename)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(self.to_dict(project), handle, ensure_ascii=False, indent=2)
        return path

    def load(self, filename: str) -> BatchProject:
        path = os.path.join(self.base_dir, filename)
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return self.from_dict(payload)

    def save_to_path(self, project: BatchProject, path: str) -> str:
        """保存项目到指定路径（支持任意位置）。"""
        parent_dir = os.path.dirname(path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(self.to_dict(project), handle, ensure_ascii=False, indent=2)
        return path

    def load_from_path(self, path: str) -> BatchProject:
        """从指定路径加载项目（支持任意位置）。"""
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return self.from_dict(payload)

    @classmethod
    def to_dict(cls, project: BatchProject) -> dict:
        return {
            "version": project.version,
            "name": project.name,
            "base_config": project.base_config,
            "root": cls._node_to_dict(project.root),
        }

    @classmethod
    def from_dict(cls, payload: dict) -> BatchProject:
        return BatchProject(
            version=int(payload.get("version", 1)),
            name=payload.get("name", "新批处理项目"),
            base_config=payload.get("base_config", {}),
            root=cls._node_from_dict(payload.get("root", {})),
        )

    @classmethod
    def _node_to_dict(cls, node: BatchNode) -> dict:
        data = {
            "id": node.id,
            "name": node.name,
            "kind": node.kind.value,
            "children": [cls._node_to_dict(child) for child in node.children],
            "generated_from_anchor_id": node.generated_from_anchor_id,
        }
        if node.rule:
            data["rule"] = asdict(node.rule)
        if node.range_config:
            data["range_config"] = asdict(node.range_config)
        return data

    @classmethod
    def _node_from_dict(cls, payload: dict) -> BatchNode:
        rule_payload = payload.get("rule")
        range_payload = payload.get("range_config")
        node = BatchNode(
            id=payload["id"],
            name=payload.get("name", ""),
            kind=BatchNodeKind(payload.get("kind", BatchNodeKind.RULE.value)),
            rule=MutationRule(**rule_payload) if rule_payload else None,
            range_config=RangeMutationConfig(**range_payload)
            if range_payload
            else None,
            generated_from_anchor_id=payload.get("generated_from_anchor_id"),
        )
        node.children = [
            cls._node_from_dict(child_payload)
            for child_payload in payload.get("children", [])
        ]
        return node
