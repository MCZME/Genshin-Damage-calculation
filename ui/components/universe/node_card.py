from __future__ import annotations

import flet as ft

from core.batch.models import BatchNodeKind
from ui.theme import GenshinTheme
from ui.view_models.universe.node_vm import NodeViewModel


@ft.component
def NodeCard(vm: NodeViewModel, is_selected: bool, on_select, on_open_add_drawer):
    palette = {
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
    }[vm.kind]

    detail = (
        "根配置"
        if vm.kind == BatchNodeKind.ROOT
        else (
            vm.rule_label
            if vm.rule_label
            else (
                f"{vm.range_child_count} 个区间子节点"
                if vm.kind == BatchNodeKind.RANGE_ANCHOR
                else "尚未配置规则"
            )
        )
    )

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
            palette["accent"] if is_selected else ft.Colors.with_opacity(0.08, ft.Colors.WHITE),
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
                                        palette["icon"],
                                        size=12,
                                        color=GenshinTheme.ON_PRIMARY,
                                    ),
                                    width=22,
                                    height=22,
                                    alignment=ft.Alignment.CENTER,
                                    border_radius=999,
                                    bgcolor=palette["accent"],
                                ),
                                ft.Container(
                                    content=ft.Text(
                                        palette["label"],
                                        size=9,
                                        weight=ft.FontWeight.W_800,
                                        color=GenshinTheme.ON_PRIMARY,
                                    ),
                                    bgcolor=palette["accent"],
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
                                icon_color=palette["accent"],
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
                            palette["accent"],
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
                ft.Text(
                    detail,
                    size=11,
                    color=GenshinTheme.TEXT_SECONDARY,
                    max_lines=2,
                ),
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Text(
                                f"子节点 {vm.children_count}",
                                size=10,
                                color=palette["accent"],
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
                                color=palette["accent"] if is_selected else GenshinTheme.TEXT_SECONDARY,
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
