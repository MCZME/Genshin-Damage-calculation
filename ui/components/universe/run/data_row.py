from __future__ import annotations

from typing import TYPE_CHECKING
from collections.abc import Callable

import flet as ft

from core.batch.models import TaskRunState
from ui.theme import GenshinTheme

if TYPE_CHECKING:
    from ui.view_models.universe.run_task_vm import RunTaskViewModel


# 状态视觉配置
_STATE_CONFIG: dict[TaskRunState, dict] = {
    TaskRunState.PENDING: {
        "opacity": 0.6,
        "border_color": ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
        "icon": ft.Icons.SCHEDULE,
        "icon_color": GenshinTheme.TEXT_SECONDARY,
        "bg_gradient": ft.LinearGradient(
            begin=ft.Alignment.TOP_LEFT,
            end=ft.Alignment.BOTTOM_RIGHT,
            colors=[
                ft.Colors.with_opacity(0.3, "#282337"),
                ft.Colors.with_opacity(0.3, "#1E192D"),
            ],
        ),
        "accent_color": GenshinTheme.TEXT_SECONDARY,
    },
    TaskRunState.RUNNING: {
        "opacity": 1.0,
        "border_color": GenshinTheme.PRIMARY,
        "icon": ft.Icons.AUTORENEW,
        "icon_color": GenshinTheme.PRIMARY,
        "bg_gradient": ft.LinearGradient(
            begin=ft.Alignment.TOP_LEFT,
            end=ft.Alignment.BOTTOM_RIGHT,
            colors=[
                ft.Colors.with_opacity(0.4, "#503C78"),
                ft.Colors.with_opacity(0.4, "#322850"),
            ],
        ),
        "accent_color": GenshinTheme.PRIMARY,
        "glow": True,
    },
    TaskRunState.SUCCESS: {
        "opacity": 1.0,
        "border_color": GenshinTheme.GOLD_LIGHT,
        "icon": ft.Icons.CHECK_CIRCLE_OUTLINE,
        "icon_color": GenshinTheme.GOLD_LIGHT,
        "bg_gradient": ft.LinearGradient(
            begin=ft.Alignment.TOP_LEFT,
            end=ft.Alignment.BOTTOM_RIGHT,
            colors=[
                ft.Colors.with_opacity(0.4, "#3C3228"),
                ft.Colors.with_opacity(0.4, "#28231E"),
            ],
        ),
        "accent_color": GenshinTheme.GOLD_LIGHT,
    },
    TaskRunState.ERROR: {
        "opacity": 1.0,
        "border_color": ft.Colors.RED_400,
        "icon": ft.Icons.ERROR_OUTLINE,
        "icon_color": ft.Colors.RED_400,
        "bg_gradient": ft.LinearGradient(
            begin=ft.Alignment.TOP_LEFT,
            end=ft.Alignment.BOTTOM_RIGHT,
            colors=[
                ft.Colors.with_opacity(0.4, "#462828"),
                ft.Colors.with_opacity(0.4, "#321E1E"),
            ],
        ),
        "accent_color": ft.Colors.RED_400,
    },
}


