"""目标路径可视化选择器 - 树形弹出面板。"""
from __future__ import annotations

from typing import Any, Callable

import flet as ft

from ui.theme import GenshinTheme


def _get_list_item_name(item: Any, idx: int) -> str:
    """获取列表项的显示名称。"""
    if isinstance(item, dict):
        for key in ["name", "character", "id"]:
            if key in item:
                val = item[key]
                if isinstance(val, str):
                    return val
                if isinstance(val, dict) and "name" in val:
                    return val["name"]
    return f"[{idx}]"


def _format_value_preview(value: Any) -> str:
    """格式化值预览。"""
    if isinstance(value, str):
        return value[:20] + "..." if len(value) > 20 else value
    if isinstance(value, bool):
        return "是" if value else "否"
    if isinstance(value, (int, float)):
        return str(value)
    return str(type(value).__name__)


@ft.component
def TreeNode(
    node_key: str,
    value: Any,
    path: str,
    depth: int,
    on_select: Callable[[str], None],
) -> ft.Control:
    """单个树节点，支持展开/折叠。"""
    is_expanded, set_expanded = ft.use_state(False)
    is_hovered, set_hovered = ft.use_state(False)
    is_dict_or_list = isinstance(value, (dict, list)) and value
    indent = depth * 16

    if is_dict_or_list:
        # 可展开节点
        icon = ft.Icons.FOLDER if not is_expanded else ft.Icons.FOLDER_OPEN
        arrow = ft.Icons.KEYBOARD_ARROW_RIGHT if not is_expanded else ft.Icons.KEYBOARD_ARROW_DOWN

        children = []
        if is_expanded:
            children = [
                TreeNode(
                    node_key=k,
                    value=v,
                    path=f"{path}.{k}" if path else k,
                    depth=depth + 1,
                    on_select=on_select,
                )
                for k, v in (
                    value.items()
                    if isinstance(value, dict)
                    else [(str(i), v) for i, v in enumerate(value)]
                )
            ]

        def handle_click(e):
            set_expanded(not is_expanded)
            if e.control.page:
                e.control.page.update()

        return ft.Column(
            [
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(arrow, size=16, color=GenshinTheme.TEXT_SECONDARY),
                            ft.Icon(icon, size=14, color=GenshinTheme.PRIMARY),
                            ft.Text(node_key, size=12, weight=ft.FontWeight.W_500),
                        ],
                        spacing=6,
                    ),
                    padding=ft.Padding(left=indent, top=4, bottom=4, right=4),
                    border_radius=8,
                    bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.WHITE) if is_hovered else None,
                    on_click=handle_click,
                    on_hover=lambda e: set_hovered(e.data),
                ),
                ft.Container(
                    content=ft.Column(children, spacing=0, tight=True) if children else None,
                    padding=ft.Padding(left=0, top=0, bottom=0, right=0),
                ) if children else ft.Container(),
            ],
            spacing=0,
        )
    else:
        # 叶子节点 - 可选择
        type_icon = (
            ft.Icons.NUMBERS
            if isinstance(value, (int, float))
            else ft.Icons.TEXT_FIELDS
            if isinstance(value, str)
            else ft.Icons.CHECK_BOX
            if isinstance(value, bool)
            else ft.Icons.HELP_OUTLINE
        )

        preview = _format_value_preview(value) if value is not None else None

        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(type_icon, size=14, color=GenshinTheme.TEXT_SECONDARY),
                    ft.Text(node_key, size=12),
                    ft.Container(
                        content=ft.Text(preview, size=10, color=GenshinTheme.TEXT_SECONDARY),
                        bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.WHITE),
                        padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                        border_radius=4,
                    )
                    if preview
                    else None,
                ],
                spacing=6,
            ),
            padding=ft.Padding(left=indent + 22, top=4, bottom=4, right=4),
            border_radius=8,
            bgcolor=ft.Colors.with_opacity(0.1, GenshinTheme.PRIMARY) if is_hovered else None,
            border=ft.Border.all(1, ft.Colors.with_opacity(0.3, GenshinTheme.PRIMARY)) if is_hovered else None,
            on_click=lambda _: on_select(path),
            on_hover=lambda e: set_hovered(e.data),
        )


@ft.component
def ConfigTreeView(
    config: dict[str, Any],
    on_select: Callable[[str], None],
) -> ft.Control:
    """配置树视图。"""
    items: list[ft.Control] = []
    for key, value in config.items():
        items.append(
            TreeNode(
                node_key=key,
                value=value,
                path=key,
                depth=0,
                on_select=on_select,
            )
        )
    return ft.Column(items, spacing=0, tight=True, scroll=ft.ScrollMode.AUTO, expand=True)


@ft.component
def PathSelectorDrawer(
    is_open: bool,
    anchor_x: float,
    anchor_y: float,
    viewport_width: float,
    base_config: dict[str, Any],
    on_select_path: Callable[[str], None],
    on_close: Callable[[], None],
) -> ft.Control:
    """目标路径树形选择器弹出面板。"""
    drawer_width = 320
    drawer_gap = 10
    right_space = max(0, viewport_width - anchor_x)
    has_right_space = right_space >= drawer_width + drawer_gap

    direction = "right" if has_right_space else "left"
    left = (
        anchor_x + drawer_gap
        if direction == "right"
        else anchor_x - drawer_width - drawer_gap
    )
    left = max(8, min(left, max(8, viewport_width - drawer_width - 8)))

    return ft.Stack(
        visible=is_open,
        controls=[
            ft.Container(
                width=viewport_width,
                height=600,
                on_click=lambda _: on_close(),
                bgcolor=ft.Colors.TRANSPARENT,
            ),
            ft.Container(
                left=left,
                top=anchor_y,
                width=drawer_width,
                height=400,
                padding=12,
                border_radius=16,
                bgcolor="#2E2742",
                border=ft.Border.all(1, ft.Colors.with_opacity(0.15, ft.Colors.WHITE)),
                shadow=ft.BoxShadow(
                    blur_radius=20,
                    spread_radius=0,
                    color=ft.Colors.with_opacity(0.35, ft.Colors.BLACK),
                    offset=ft.Offset(0, 8),
                ),
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.ACCOUNT_TREE, size=14, color=GenshinTheme.PRIMARY),
                                ft.Text("选择目标路径", size=12, weight=ft.FontWeight.W_600),
                                ft.IconButton(
                                    icon=ft.Icons.CLOSE,
                                    icon_size=16,
                                    on_click=lambda _: on_close(),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ConfigTreeView(config=base_config, on_select=on_select_path),
                    ],
                    spacing=8,
                    tight=True,
                ),
            ),
        ],
    )
