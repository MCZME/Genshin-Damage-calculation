from __future__ import annotations

import flet as ft

from ui.components.universe.run.action_drawer import ActionDrawer
from ui.components.universe.run.command_ribbon import CommandRibbon
from ui.components.universe.run.data_grid import DataGrid
from ui.states.batch_run_state import BatchRunState
from ui.theme import GenshinTheme

EDITOR_ROUTE = "/"
RUN_ROUTE = "/run"
ANALYSIS_ROUTE = "/analysis"


async def _push_route(page: ft.Page, route: str) -> None:
    await page.push_route(route)


def _route_btn(
    state: BatchRunState, label: str, route: str, active: bool
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


class UniverseRunView(ft.View):
    """批处理运行页面视图。

    采用纵向层叠布局：
    - CommandRibbon: 顶部悬浮命令栏
    - DataGrid: 主体数据展示区域
    - ActionDrawer: 底部交互层
    """

    def __init__(self, state: BatchRunState, route: str = RUN_ROUTE) -> None:
        self._state = state

        # 获取项目名称（从编辑器状态）
        project_name = "批处理项目"  # 默认值

        # 构建内容
        content = ft.Container(
            expand=True,
            bgcolor=GenshinTheme.BACKGROUND,
            content=ft.Stack(
                [
                    # 主体区域
                    ft.Column(
                        [
                            # 顶部导航栏
                            ft.Container(
                                content=ft.Row(
                                    [
                                        ft.Row(
                                            [
                                                ft.Icon(
                                                    ft.Icons.PLAY_ARROW_ROUNDED,
                                                    size=20,
                                                    color=GenshinTheme.PRIMARY,
                                                ),
                                                ft.Text(
                                                    "批处理执行",
                                                    size=20,
                                                    weight=ft.FontWeight.W_800,
                                                    color=GenshinTheme.ON_SURFACE,
                                                ),
                                            ],
                                            spacing=8,
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
                                padding=ft.Padding.symmetric(horizontal=20, vertical=12),
                            ),
                            # Command Ribbon
                            ft.Container(
                                content=CommandRibbon(state, project_name),
                                padding=ft.Padding.symmetric(horizontal=20),
                            ),
                            # Data Grid
                            DataGrid(state, self._on_toggle_expand),
                        ],
                        spacing=12,
                        expand=True,
                    ),
                    # Action Drawer
                    ActionDrawer(
                        state,
                        on_stop=self._on_stop,
                        on_back=self._on_back,
                        on_analysis=self._on_analysis,
                    ),
                ],
                expand=True,
            ),
        )

        super().__init__(route=route, controls=[content])

    def _on_toggle_expand(self, request_id: str) -> None:
        """切换任务展开状态。"""
        if request_id in self._state.tasks:
            self._state.tasks[request_id].toggle_expanded()

    def _on_stop(self) -> None:
        """停止执行。"""
        # TODO: 实现停止逻辑
        pass

    def _on_back(self) -> None:
        """返回编辑器。"""
        if self._state.page:
            self._state.page.run_task(_push_route, self._state.page, EDITOR_ROUTE)

    def _on_analysis(self) -> None:
        """查看分析。"""
        if self._state.page:
            self._state.page.run_task(_push_route, self._state.page, ANALYSIS_ROUTE)
