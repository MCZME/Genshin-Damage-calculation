from __future__ import annotations

from dataclasses import dataclass, field

from core.batch.models import BatchNode
from ui.view_models.universe.node_vm import NodeViewModel


@dataclass
class MindMapCanvasData:
    root: BatchNode
    selected_node_id: str
    node_index: dict[str, NodeViewModel] = field(default_factory=dict)
    x_gap: int = 300
    y_gap: int = 170
    base_x: int = 320
    base_y: int = 140
