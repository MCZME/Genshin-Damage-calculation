from __future__ import annotations

from dataclasses import dataclass

import flet as ft

from core.batch.models import BatchNodeKind


@ft.observable
@dataclass
class NodeViewModel:
    id: str
    name: str
    kind: BatchNodeKind
    is_generated: bool = False
    children_count: int = 0
    rule_label: str = ""
    range_child_count: int = 0

    def set_name(self, name: str) -> None:
        self.name = name
