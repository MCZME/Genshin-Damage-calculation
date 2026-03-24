from __future__ import annotations

from typing import TYPE_CHECKING
from collections.abc import Callable

import flet as ft

from ui.components.universe.run.data_row import DataRow

if TYPE_CHECKING:
    from ui.states.batch_run_state import BatchRunState


@ft.component
def DataGrid(
    state: BatchRunState,
    on_toggle_expand: Callable[[str], None] | None = None,
):
    """数据网格组件。

    主体区域，100% 宽度显示所有任务行。
    使用 ListView 实现虚拟滚动。
    """
    if not state.task_order:
        return ft.Container(
            content=ft.Column(
                [
                    ft.Icon(
                        ft.Icons.INBOX_OUTLINED,
                        size=48,
                        color=ft.Colors.with_opacity(0.3, ft.Colors.WHITE),
                    ),
                    ft.Text(
                        "暂无任务",
                        size=16,
                        color=ft.Colors.with_opacity(0.5, ft.Colors.WHITE),
                    ),
                    ft.Text(
                        "请在编辑器中配置批处理任务后执行",
                        size=12,
                        color=ft.Colors.with_opacity(0.3, ft.Colors.WHITE),
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
            ),
            alignment=ft.Alignment.CENTER,
            expand=True,
        )

    rows: list[ft.Control] = []
    for request_id in state.task_order:
        vm = state.tasks.get(request_id)
        if vm:
            rows.append(DataRow(vm, on_toggle_expand))

    return ft.ListView(
        rows,
        spacing=8,
        padding=ft.Padding.symmetric(horizontal=20, vertical=8),
        expand=True,
    )
