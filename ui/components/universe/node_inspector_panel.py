from __future__ import annotations

import flet as ft

from core.batch.models import BatchNodeKind, BatchRunSummary
from ui.theme import GenshinTheme
from ui.view_models.universe.node_inspector_panel_vm import NodeInspectorPanelViewModel


@ft.component
def NodeInspectorPanel(
    vm: NodeInspectorPanelViewModel,
    on_rename,
    on_add_rule,
    on_add_range,
    on_delete,
    on_apply_rule,
    on_apply_range,
    last_summary: BatchRunSummary | None = None,
) -> ft.Control:
    rule_path, set_rule_path = ft.use_state(vm.rule_path_text)
    rule_value, set_rule_value = ft.use_state(vm.rule_value_text)
    rule_label, set_rule_label = ft.use_state(vm.rule_label_text)

    range_path, set_range_path = ft.use_state(vm.range_path_text)
    range_start, set_range_start = ft.use_state(vm.range_start_text)
    range_end, set_range_end = ft.use_state(vm.range_end_text)
    range_step, set_range_step = ft.use_state(vm.range_step_text)
    range_label, set_range_label = ft.use_state(vm.range_label_text)

    def sync_inputs() -> None:
        set_rule_path(vm.rule_path_text)
        set_rule_value(vm.rule_value_text)
        set_rule_label(vm.rule_label_text)
        set_range_path(vm.range_path_text)
        set_range_start(vm.range_start_text)
        set_range_end(vm.range_end_text)
        set_range_step(vm.range_step_text)
        set_range_label(vm.range_label_text)

    ft.use_effect(sync_inputs, [vm.node_id])

    name_field = ft.TextField(
        label="节点名称",
        value=vm.node_name,
        on_change=lambda e: on_rename(e.control.value),
    )

    node_meta = ft.Container(
        content=ft.Row(
            [
                ft.Text(f"类型: {vm.node_kind.value}", color=GenshinTheme.TEXT_SECONDARY),
                ft.Text(
                    "受控子节点" if vm.is_generated else "可编辑",
                    color=ft.Colors.AMBER_200 if vm.is_generated else GenshinTheme.TEXT_SECONDARY,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=ft.Padding.symmetric(horizontal=4),
    )

    actions = ft.Row(
        [
            ft.OutlinedButton(
                "新增规则子节点",
                icon=ft.Icons.ADD_CIRCLE_OUTLINE,
                on_click=lambda _: on_add_rule(vm.node_id),
            ),
            ft.OutlinedButton(
                "新增区间锚点",
                icon=ft.Icons.LINE_AXIS,
                on_click=lambda _: on_add_range(vm.node_id),
            ),
            ft.TextButton(
                "删除当前节点",
                icon=ft.Icons.DELETE_OUTLINE,
                disabled=not vm.can_delete,
                on_click=lambda _: on_delete(),
            ),
        ],
        wrap=True,
    )

    controls: list[ft.Control] = [name_field, node_meta, actions, ft.Divider()]

    if vm.show_rule_form:
        controls.append(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("规则编辑", weight=ft.FontWeight.BOLD),
                        ft.Text(
                            "路径使用点分隔，例如 context_config.team.0.character.level",
                            size=11,
                            color=GenshinTheme.TEXT_SECONDARY,
                        ),
                        ft.TextField(
                            label="目标路径",
                            value=rule_path,
                            on_change=lambda e: set_rule_path(e.control.value),
                        ),
                        ft.TextField(
                            label="替换值",
                            value=rule_value,
                            on_change=lambda e: set_rule_value(e.control.value),
                        ),
                        ft.TextField(
                            label="规则标签",
                            value=rule_label,
                            on_change=lambda e: set_rule_label(e.control.value),
                        ),
                        ft.ElevatedButton(
                            "应用规则",
                            bgcolor=GenshinTheme.PRIMARY,
                            color=ft.Colors.WHITE,
                            on_click=lambda _: on_apply_rule(
                                rule_path, rule_value, rule_label
                            ),
                        ),
                    ],
                    spacing=10,
                ),
                padding=16,
                border_radius=16,
                bgcolor=GenshinTheme.SURFACE,
                border=ft.border.all(1, GenshinTheme.GLASS_BORDER),
            )
        )
    elif vm.show_range_form:
        controls.append(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("区间锚点", weight=ft.FontWeight.BOLD),
                        ft.TextField(
                            label="目标路径",
                            value=range_path,
                            on_change=lambda e: set_range_path(e.control.value),
                        ),
                        ft.Row(
                            [
                                ft.TextField(
                                    label="起始",
                                    value=range_start,
                                    on_change=lambda e: set_range_start(e.control.value),
                                    expand=True,
                                ),
                                ft.TextField(
                                    label="终止",
                                    value=range_end,
                                    on_change=lambda e: set_range_end(e.control.value),
                                    expand=True,
                                ),
                                ft.TextField(
                                    label="步长",
                                    value=range_step,
                                    on_change=lambda e: set_range_step(e.control.value),
                                    expand=True,
                                ),
                            ],
                            spacing=10,
                        ),
                        ft.TextField(
                            label="区间标签",
                            value=range_label,
                            on_change=lambda e: set_range_label(e.control.value),
                        ),
                        ft.ElevatedButton(
                            "生成区间子节点",
                            bgcolor=GenshinTheme.PRIMARY,
                            color=ft.Colors.WHITE,
                            on_click=lambda _: on_apply_range(
                                range_path,
                                range_start,
                                range_end,
                                range_step,
                                range_label,
                            ),
                        ),
                        ft.Text(
                            f"当前生成子节点数: {vm.range_children_count}",
                            color=GenshinTheme.TEXT_SECONDARY,
                            size=11,
                        ),
                    ],
                    spacing=10,
                ),
                padding=16,
                border_radius=16,
                bgcolor=GenshinTheme.SURFACE,
                border=ft.border.all(1, GenshinTheme.GLASS_BORDER),
            )
        )
    else:
        controls.append(ft.Text(vm.help_text, color=GenshinTheme.TEXT_SECONDARY))

    if last_summary:
        controls.extend(
            [
                ft.Divider(),
                ft.Text("最近一次执行摘要", weight=ft.FontWeight.BOLD),
                ft.Text(
                    f"总数 {last_summary.total_runs} | 成功 {last_summary.completed_runs} | 失败 {last_summary.failed_runs}"
                ),
                ft.Text(
                    f"平均 DPS {int(last_summary.avg_dps)} | 最高 {int(last_summary.max_dps)} | 最低 {int(last_summary.min_dps)}"
                ),
            ]
        )

    return ft.Column(controls, spacing=14, scroll=ft.ScrollMode.AUTO)