@ft.component
def DataRow(
    vm: RunTaskViewModel,
    on_toggle_expand: Callable[[str], None] | None = None,
):
    """单个任务行组件。

    状态驱动视觉设计：
    - PENDING: 半透明，虚线图标，灰色边框
    - RUNNING: 发光边框，旋转图标，扫描动画
    - SUCCESS: 金色高亮，勾选图标
    - ERROR: 红色遮罩，警告图标，错误简述
    """
    config = _STATE_CONFIG[vm.state]

    # 状态图标（运行中状态通过颜色和发光边框区分）
    status_icon = ft.Icon(
        config["icon"],
        size=20,
        color=config["icon_color"],
    )

    # 主内容行
    main_row = ft.Row(
        [
            ft.Container(
                content=status_icon,
                width=32,
                alignment=ft.Alignment.CENTER,
            ),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            vm.node_name,
                            size=14,
                            weight=ft.FontWeight.W_600,
                            color=GenshinTheme.ON_SURFACE,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        _build_detail_row(vm),
                    ],
                    spacing=4,
                ),
                expand=True,
            ),
            _build_metrics(vm),
        ],
        spacing=12,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # 错误信息
    error_text = None
    if vm.state == TaskRunState.ERROR and vm.error:
        error_text = ft.Container(
            content=ft.Text(
                vm.error[:80] + ("..." if len(vm.error) > 80 else ""),
                size=11,
                color=ft.Colors.RED_300,
            ),
            padding=ft.Padding.only(left=44, top=4),
        )

    # 展开内容
    expanded_content = None
    if vm.is_expanded and vm.param_snapshot:
        expanded_content = ft.Container(
            content=_build_param_snapshot(vm.param_snapshot),
            padding=ft.Padding.only(left=44, top=8),
        )

    # 构建容器
    shadows = [
        ft.BoxShadow(
            blur_radius=10,
            spread_radius=0,
            color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK),
            offset=ft.Offset(0, 4),
        )
    ]
    if config.get("glow"):
        shadows.append(
            ft.BoxShadow(
                blur_radius=20,
                spread_radius=0,
                color=ft.Colors.with_opacity(0.3, GenshinTheme.PRIMARY),
                offset=ft.Offset(0, 0),
            )
        )

    return ft.Container(
        content=ft.Column(
            [c for c in [main_row, error_text, expanded_content] if c is not None],
            spacing=0,
        ),
        padding=ft.Padding.all(14),
        border_radius=12,
        gradient=config["bg_gradient"],
        border=ft.Border.all(1.5, config["border_color"]),
        shadow=shadows,
        opacity=config["opacity"],
        on_click=lambda _: on_toggle_expand(vm.request_id) if on_toggle_expand else None,
        animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
    )


def _build_detail_row(vm: RunTaskViewModel) -> ft.Control:
    """构建详情行。"""
    if vm.state == TaskRunState.PENDING:
        return ft.Text(
            "等待执行...",
            size=11,
            color=GenshinTheme.TEXT_SECONDARY,
        )
    elif vm.state == TaskRunState.RUNNING:
        return ft.Row(
            [
                ft.Container(
                    width=8,
                    height=8,
                    border_radius=4,
                    bgcolor=GenshinTheme.PRIMARY,
                    animate=ft.Animation(500),
                ),
                ft.Text(
                    "正在执行...",
                    size=11,
                    color=GenshinTheme.PRIMARY,
                ),
            ],
            spacing=6,
        )
    elif vm.state == TaskRunState.ERROR:
        return ft.Text(
            "执行失败",
            size=11,
            color=ft.Colors.RED_300,
        )
    else:  # SUCCESS
        return ft.Text(
            f"执行完成 · {vm.simulation_duration / 60:.1f}s",
            size=11,
            color=GenshinTheme.TEXT_SECONDARY,
        )


def _build_metrics(vm: RunTaskViewModel) -> ft.Control:
    """构建指标显示。"""
    if vm.state not in (TaskRunState.SUCCESS, TaskRunState.ERROR):
        return ft.Container()

    if vm.state == TaskRunState.ERROR:
        return ft.Container(
            content=ft.Text(
                "FAILED",
                size=10,
                weight=ft.FontWeight.W_700,
                color=ft.Colors.RED_400,
            ),
            padding=ft.Padding.symmetric(horizontal=8, vertical=4),
            border_radius=6,
            bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.RED_400),
        )

    return ft.Column(
        [
            ft.Text(
                f"{vm.dps:,.0f}",
                size=16,
                weight=ft.FontWeight.W_800,
                color=GenshinTheme.GOLD_LIGHT,
            ),
            ft.Text(
                "DPS",
                size=9,
                color=GenshinTheme.TEXT_SECONDARY,
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.END,
        spacing=0,
    )


def _build_param_snapshot(snapshot: dict) -> ft.Control:
    """构建参数快照展示。"""
    items: list[ft.Control] = []
    for key, value in snapshot.items():
        if len(items) >= 6:  # 最多显示6个参数
            break
        items.append(
            ft.Row(
                [
                    ft.Text(
                        str(key),
                        size=10,
                        color=GenshinTheme.TEXT_SECONDARY,
                    ),
                    ft.Text(
                        str(value)[:30],
                        size=10,
                        color=GenshinTheme.ON_SURFACE,
                    ),
                ],
                spacing=6,
            )
        )

    return ft.Container(
        content=ft.Column(
            [
                ft.Text(
                    "参数快照",
                    size=10,
                    weight=ft.FontWeight.W_600,
                    color=GenshinTheme.TEXT_SECONDARY,
                ),
                ft.Column(items, spacing=2),
            ],
            spacing=6,
        ),
        padding=ft.Padding.all(8),
        border_radius=8,
        bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.WHITE),
    )
