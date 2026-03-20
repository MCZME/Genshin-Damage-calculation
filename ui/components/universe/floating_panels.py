from __future__ import annotations

import flet as ft

from ui.theme import GenshinTheme


@ft.component
def StatusBar(status_text: str, error_message: str, progress: float):
    return ft.Container(
        content=ft.Row(
            [
                ft.Column(
                    [
                        ft.Text(
                            status_text,
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=GenshinTheme.ON_SURFACE,
                        ),
                        ft.Text(
                            error_message or "状态稳定",
                            size=11,
                            color=ft.Colors.RED_300
                            if error_message
                            else GenshinTheme.TEXT_SECONDARY,
                        ),
                    ],
                    spacing=4,
                ),
                ft.Container(
                    width=320,
                    content=ft.ProgressBar(
                        value=progress,
                        color=GenshinTheme.PRIMARY,
                        bgcolor="rgba(255,255,255,0.08)",
                    ),
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        left=24,
        right=24,
        bottom=18,
        padding=ft.Padding.symmetric(horizontal=20, vertical=14),
        border_radius=18,
        bgcolor="rgba(28, 24, 41, 0.88)",
        border=ft.border.all(1, "rgba(255,255,255,0.08)"),
    )
