import flet as ft
from ui.theme import GenshinTheme

@ft.component
def HistoryDialog(sessions, on_select, on_close):
    """
    仿真历史记录选择组件 (声明式版)。
    """
    # 1. 构建列表内容
    if not sessions:
        content_view = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.HISTORY_ROUNDED, size=64, color=ft.Colors.with_opacity(0.2, GenshinTheme.GOLD_DARK)),
                ft.Text("暂无仿真历史记录", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.with_opacity(0.5, ft.Colors.WHITE)),
                ft.Text("完成一次仿真后，结果将自动保存至此处", size=14, color=ft.Colors.with_opacity(0.3, ft.Colors.WHITE)),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            alignment=ft.alignment.center,
            expand=True
        )
    else:
        list_items = []
        for s in sessions:
            list_items.append(
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.DASHBOARD_ROUNDED, color=GenshinTheme.GOLD_DARK),
                    title=ft.Text(f"仿真会话 #{s['id']}", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    subtitle=ft.Text(f"时间: {s['time']} | 伤害: {s['damage']:,.0f}", color=ft.Colors.with_opacity(0.7, ft.Colors.WHITE)),
                    trailing=ft.Text(f"{s['duration']:.1f}s", color=ft.Colors.with_opacity(0.4, ft.Colors.WHITE)),
                    on_click=lambda _, sid=s['id']: on_select(sid),
                    hover_color=ft.Colors.with_opacity(0.05, ft.Colors.WHITE)
                )
            )
        content_view = ft.ListView(list_items, expand=True, spacing=5, item_extent=70)

    # 2. 内层核心视图 (紫色核心)
    inner_content = ft.Container(
        bgcolor="#1A1625",
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        border_radius=ft.BorderRadius.only(top_left=32, bottom_right=32, top_right=6, bottom_left=6),
        content=ft.Stack([
            ft.Container(
                height=150, top=0, left=0, right=0,
                gradient=ft.LinearGradient(
                    begin=ft.Alignment(0, -1), end=ft.Alignment(0, 1),
                    colors=[ft.Colors.with_opacity(0.2, GenshinTheme.GOLD_DARK), ft.Colors.TRANSPARENT]
                ),
            ),
            ft.Container(
                content=ft.Icon(ft.Icons.AUTO_AWESOME, size=250, color=ft.Colors.with_opacity(0.015, ft.Colors.WHITE)),
                right=-80, bottom=-80
            ),
            ft.Column([
                ft.Container(
                    padding=ft.Padding(30, 20, 25, 15),
                    border=ft.Border(bottom=ft.BorderSide(1, ft.Colors.with_opacity(0.05, ft.Colors.WHITE))),
                    content=ft.Row([
                        ft.Row([
                            ft.Icon(ft.Icons.HISTORY_ROUNDED, color=GenshinTheme.GOLD_DARK),
                            ft.Container(
                                content=ft.Text("仿真历史记录回顾", size=16, weight=ft.FontWeight.W_800, color=GenshinTheme.GOLD_DARK, style=ft.TextStyle(letter_spacing=1.5)),
                                padding=ft.Padding(0, 2, 0, 0)
                            )
                        ], spacing=15),
                        ft.IconButton(
                            ft.Icons.CLOSE_ROUNDED, 
                            icon_color=ft.Colors.RED_ACCENT_200,
                            tooltip="关闭面板",
                            on_click=lambda _: on_close()
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                ),
                ft.Container(
                    content=content_view,
                    expand=True,
                    padding=ft.Padding(20, 10, 20, 20)
                )
            ], spacing=0)
        ])
    )

    # 最终外层容器 (外壳)
    return ft.Container(
        content=inner_content,
        width=650, height=550, padding=2,
        gradient=ft.LinearGradient(
            begin=ft.Alignment(0, -1), end=ft.Alignment(0, 1),
            colors=[GenshinTheme.GOLD_LIGHT, GenshinTheme.GOLD_DARK, "#2A2435"]
        ),
        border_radius=ft.BorderRadius.only(top_left=34, bottom_right=34, top_right=8, bottom_left=8)
    )
