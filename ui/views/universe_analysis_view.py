from __future__ import annotations

import flet as ft

from core.batch.models import BatchRunSummary
from ui.components.universe.analysis_kpi import BatchAnalysisKPICard
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


def _build_kpi_row(summary: BatchRunSummary) -> ft.Control:
    """构建 KPI 卡片行。"""
    return ft.Row(
        [
            BatchAnalysisKPICard(
                icon=ft.Icons.SPEED,
                label="平均 DPS",
                value=f"{int(summary.avg_dps):,}",
                accent_color=GenshinTheme.PRIMARY,
            ),
            BatchAnalysisKPICard(
                icon=ft.Icons.TRENDING_UP,
                label="P95 DPS",
                value=f"{int(summary.p95_dps):,}",
                accent_color=GenshinTheme.GOLD_LIGHT,
            ),
            BatchAnalysisKPICard(
                icon=ft.Icons.ARROW_UPWARD,
                label="最高 DPS",
                value=f"{int(summary.max_dps):,}",
                accent_color="#6AB3FF",
            ),
            BatchAnalysisKPICard(
                icon=ft.Icons.ARROW_DOWNWARD,
                label="最低 DPS",
                value=f"{int(summary.min_dps):,}",
                accent_color="#FF6B9D",
            ),
        ],
        spacing=12
    )


def _build_results_table(summary: BatchRunSummary) -> ft.Control:
    """构建结果数据表格。"""
    rows: list[ft.DataRow] = []
    for result in summary.results[:50]:
        status_icon = ft.Icon(
            ft.Icons.CHECK_CIRCLE_OUTLINE,
            color="#4CAF50",
            size=18,
        ) if not result.error else ft.Icon(
            ft.Icons.ERROR_OUTLINE,
            color="#FF6B6B",
            size=18,
        )

        rows.append(
            ft.DataRow(
                cells=[
                    ft.DataCell(status_icon),
                    ft.DataCell(ft.Text(result.node_name, size=13)),
                    ft.DataCell(ft.Text(f"{int(result.dps):,}", size=13)),
                    ft.DataCell(ft.Text(f"{int(result.total_damage):,}", size=13)),
                    ft.DataCell(
                        ft.Text(
                            f"{result.simulation_duration}ms" if result.simulation_duration else "-",
                            size=13,
                            color=GenshinTheme.TEXT_SECONDARY,
                        )
                    ),
                ]
            )
        )

    return ft.Container(
        padding=16,
        border_radius=16,
        bgcolor=GenshinTheme.GLASS_BG,
        border=ft.Border.all(1.2, GenshinTheme.GLASS_BORDER),
        content=ft.Column(
            [
                ft.Text(
                    "运行结果明细",
                    size=14,
                    weight=ft.FontWeight.W_700,
                    color=GenshinTheme.ON_SURFACE,
                ),
                ft.Divider(height=12, color=ft.Colors.with_opacity(0.08, ft.Colors.WHITE)),
                ft.ListView(
                    controls=[
                        ft.DataTable(
                            columns=[
                                ft.DataColumn(label=ft.Text("状态", size=12, color=GenshinTheme.TEXT_SECONDARY)),
                                ft.DataColumn(label=ft.Text("配置名称", size=12, color=GenshinTheme.TEXT_SECONDARY)),
                                ft.DataColumn(label=ft.Text("DPS", size=12, color=GenshinTheme.TEXT_SECONDARY)),
                                ft.DataColumn(label=ft.Text("总伤害", size=12, color=GenshinTheme.TEXT_SECONDARY)),
                                ft.DataColumn(label=ft.Text("耗时", size=12, color=GenshinTheme.TEXT_SECONDARY)),
                            ],
                            rows=rows,
                            border=ft.Border.all(0, ft.Colors.TRANSPARENT),
                            heading_row_color=ft.Colors.TRANSPARENT,
                            data_row_color=ft.Colors.TRANSPARENT,
                            data_row_min_height=36,
                            data_row_max_height=36,
                        )
                    ],
                    height=320,
                    expand=True,
                ),
            ],
            spacing=8,
        ),
    )


def _build_empty_state() -> ft.Control:
    """构建空状态占位。"""
    return ft.Container(
        padding=24,
        border_radius=16,
        bgcolor=GenshinTheme.GLASS_BG,
        border=ft.Border.all(1.2, GenshinTheme.GLASS_BORDER),
        alignment=ft.Alignment.CENTER,
        content=ft.Column(
            [
                ft.Icon(ft.Icons.ANALYTICS_OUTLINED, size=48, color=GenshinTheme.TEXT_SECONDARY),
                ft.Text(
                    "暂无可分析数据",
                    size=16,
                    weight=ft.FontWeight.W_600,
                    color=GenshinTheme.ON_SURFACE,
                ),
                ft.Text(
                    "请先执行一次批处理以生成分析数据",
                    size=13,
                    color=GenshinTheme.TEXT_SECONDARY,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        ),
    )


class UniverseAnalysisView(ft.View):
    """批处理分析页面视图。"""

    def __init__(self, state: BatchAnalysisState, route: str = ANALYSIS_ROUTE) -> None:
        summary = state.last_summary

        if summary is None:
            result_block: ft.Control = _build_empty_state()
        else:
            result_block = ft.Column(
                [
                    _build_kpi_row(summary),
                    _build_results_table(summary),
                ],
                spacing=16,
            )

        header = ft.Container(
            content=ft.Row(
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
            bgcolor=GenshinTheme.BACKGROUND,
            padding=ft.Padding(24, 24, 24, 12),
        )

        scroll_content = ft.Container(
            bgcolor=GenshinTheme.BACKGROUND,
            padding=ft.Padding(24, 0, 24, 24),
            content=result_block,
        )

        content = ft.Container(
            expand=True,
            bgcolor=GenshinTheme.BACKGROUND,
            content=ft.Column(
                [
                    header,
                    ft.ListView(
                        controls=[scroll_content],
                        expand=True,
                        padding=0,
                    ),
                ],
                spacing=0,
                expand=True,
            ),
        )

        super().__init__(route=route, controls=[content])
