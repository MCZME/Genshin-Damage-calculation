from __future__ import annotations

import flet as ft

from ui.states.batch_run_state import BatchRunState
from ui.theme import GenshinTheme

EDITOR_ROUTE = "/"
RUN_ROUTE = "/run"
ANALYSIS_ROUTE = "/analysis"


async def _push_route(page: ft.Page, route: str) -> None:
    await page.push_route(route)


def _route_btn(state: BatchRunState, label: str, route: str, active: bool) -> ft.Control:
    return ft.OutlinedButton(
        content=ft.Text(label),
        disabled=active,
        on_click=lambda _: state.page.run_task(_push_route, state.page, route),
        style=ft.ButtonStyle(
            bgcolor=(
                ft.Colors.with_opacity(0.2, GenshinTheme.PRIMARY)
                if active
                else ft.Colors.with_opacity(0.04, ft.Colors.WHITE)
            ),
            side=ft.BorderSide(
                1.2,
                (
                    ft.Colors.with_opacity(0.7, GenshinTheme.PRIMARY)
                    if active
                    else ft.Colors.with_opacity(0.2, ft.Colors.WHITE)
                ),
            ),
        ),
    )


class UniverseRunView(ft.View):
    """批处理运行页面视图。"""

    def __init__(self, state: BatchRunState, route: str = RUN_ROUTE) -> None:
        summary = state.last_summary
        progress = max(0.0, min(1.0, state.progress))

        metric_row = ft.Row(
            [
                ft.Container(
                    content=ft.Text(
                        f"总任务: {summary.total_runs if summary else '-'}",
                        size=13,
                        color=GenshinTheme.TEXT_SECONDARY,
                    ),
                    padding=ft.Padding.symmetric(horizontal=12, vertical=8),
                    border_radius=999,
                    bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.WHITE),
                ),
                ft.Container(
                    content=ft.Text(
                        f"成功: {summary.completed_runs if summary else '-'}",
                        size=13,
                        color=GenshinTheme.TEXT_SECONDARY,
                    ),
                    padding=ft.Padding.symmetric(horizontal=12, vertical=8),
                    border_radius=999,
                    bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.WHITE),
                ),
                ft.Container(
                    content=ft.Text(
                        f"失败: {summary.failed_runs if summary else '-'}",
                        size=13,
                        color=GenshinTheme.TEXT_SECONDARY,
                    ),
                    padding=ft.Padding.symmetric(horizontal=12, vertical=8),
                    border_radius=999,
                    bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.WHITE),
                ),
            ],
            spacing=10,
            wrap=True,
        )

        content = ft.Container(
            expand=True,
            bgcolor=GenshinTheme.BACKGROUND,
            padding=24,
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(
                                "批处理运行视图",
                                size=24,
                                weight=ft.FontWeight.W_800,
                            ),
                            ft.Row(
                                [
                                    _route_btn(state, "编辑", EDITOR_ROUTE, False),
                                    _route_btn(state, "运行", RUN_ROUTE, True),
                                    _route_btn(state, "分析", ANALYSIS_ROUTE, False),
                                ],
                                spacing=8,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Container(
                        padding=16,
                        border_radius=16,
                        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
                        border=ft.Border.all(
                            1, ft.Colors.with_opacity(0.12, ft.Colors.WHITE)
                        ),
                        content=ft.Column(
                            [
                                ft.Text(state.status_text, size=14),
                                ft.ProgressBar(value=progress, height=8),
                                ft.Text(
                                    f"当前进度: {int(progress * 100)}%",
                                    size=12,
                                    color=GenshinTheme.TEXT_SECONDARY,
                                ),
                                metric_row,
                            ],
                            spacing=12,
                        ),
                    ),
                    ft.Container(
                        padding=16,
                        border_radius=16,
                        bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.WHITE),
                        border=ft.Border.all(
                            1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE)
                        ),
                        content=ft.Text(
                            state.error_message or "暂无运行错误。",
                            color=(
                                ft.Colors.RED_200
                                if state.error_message
                                else GenshinTheme.TEXT_SECONDARY
                            ),
                        ),
                    ),
                ],
                spacing=16,
                expand=True,
            ),
        )

        super().__init__(route=route, controls=[content])
