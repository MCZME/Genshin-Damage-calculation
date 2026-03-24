from __future__ import annotations

import flet as ft

from core.batch.models import BatchNodeKind, BatchRunSummary
from ui.components.universe.node_add_drawer import NodeAddDrawer
from ui.components.universe.path_selector_drawer import PathSelectorDrawer
from ui.components.universe.range_anchor_form import RangeAnchorForm
from ui.theme import GenshinTheme
from ui.view_models.universe.node_inspector_panel_vm import NodeInspectorPanelViewModel


@ft.component
def NodeInspectorPanel(
    vm: NodeInspectorPanelViewModel,
    on_rename,
    on_add_node,
    on_delete,
    on_apply_rule,
    on_apply_range,
    last_summary: BatchRunSummary | None = None,
) -> ft.Control:
    drawer_open, set_drawer_open = ft.use_state(False)
    path_selector_open, set_path_selector_open = ft.use_state(False)
    rule_path, set_rule_path = ft.use_state(vm.rule_path_text)
    rule_value, set_rule_value = ft.use_state(vm.rule_value_text)

    range_path, set_range_path = ft.use_state(vm.range_path_text)
    range_type, set_range_type = ft.use_state(vm.range_type.value)
    range_start, set_range_start = ft.use_state(vm.range_start_text)
    range_end, set_range_end = ft.use_state(vm.range_end_text)
    range_step, set_range_step = ft.use_state(vm.range_step_text)
    range_values, set_range_values = ft.use_state(vm.range_values_text)
    range_label, set_range_label = ft.use_state(vm.range_label_text)

    def sync_inputs() -> None:
        set_rule_path(vm.rule_path_text)
        set_rule_value(vm.rule_value_text)
        set_range_path(vm.range_path_text)
        set_range_type(vm.range_type.value)
        set_range_start(vm.range_start_text)
        set_range_end(vm.range_end_text)
        set_range_step(vm.range_step_text)
        set_range_values(vm.range_values_text)
        set_range_label(vm.range_label_text)
        set_drawer_open(False)

    ft.use_effect(sync_inputs, [vm.node_id])

    kind_palette = {
        BatchNodeKind.ROOT: {"accent": GenshinTheme.GOLD_LIGHT, "label": "BASE"},
        BatchNodeKind.RULE: {"accent": GenshinTheme.PRIMARY, "label": "RULE"},
        BatchNodeKind.RANGE_ANCHOR: {"accent": "#6AB3FF", "label": "RANGE"},
    }[vm.node_kind]

    def soft_card(content: ft.Control, padding: int = 16) -> ft.Container:
        return ft.Container(
            content=content,
            padding=padding,
            border_radius=16,
            bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.WHITE),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.08, ft.Colors.WHITE)),
        )

    def styled_text_field(
        *,
        label: str,
        value: str,
        on_change,
        hint_text: str | None = None,
        dense: bool = False,
        text_size: int = 15,
        text_style: ft.TextStyle | None = None,
        expand: bool = False,
    ) -> ft.TextField:
        return ft.TextField(
            label=label,
            value=value,
            on_change=on_change,
            hint_text=hint_text,
            dense=dense,
            text_size=text_size,
            text_style=text_style,
            label_style=ft.TextStyle(
                size=12,
                color=ft.Colors.with_opacity(0.78, GenshinTheme.TEXT_SECONDARY),
            ),
            hint_style=ft.TextStyle(
                size=max(12, text_size - 2),
                color=ft.Colors.with_opacity(0.50, GenshinTheme.TEXT_SECONDARY),
            ),
            bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.WHITE),
            border=ft.InputBorder.OUTLINE,
            border_radius=14,
            border_width=1.2,
            border_color=ft.Colors.with_opacity(0.14, ft.Colors.WHITE),
            focused_border_width=1.8,
            focused_border_color=ft.Colors.with_opacity(0.65, kind_palette["accent"]),
            content_padding=ft.Padding.symmetric(horizontal=14, vertical=12),
            cursor_color=kind_palette["accent"],
            selection_color=ft.Colors.with_opacity(0.25, kind_palette["accent"]),
            expand=expand,
        )

    hero = ft.Container(
        padding=18,
        border_radius=18,
        gradient=ft.LinearGradient(
            begin=ft.Alignment(-1, -1),
            end=ft.Alignment(1, 1),
            colors=["#2F2943", "#231F33"],
        ),
        border=ft.Border.all(1, ft.Colors.with_opacity(0.09, ft.Colors.WHITE)),
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Row(
                            [
                                ft.Container(
                                    content=ft.Text(
                                        kind_palette["label"],
                                        size=9,
                                        weight=ft.FontWeight.W_800,
                                        color=GenshinTheme.ON_PRIMARY,
                                    ),
                                    bgcolor=kind_palette["accent"],
                                    padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                                    border_radius=999,
                                ),
                                ft.Container(
                                    content=ft.Text(
                                        "受控生成" if vm.is_generated else "可编辑",
                                        size=9,
                                        color=ft.Colors.AMBER_200
                                        if vm.is_generated
                                        else GenshinTheme.TEXT_SECONDARY,
                                        weight=ft.FontWeight.W_700,
                                    ),
                                    padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                                    border_radius=999,
                                    bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.WHITE),
                                    border=ft.Border.all(
                                        1, ft.Colors.with_opacity(0.08, ft.Colors.WHITE)
                                    ),
                                ),
                            ],
                            spacing=8,
                        ),
                        ft.Row(
                            [
                                ft.IconButton(
                                    icon=ft.Icons.ADD,
                                    tooltip="新增子节点",
                                    icon_color=kind_palette["accent"],
                                    on_click=lambda _: set_drawer_open(True),
                                    style=ft.ButtonStyle(
                                        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
                                        side=ft.BorderSide(
                                            width=1,
                                            color=ft.Colors.with_opacity(
                                                0.25, kind_palette["accent"]
                                            ),
                                        ),
                                        shape=ft.RoundedRectangleBorder(radius=12),
                                    ),
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_OUTLINE,
                                    tooltip="删除当前节点",
                                    icon_color=ft.Colors.with_opacity(0.9, "#F6C0C8"),
                                    disabled=not vm.can_delete,
                                    on_click=lambda _: on_delete(),
                                    style=ft.ButtonStyle(
                                        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
                                        side=ft.BorderSide(
                                            width=1,
                                            color=ft.Colors.with_opacity(0.25, "#F6C0C8"),
                                        ),
                                        shape=ft.RoundedRectangleBorder(radius=12),
                                    ),
                                ),
                            ],
                            spacing=4,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
                ft.Text(
                    f"节点类型: {vm.node_kind.value}",
                    size=11,
                    color=GenshinTheme.TEXT_SECONDARY,
                ),
                styled_text_field(
                    label="节点名称",
                    value=vm.node_name,
                    hint_text="未命名节点",
                    text_size=20,
                    text_style=ft.TextStyle(weight=ft.FontWeight.W_900),
                    on_change=lambda e: on_rename(e.control.value),
                ),
            ],
            spacing=10,
        ),
    )

    controls: list[ft.Control] = [
        hero,
        ft.Divider(height=14, color=ft.Colors.with_opacity(0.08, ft.Colors.WHITE)),
    ]

    if vm.show_rule_form:
        controls.append(
            soft_card(
                ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.TUNE, size=16, color=GenshinTheme.PRIMARY),
                                ft.Text("规则编辑", weight=ft.FontWeight.BOLD),
                            ],
                            spacing=8,
                        ),
                        ft.Container(
                            content=ft.Row(
                                [
                                    ft.Icon(ft.Icons.ACCOUNT_TREE, size=16, color=GenshinTheme.TEXT_SECONDARY),
                                    ft.Text(
                                        rule_path or "点击选择目标路径",
                                        size=13,
                                        color=GenshinTheme.TEXT_SECONDARY if not rule_path else ft.Colors.WHITE,
                                        expand=True,
                                        no_wrap=True,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.EXPAND_MORE,
                                        icon_size=16,
                                        icon_color=kind_palette["accent"],
                                        tooltip="选择路径",
                                        on_click=lambda _: set_path_selector_open(True),
                                        style=ft.ButtonStyle(
                                            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
                                        ),
                                    ),
                                ],
                                spacing=8,
                            ),
                            padding=ft.Padding(12, 10, 4, 10),
                            border_radius=14,
                            bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.WHITE),
                            border=ft.Border.all(1, ft.Colors.with_opacity(0.14, ft.Colors.WHITE)),
                            on_click=lambda _: set_path_selector_open(True),
                        ),
                        styled_text_field(
                            label="替换值",
                            value=rule_value,
                            on_change=lambda e: set_rule_value(e.control.value),
                        ),
                        ft.Button(
                            "应用规则",
                            icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
                            bgcolor=GenshinTheme.PRIMARY,
                            color=ft.Colors.WHITE,
                            expand=True,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=18),
                                padding=ft.Padding.symmetric(horizontal=16, vertical=14),
                            ),
                            on_click=lambda _: on_apply_rule(
                                rule_path, rule_value, ""
                            ),
                        ),
                    ],
                    spacing=10,
                )
            )
        )
    elif vm.show_range_form:
        controls.append(
            RangeAnchorForm(
                range_path=range_path,
                range_type=range_type,
                range_start=range_start,
                range_end=range_end,
                range_step=range_step,
                range_values=range_values,
                range_label=range_label,
                range_children_count=vm.range_children_count,
                base_config=vm.base_config,
                on_set_range_path=set_range_path,
                on_set_range_type=set_range_type,
                on_set_range_start=set_range_start,
                on_set_range_end=set_range_end,
                on_set_range_step=set_range_step,
                on_set_range_values=set_range_values,
                on_set_range_label=set_range_label,
                on_apply_range=on_apply_range,
            )
        )
    else:
        controls.append(
            soft_card(
                ft.Text(vm.help_text, color=GenshinTheme.TEXT_SECONDARY, size=12),
                padding=14,
            )
        )

    if last_summary:
        controls.extend(
            [
                ft.Divider(height=14, color=ft.Colors.with_opacity(0.08, ft.Colors.WHITE)),
                ft.Text("最近一次执行摘要", weight=ft.FontWeight.BOLD, size=13),
                soft_card(
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Container(
                                        content=ft.Text(
                                            f"总数 {last_summary.total_runs}",
                                            size=11,
                                            color=GenshinTheme.TEXT_SECONDARY,
                                        ),
                                        padding=ft.Padding.symmetric(horizontal=9, vertical=5),
                                        border_radius=999,
                                        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
                                    ),
                                    ft.Container(
                                        content=ft.Text(
                                            f"成功 {last_summary.completed_runs}",
                                            size=11,
                                            color=GenshinTheme.TEXT_SECONDARY,
                                        ),
                                        padding=ft.Padding.symmetric(horizontal=9, vertical=5),
                                        border_radius=999,
                                        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
                                    ),
                                    ft.Container(
                                        content=ft.Text(
                                            f"失败 {last_summary.failed_runs}",
                                            size=11,
                                            color=GenshinTheme.TEXT_SECONDARY,
                                        ),
                                        padding=ft.Padding.symmetric(horizontal=9, vertical=5),
                                        border_radius=999,
                                        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
                                    ),
                                ],
                                spacing=6,
                                wrap=True,
                            ),
                            ft.Text(
                                f"平均 DPS {int(last_summary.avg_dps)} | 最高 {int(last_summary.max_dps)} | 最低 {int(last_summary.min_dps)}"
                            ),
                        ],
                        spacing=8,
                    ),
                ),
            ]
        )

    def handle_select_path(path: str) -> None:
        set_rule_path(path)
        set_path_selector_open(False)

    return ft.Stack(
        expand=True,
        controls=(
            [
                ft.Column(controls, spacing=14, scroll=ft.ScrollMode.AUTO, tight=True),
            ]
            + (
                [
                    NodeAddDrawer(
                        is_open=drawer_open,
                        anchor_x=332,
                        anchor_y=60,
                        viewport_width=372,
                        on_select_kind=lambda kind: [
                            on_add_node(vm.node_id, kind),
                            set_drawer_open(False),
                        ],
                        on_close=lambda: set_drawer_open(False),
                        preferred_direction="right",
                    )
                ] if drawer_open else []
            )
            + (
                [
                    PathSelectorDrawer(
                        is_open=path_selector_open,
                        anchor_x=332,
                        anchor_y=120,
                        viewport_width=372,
                        base_config=vm.base_config,
                        on_select_path=handle_select_path,
                        on_close=lambda: set_path_selector_open(False),
                    )
                ] if path_selector_open else []
            )
        ),
    )
