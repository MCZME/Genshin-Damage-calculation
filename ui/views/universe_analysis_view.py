from __future__ import annotations

import flet as ft

from ui.states.batch_analysis_state import BatchAnalysisState
from ui.theme import GenshinTheme

EDITOR_ROUTE = "/"
RUN_ROUTE = "/run"
ANALYSIS_ROUTE = "/analysis"


async def _push_route(page: ft.Page, route: str) -> None:
    await page.push_route(route)


def _route_btn(
    state: BatchAnalysisState, label: str, route: str, active: bool
) -> ft.Control:
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


class UniverseAnalysisView(ft.View):
    """批处理分析页面视图。"""

    def __init__(self, state: BatchAnalysisState, route: str = ANALYSIS_ROUTE) -> None:
        summary = state.last_summary

        if summary is None:
            result_block: ft.Control = ft.Container(
                padding=16,
                border_radius=16,
                bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
                border=ft.Border.all(
                    1, ft.Colors.with_opacity(0.12, ft.Colors.WHITE)
                ),
                content=ft.Text("暂无可分析数据，请先执行一次批处理。", size=14),
            )
        else:
            result_block = ft.Container(
                padding=16,
                border_radius=16,
                bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
                border=ft.Border.all(
                    1, ft.Colors.with_opacity(0.12, ft.Colors.WHITE)
                ),
                content=ft.Column(
                    [
                        ft.Text(
                            f"平均 DPS {int(summary.avg_dps)}  |  P95 {int(summary.p95_dps)}",
                            size=14,
                        ),
                        ft.Text(
                            f"最高 {int(summary.max_dps)}  |  最低 {int(summary.min_dps)}  |  标准差 {int(summary.std_dev_dps)}",
                            size=13,
                            color=GenshinTheme.TEXT_SECONDARY,
                        ),
                        ft.Divider(
                            height=14,
                            color=ft.Colors.with_opacity(0.12, ft.Colors.WHITE),
                        ),
                        ft.Text(
                            f"结果样本数: {len(summary.results)}",
                            size=13,
                            color=GenshinTheme.TEXT_SECONDARY,
                        ),
                        ft.Column(
                            [
                                ft.Text(
                                    f"{idx + 1}. {result.node_name} | DPS {int(result.dps)} | 伤害 {int(result.total_damage)}"
                                    + (
                                        f" | 错误: {result.error}"
                                        if result.error
                                        else ""
                                    ),
                                    size=12,
                                )
                                for idx, result in enumerate(summary.results[:20])
                            ],
                            spacing=6,
                            scroll=ft.ScrollMode.AUTO,
                            height=220,
                        ),
                    ],
                    spacing=8,
                ),
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
                                "批处理分析视图",
                                size=24,
                                weight=ft.FontWeight.W_800,
                            ),
                            ft.Row(
                                [
                                    _route_btn(state, "编辑", EDITOR_ROUTE, False),
                                    _route_btn(state, "运行", RUN_ROUTE, False),
                                    _route_btn(state, "分析", ANALYSIS_ROUTE, True),
                                ],
                                spacing=8,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    result_block,
                ],
                spacing=16,
                expand=True,
            ),
        )

        super().__init__(route=route, controls=[content])
