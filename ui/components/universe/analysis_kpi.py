"""批处理分析 KPI 卡片组件。"""

from __future__ import annotations

import flet as ft

from ui.theme import GenshinTheme


@ft.component
def BatchAnalysisKPICard(
    icon: ft.IconData,
    label: str,
    value: str,
    accent_color: str = GenshinTheme.PRIMARY,
) -> ft.Control:
    """批处理分析指标卡片。

    Args:
        icon: 图标数据。
        label: 指标名称标签。
        value: 指标数值（已格式化）。
        accent_color: 强调色，用于图标和高亮。

    Returns:
        ft.Control: 卡片容器控件。
    """
    return ft.Container(
        expand=1,
        padding=16,
        border_radius=16,
        bgcolor=GenshinTheme.GLASS_BG,
        border=ft.Border.all(1.2, GenshinTheme.GLASS_BORDER),
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(
                            icon,
                            size=18,
                            color=accent_color,
                        ),
                        ft.Text(
                            label,
                            size=12,
                            color=GenshinTheme.TEXT_SECONDARY,
                            weight=ft.FontWeight.W_500,
                        ),
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Text(
                    value,
                    size=28,
                    weight=ft.FontWeight.W_900,
                    color=GenshinTheme.ON_SURFACE,
                ),
            ],
            spacing=8,
        ),
    )
