"""路径选择配置项组件。"""
from __future__ import annotations

import flet as ft
from typing import Any, Callable, TYPE_CHECKING, cast

from ui.theme import GenshinTheme

if TYPE_CHECKING:
    from flet import Page


@ft.component
def ConfigPathItem(
    label: str,
    value: str,
    on_change: Callable[[str], Any],
    page: "Page",
    browse_type: str = "folder",
) -> ft.Control:
    """
    路径选择配置项组件。

    Args:
        label: 配置项标签
        value: 当前路径
        on_change: 值变更回调
        page: Flet Page 对象
        browse_type: 浏览类型 ("folder" 或 "file")
    """

    async def handle_browse() -> None:
        if browse_type == "folder":
            picker = ft.FilePicker()
            page.overlay.append(picker)
            dir_path = await picker.get_directory_path(dialog_title=f"选择{label}")
            if dir_path:
                on_change(dir_path)
            page.overlay.remove(picker)
        else:
            picker = ft.FilePicker()
            page.overlay.append(picker)
            # ft.FilePicker.pick_files 异步调用直接返回 list[FilePickerFile] | None
            files = await picker.pick_files(dialog_title=f"选择{label}")
            if files and len(files) > 0:
                on_change(cast(str, files[0].path))
            page.overlay.remove(picker)

    return ft.Container(
        content=ft.Column(
            [
            ft.Text(
                label,
                size=12,
                weight=ft.FontWeight.W_500,
                color=GenshinTheme.TEXT_SECONDARY,
            ),
            ft.Row(
                [
                    ft.TextField(
                        value=value,
                        on_change=lambda e: on_change(e.control.value or ""),
                        expand=True,
                        dense=True,
                        text_size=12,
                        border_color=ft.Colors.WHITE_24,
                        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
                        cursor_color=GenshinTheme.PRIMARY,
                    ),
                    ft.IconButton(
                        ft.Icons.FOLDER_OPEN,
                        icon_color=GenshinTheme.PRIMARY,
                        on_click=lambda _: page.run_task(handle_browse),
                        tooltip="浏览...",
                        icon_size=20,
                    ),
                ],
                spacing=8,
            ),
            ],
            spacing=4,
        ),
        padding=ft.Padding(12, 8, 12, 8),
        bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.WHITE),
        border_radius=8,
    )
