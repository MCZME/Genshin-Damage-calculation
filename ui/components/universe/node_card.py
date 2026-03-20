from __future__ import annotations

import flet as ft

from core.batch.models import BatchNodeKind
from ui.theme import GenshinTheme
from ui.view_models.universe.node_vm import NodeViewModel


@ft.component
def NodeCard(vm: NodeViewModel, is_selected: bool, on_select, on_add_rule):
    palette = {
        BatchNodeKind.ROOT: {
            "accent": GenshinTheme.GOLD_LIGHT,
            "label": "BASE",
        },
        BatchNodeKind.RULE: {
            "accent": GenshinTheme.PRIMARY,
            "label": "RULE",
        },
        BatchNodeKind.RANGE_ANCHOR: {
            "accent": "#6AB3FF",
            "label": "RANGE",
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

    return ft.Container(
        width=220,
        padding=16,
        border_radius=22,
        bgcolor="#2A2439" if is_selected else "#221D30",
        border=ft.border.all(
            2 if is_selected else 1,
            palette["accent"] if is_selected else "rgba(255,255,255,0.08)",
        ),
        shadow=ft.BoxShadow(
            blur_radius=12 if is_selected else 6,
            spread_radius=0,
            color="rgba(0,0,0,0.30)",
        ),
        on_click=on_select,
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Text(
                                palette["label"],
                                size=9,
                                weight=ft.FontWeight.BOLD,
                                color=GenshinTheme.ON_PRIMARY,
                            ),
                            bgcolor=palette["accent"],
                            padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                            border_radius=10,
                        ),
                        ft.IconButton(
                            ft.Icons.ADD_CIRCLE_OUTLINE,
                            tooltip="添加规则子节点",
                            icon_color=palette["accent"],
                            icon_size=18,
                            on_click=on_add_rule,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(
                    height=3,
                    border_radius=999,
                    bgcolor=palette["accent"],
                    opacity=0.95 if is_selected else 0.7,
                ),
                ft.Text(
                    vm.name,
                    size=15,
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
                        ft.Text(
                            f"子节点 {vm.children_count}",
                            size=10,
                            color=palette["accent"],
                        ),
                        ft.Text(
                            "SELECTED" if is_selected else "",
                            size=10,
                            color=palette["accent"],
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            ],
            spacing=10,
        ),
    )
