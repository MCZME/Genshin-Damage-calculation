"""区间锚点表单组件。"""
from __future__ import annotations
from collections.abc import Callable

import flet as ft

from core.batch.models import RangeType
from ui.components.universe.path_selector_drawer import PathSelectorDrawer
from ui.theme import GenshinTheme

RANGE_ACCENT = "#6AB3FF"


@ft.component
def RangeAnchorForm(
    range_path: str,
    range_type: str,
    range_start: str,
    range_end: str,
    range_step: str,
    range_values: str,
    range_label: str,
    range_children_count: int,
    base_config: dict,
    on_set_range_path: Callable[[str], None],
    on_set_range_type: Callable[[str], None],
    on_set_range_start: Callable[[str], None],
    on_set_range_end: Callable[[str], None],
    on_set_range_step: Callable[[str], None],
    on_set_range_values: Callable[[str], None],
    on_set_range_label: Callable[[str], None],
    on_apply_range: Callable[[str, str, str, str, str, str, str], None],
) -> ft.Control:
    """区间锚点配置表单。"""
    path_selector_open, set_path_selector_open = ft.use_state(False)
    current_type = RangeType(range_type) if range_type else RangeType.NUMERIC

    def styled_text_field(
        *,
        label: str,
        value: str,
        on_change: Callable[..., None],
        expand: bool = False,
        multiline: bool = False,
        hint_text: str = "",
    ) -> ft.TextField:
        return ft.TextField(
            label=label,
            value=value,
            on_change=on_change,
            text_size=15,
            hint_text=hint_text,
            label_style=ft.TextStyle(
                size=12,
                color=ft.Colors.with_opacity(0.78, GenshinTheme.TEXT_SECONDARY),
            ),
            hint_style=ft.TextStyle(
                size=13,
                color=ft.Colors.with_opacity(0.50, GenshinTheme.TEXT_SECONDARY),
            ),
            bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.WHITE),
            border=ft.InputBorder.OUTLINE,
            border_radius=14,
            border_width=1.2,
            border_color=ft.Colors.with_opacity(0.14, ft.Colors.WHITE),
            focused_border_width=1.8,
            focused_border_color=ft.Colors.with_opacity(0.65, RANGE_ACCENT),
            content_padding=ft.Padding.symmetric(horizontal=14, vertical=12),
            cursor_color=RANGE_ACCENT,
            selection_color=ft.Colors.with_opacity(0.25, RANGE_ACCENT),
            expand=expand,
            multiline=multiline,
            min_lines=1 if not multiline else 2,
            max_lines=3 if multiline else 1,
        )

    def handle_select_path(path: str) -> None:
        on_set_range_path(path)
        set_path_selector_open(False)

    def soft_card(content: ft.Control, padding: int = 16) -> ft.Container:
        return ft.Container(
            content=content,
            padding=padding,
            border_radius=16,
            bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.WHITE),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.08, ft.Colors.WHITE)),
        )

    def type_chip(text: str, type_val: RangeType, selected_type: RangeType) -> ft.Container:
        is_selected = type_val == selected_type
        return ft.Container(
            content=ft.Text(text, size=12, weight=ft.FontWeight.W_600),
            padding=ft.Padding.symmetric(horizontal=12, vertical=6),
            border_radius=999,
            bgcolor=ft.Colors.with_opacity(0.15, RANGE_ACCENT) if is_selected else ft.Colors.with_opacity(0.06, ft.Colors.WHITE),
            border=ft.Border.all(1, RANGE_ACCENT if is_selected else ft.Colors.with_opacity(0.14, ft.Colors.WHITE)),
            on_click=lambda _: on_set_range_type(type_val.value),
        )

    is_numeric = current_type == RangeType.NUMERIC

    # 根据类型显示不同的输入区域
    if is_numeric:
        value_inputs = ft.Row(
            [
                styled_text_field(
                    label="起始",
                    value=range_start,
                    on_change=lambda e: on_set_range_start(e.control.value),  # type: ignore
                    expand=True,
                ),
                styled_text_field(
                    label="终止",
                    value=range_end,
                    on_change=lambda e: on_set_range_end(e.control.value),  # type: ignore
                    expand=True,
                ),
                styled_text_field(
                    label="步长",
                    value=range_step,
                    on_change=lambda e: on_set_range_step(e.control.value),  # type: ignore
                    expand=True,
                ),
            ],
            spacing=10,
        )
    else:
        value_inputs = styled_text_field(
            label="枚举值（逗号分隔）",
            value=range_values,
            hint_text="例如: 芙宁娜, 那维莱特, 娜维娅",
            on_change=lambda e: on_set_range_values(e.control.value),  # type: ignore
            multiline=True,
        )

    form_content = ft.Column(
        [
            ft.Row(
                [
                    ft.Icon(ft.Icons.MULTILINE_CHART, size=16, color=RANGE_ACCENT),
                    ft.Text("区间锚点", weight=ft.FontWeight.BOLD),
                ],
                spacing=8,
            ),
            ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.ACCOUNT_TREE, size=16, color=GenshinTheme.TEXT_SECONDARY),
                        ft.Text(
                            range_path or "点击选择目标路径",
                            size=13,
                            color=GenshinTheme.TEXT_SECONDARY if not range_path else ft.Colors.WHITE,
                            expand=True,
                            no_wrap=True,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.EXPAND_MORE,
                            icon_size=16,
                            icon_color=RANGE_ACCENT,
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
            ft.Row(
                [
                    ft.Text("类型:", size=13, color=GenshinTheme.TEXT_SECONDARY),
                    type_chip("数值区间", RangeType.NUMERIC, current_type),
                    type_chip("枚举列表", RangeType.ENUM, current_type),
                ],
                spacing=8,
            ),
            value_inputs,
            styled_text_field(
                label="区间标签",
                value=range_label,
                on_change=lambda e: on_set_range_label(e.control.value),  # type: ignore
            ),
            ft.ElevatedButton(
                "生成区间子节点",
                icon=ft.Icons.AUTO_AWESOME,
                bgcolor=GenshinTheme.PRIMARY,
                color=ft.Colors.WHITE,
                expand=True,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=18),
                    padding=ft.Padding.symmetric(horizontal=16, vertical=14),
                ),
                on_click=lambda _: on_apply_range(
                    range_path,
                    range_start,
                    range_end,
                    range_step,
                    range_label,
                    current_type.value,
                    range_values,
                ),
            ),
            ft.Container(
                padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                border_radius=999,
                bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
                border=ft.Border.all(1, ft.Colors.with_opacity(0.08, ft.Colors.WHITE)),
                content=ft.Text(
                    f"当前生成子节点数: {range_children_count}",
                    color=GenshinTheme.TEXT_SECONDARY,
                    size=11,
                ),
            ),
        ],
        spacing=10,
    )

    return ft.Stack(
        controls=[
            soft_card(form_content),
            (
                PathSelectorDrawer(
                    is_open=path_selector_open,
                    anchor_x=332,
                    anchor_y=200,
                    viewport_width=372,
                    base_config=base_config,
                    on_select_path=handle_select_path,
                    on_close=lambda: set_path_selector_open(False),
                )
                if path_selector_open
                else ft.Container()
            ),
        ],
    )
