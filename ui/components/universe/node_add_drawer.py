from __future__ import annotations

import flet as ft

from core.batch.models import BatchNodeKind
from ui.theme import GenshinTheme


def _kind_meta(kind: BatchNodeKind) -> tuple[str, ft.IconData, str]:
    if kind == BatchNodeKind.RULE:
        return ("规则节点", ft.Icons.TUNE, "用于单点参数替换")
    if kind == BatchNodeKind.RANGE_ANCHOR:
        return ("区间锚点", ft.Icons.MULTILINE_CHART, "用于批量生成区间子节点")
    return (kind.value, ft.Icons.ADD_BOX, "扩展类型")


def _iter_addable_kinds() -> list[BatchNodeKind]:
    ordered = [BatchNodeKind.RULE, BatchNodeKind.RANGE_ANCHOR]
    rest = [
        kind
        for kind in BatchNodeKind
        if kind not in ordered and kind != BatchNodeKind.ROOT
    ]
    return [*ordered, *rest]


@ft.component
def NodeAddDrawer(
    is_open: bool,
    anchor_x: float,
    anchor_y: float,
    viewport_width: float,
    on_select_kind,
    on_close,
    preferred_direction: str = "right",
) -> ft.Control:
    drawer_width = 220
    drawer_gap = 10
    right_space = max(0, viewport_width - anchor_x)
    has_right_space = right_space >= drawer_width + drawer_gap

    if preferred_direction == "right" and has_right_space:
        direction = "right"
    elif preferred_direction == "left" and not has_right_space:
        direction = "left"
    else:
        direction = "right" if has_right_space else "left"

    left = anchor_x + drawer_gap if direction == "right" else anchor_x - drawer_width - drawer_gap
    left = max(8, min(left, max(8, viewport_width - drawer_width - 8)))

    options = _iter_addable_kinds()
    tiles: list[ft.Control] = []
    for kind in options:
        title, icon, desc = _kind_meta(kind)
        tiles.append(
            ft.ListTile(
                leading=ft.Icon(icon, color=GenshinTheme.PRIMARY, size=18),
                title=ft.Text(title, size=13, weight=ft.FontWeight.W_700),
                subtitle=ft.Text(desc, size=11, color=GenshinTheme.TEXT_SECONDARY),
                dense=True,
                shape=ft.RoundedRectangleBorder(radius=12),
                on_click=lambda _, k=kind: on_select_kind(k),
            )
        )

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
                                ft.Text("添加节点", size=12, color=GenshinTheme.TEXT_SECONDARY),
                                ft.IconButton(
                                    icon=ft.Icons.CLOSE,
                                    icon_size=16,
                                    on_click=lambda _: on_close(),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Column(tiles, spacing=4, tight=True),
                    ],
                    spacing=6,
                    tight=True,
                ),
            ),
        ],
    )
