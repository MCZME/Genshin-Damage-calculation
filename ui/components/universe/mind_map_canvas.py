from __future__ import annotations

import flet as ft
import flet.canvas as cv

from core.batch.models import BatchNode
from ui.components.universe.node_card import NodeCard
from ui.view_models.universe.mind_map_canvas_data import MindMapCanvasData


@ft.component
def MindMapCanvas(data: MindMapCanvasData, on_select, on_add_rule, on_deselect=None):
    root = data.root
    positions: dict[str, tuple[float, float]] = {}
    spans: dict[str, int] = {}

    def measure(node: BatchNode) -> int:
        if node.id in spans:
            return spans[node.id]
        if not node.children:
            spans[node.id] = 1
            return 1
        spans[node.id] = max(1, sum(measure(child) for child in node.children))
        return spans[node.id]

    def place(node: BatchNode, depth: int, leaf_offset: int) -> None:
        span = spans[node.id]
        center_index = leaf_offset + (span - 1) / 2
        positions[node.id] = (
            data.base_x + depth * data.x_gap,
            data.base_y + center_index * data.y_gap,
        )

        next_offset = leaf_offset
        for child in node.children:
            child_span = spans[child.id]
            place(child, depth + 1, next_offset)
            next_offset += child_span

    measure(root)
    place(root, 0, 0)

    width = 2200
    height = max(1200, 360 + max(y for _, y in positions.values()))

    line_shapes: list[cv.Shape] = []
    node_controls: list[ft.Control] = []

    def walk(node: BatchNode) -> None:
        x, y = positions[node.id]
        vm = data.node_index.get(node.id)
        if vm is None:
            return
        node_controls.append(
            ft.Container(
                left=x,
                top=y,
                content=NodeCard(
                    vm=vm,
                    is_selected=node.id == data.selected_node_id,
                    on_select=lambda _, node_id=node.id: on_select(node_id),
                    on_add_rule=lambda _, node_id=node.id: on_add_rule(node_id),
                ),
            )
        )

        for child in node.children:
            child_x, child_y = positions[child.id]
            line_shapes.append(
                cv.Path(
                    [
                        cv.Path.MoveTo(x + 220, y + 46),
                        cv.Path.CubicTo(
                            x + 270,
                            y + 46,
                            child_x - 60,
                            child_y + 46,
                            child_x,
                            child_y + 46,
                        ),
                    ],
                    paint=ft.Paint(
                        color="rgba(209,162,255,0.72)",
                        style=ft.PaintingStyle.STROKE,
                        stroke_width=2.6,
                    ),
                )
            )
            walk(child)

    walk(root)

    mind_map = ft.Stack(
        [
            cv.Canvas(shapes=line_shapes, width=width, height=height),
            ft.Stack(
                controls=node_controls,
                width=width,
                height=height,
                clip_behavior=ft.ClipBehavior.NONE,
            ),
        ],
        width=width,
        height=height,
        clip_behavior=ft.ClipBehavior.NONE,
    )

    viewer = ft.InteractiveViewer(
        content=mind_map,
        min_scale=0.45,
        max_scale=1.8,
        boundary_margin=ft.Margin(600, 400, 600, 400),
        clip_behavior=ft.ClipBehavior.NONE,
        expand=True,
    )

    if on_deselect is None:
        return viewer

    return ft.GestureDetector(
        content=viewer,
        expand=True,
        on_tap=lambda _: on_deselect(),
    )
