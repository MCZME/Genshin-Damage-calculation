from __future__ import annotations

import flet as ft

from core.batch.models import BatchNodeKind
from ui.theme import GenshinTheme
from ui.view_models.universe.node_vm import NodeViewModel


from typing import Any, Callable

@ft.component
def NodeCard(
    vm: NodeViewModel,
    is_selected: bool,
    on_select: Callable[[Any], Any],
    on_open_add_drawer: Callable[[Any], Any],
):
    _node_palettes: dict[BatchNodeKind, dict[str, Any]] = {
        BatchNodeKind.ROOT: {
            "accent": GenshinTheme.GOLD_LIGHT,
            "label": "BASE",
            "icon": ft.Icons.HUB,
        },
        BatchNodeKind.RULE: {
            "accent": GenshinTheme.PRIMARY,
            "label": "RULE",
            "icon": ft.Icons.TUNE,
        },
        BatchNodeKind.RANGE_ANCHOR: {
            "accent": "#6AB3FF",
            "label": "RANGE",
            "icon": ft.Icons.MULTILINE_CHART,
        },
    }
    
    current_palette = _node_palettes[vm.kind]
    accent_color: str = current_palette["accent"]
    label_text: str = current_palette["label"]
    icon_data: ft.IconData = current_palette["icon"]

    # 构建详情行
    detail_lines: list[str] = []
    if vm.kind == BatchNodeKind.ROOT:
        detail_lines = ["根配置"]
    elif vm.kind == BatchNodeKind.RULE:
        if vm.target_path:
            detail_lines.append(f"路径: {vm.target_path}")
        if vm.value_text:
            detail_lines.append(f"值: {vm.value_text}")
        if not detail_lines:
            detail_lines.append("尚未配置规则")
    else:  # RANGE_ANCHOR
        if vm.target_path:
            detail_lines.append(f"路径: {vm.target_path}")
        if vm.range_info:
            detail_lines.append(f"区间: {vm.range_info}")
        detail_lines.append(f"生成 {vm.range_child_count} 个子节点")

    glow_color = {
        BatchNodeKind.ROOT: ft.Colors.with_opacity(0.28, GenshinTheme.GOLD_LIGHT),
        BatchNodeKind.RULE: ft.Colors.with_opacity(0.28, GenshinTheme.PRIMARY),
        BatchNodeKind.RANGE_ANCHOR: ft.Colors.with_opacity(0.28, "#6AB3FF"),
    }[vm.kind]
    
    bg_gradient = (
        ft.LinearGradient(
            begin=ft.Alignment.TOP_LEFT,
            end=ft.Alignment.BOTTOM_RIGHT,
            colors=["#2E2642", "#231D34"],
        )
        if is_selected
        else ft.LinearGradient(
            begin=ft.Alignment.TOP_LEFT,
            end=ft.Alignment.BOTTOM_RIGHT,
            colors=["#251F35", "#1D192B"],
        )
    )

    return ft.Container(
        width=236,
        padding=18,
        border_radius=24,
        gradient=bg_gradient,
        border=ft.Border.all(
            2 if is_selected else 1,
            accent_color if is_selected else ft.Colors.with_opacity(0.08, ft.Colors.WHITE),
        ),
        shadow=[
            ft.BoxShadow(
                blur_radius=22 if is_selected else 10,
                spread_radius=1 if is_selected else 0,
                color=ft.Colors.with_opacity(0.32, ft.Colors.BLACK),
                offset=ft.Offset(0, 8),
            ),
            ft.BoxShadow(
                blur_radius=20 if is_selected else 0,
                spread_radius=0,
                color=glow_color if is_selected else ft.Colors.TRANSPARENT,
                offset=ft.Offset(0, 0),
            ),
        ],
        on_click=on_select,
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Row(
                            [
                                ft.Container(
                                    content=ft.Icon(
                                        icon_data,
                                        size=12,
                                        color=GenshinTheme.ON_PRIMARY,
                                    ),
                                    width=22,
                                    height=22,
                                    alignment=ft.Alignment.CENTER,
                                    border_radius=999,
                                    bgcolor=accent_color,
                                ),
                                ft.Container(
                                    content=ft.Text(
                                        label_text,
                                        size=9,
                                        weight=ft.FontWeight.W_800,
                                        color=GenshinTheme.ON_PRIMARY,
                                    ),
                                    bgcolor=accent_color,
                                    padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                                    border_radius=10,
                                ),
                                ft.Container(
                                    content=ft.Text(
                                        "AUTO" if vm.is_generated else "EDIT",
                                        size=8,
                                        color=GenshinTheme.TEXT_SECONDARY,
                                        weight=ft.FontWeight.W_700,
                                    ),
                                    padding=ft.Padding.symmetric(horizontal=7, vertical=3),
                                    border_radius=999,
                                    bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
                                    border=ft.Border.all(
                                        1, ft.Colors.with_opacity(0.08, ft.Colors.WHITE)
                                    ),
                                ),
                            ],
                            spacing=6,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            wrap=True,
                        ),
                        ft.Container(
                            content=ft.IconButton(
                                ft.Icons.ADD,
                                tooltip="添加子节点",
                                icon_color=accent_color,
                                icon_size=16,
                                style=ft.ButtonStyle(
                                    bgcolor={
                                        ft.ControlState.DEFAULT: ft.Colors.with_opacity(
                                            0.02, ft.Colors.WHITE
                                        ),
                                        ft.ControlState.HOVERED: ft.Colors.with_opacity(
                                            0.08, ft.Colors.WHITE
                                        ),
                                    },
                                    shape=ft.RoundedRectangleBorder(radius=10),
                                    side=ft.BorderSide(
                                        width=1,
                                        color=ft.Colors.with_opacity(0.08, ft.Colors.WHITE),
                                    ),
                                    padding=8,
                                ),
                                on_click=on_open_add_drawer,
                            ),
                            border_radius=12,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
                ft.Container(
                    height=4,
                    border_radius=999,
                    gradient=ft.LinearGradient(
                        begin=ft.Alignment(-1, 0),
                        end=ft.Alignment(1, 0),
                        colors=[
                            ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
                            accent_color,
                            ft.Colors.with_opacity(0.06, ft.Colors.WHITE),
                        ],
                    ),
                    opacity=1 if is_selected else 0.78,
                ),
                ft.Text(
                    vm.name,
                    size=16,
                    weight=ft.FontWeight.W_900,
                    color=GenshinTheme.ON_SURFACE,
                    max_lines=2,
                ),
                ft.Column(
                    [
                        ft.Text(
                            line,
                            size=11,
                            color=GenshinTheme.TEXT_SECONDARY,
                        )
                        for line in detail_lines
                    ],
                    spacing=4,
                ),
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Text(
                                f"子节点 {vm.children_count}",
                                size=10,
                                color=accent_color,
                                weight=ft.FontWeight.W_700,
                            ),
                            padding=ft.Padding.symmetric(horizontal=8, vertical=5),
                            border_radius=999,
                            bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.WHITE),
                            border=ft.Border.all(
                                1, ft.Colors.with_opacity(0.08, ft.Colors.WHITE)
                            ),
                        ),
                        ft.Container(
                            content=ft.Text(
                                "SELECTED" if is_selected else "READY",
                                size=9,
                                color=accent_color if is_selected else GenshinTheme.TEXT_SECONDARY,
                                weight=ft.FontWeight.W_700,
                            ),
                            padding=ft.Padding.symmetric(horizontal=8, vertical=5),
                            border_radius=999,
                            bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.WHITE),
                            border=ft.Border.all(
                                1,
                                glow_color
                                if is_selected
                                else ft.Colors.with_opacity(0.08, ft.Colors.WHITE),
                            ),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            ],
            spacing=10,
        ),
    )
