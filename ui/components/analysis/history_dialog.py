import flet as ft
from ui.theme import GenshinTheme

class HistoryDialog(ft.Container):
    """
    仿真历史记录选择组件 (Artifact Prime 风格)。
    作为一个独立浮窗内容存在，提供仿真记录的浏览与加载。
    """
    def __init__(self, sessions, on_select, on_close):
        super().__init__()
        self.sessions = sessions
        self.on_select_callback = on_select
        self.on_close_callback = on_close
        
        # 基础视觉配置 (Artifact Prime 外壳)
        self.width = 650
        self.height = 550
        self.padding = 2
        self.gradient = ft.LinearGradient(
            begin=ft.Alignment(0, -1),
            end=ft.Alignment(0, 1),
            colors=[GenshinTheme.GOLD_LIGHT, GenshinTheme.GOLD_DARK, "#2A2435"]
        )
        self.border_radius = ft.BorderRadius.only(top_left=34, bottom_right=34, top_right=8, bottom_left=8)
        
        self._build_ui()

    def _build_ui(self):
        # 1. 构建列表内容
        list_items = []
        for s in self.sessions:
            list_items.append(
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.DASHBOARD_ROUNDED, color=GenshinTheme.GOLD_DARK),
                    title=ft.Text(f"仿真会话 #{s['id']}", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    subtitle=ft.Text(f"时间: {s['time']} | 伤害: {s['damage']:,.0f}", color=ft.Colors.with_opacity(0.7, ft.Colors.WHITE)),
                    trailing=ft.Text(f"{s['duration']:.1f}s", color=ft.Colors.with_opacity(0.4, ft.Colors.WHITE)),
                    on_click=lambda _, sid=s['id']: self.on_select_callback(sid),
                    hover_color=ft.Colors.with_opacity(0.05, ft.Colors.WHITE)
                )
            )

        # 2. 内层包装 (紫色核心)
        self.content = ft.Container(
            bgcolor="#1A1625",
            border_radius=ft.BorderRadius.only(top_left=32, bottom_right=32, top_right=6, bottom_left=6),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=ft.Stack([
                # 顶部高光
                ft.Container(
                    height=150,
                    top=0, left=0, right=0,
                    gradient=ft.LinearGradient(
                        begin=ft.Alignment(0, -1),
                        end=ft.Alignment(0, 1),
                        colors=[ft.Colors.with_opacity(0.2, GenshinTheme.GOLD_DARK), ft.Colors.TRANSPARENT]
                    ),
                ),
                # 装饰暗纹
                ft.Container(
                    content=ft.Icon(ft.Icons.AUTO_AWESOME, size=250, color=ft.Colors.with_opacity(0.015, ft.Colors.WHITE)),
                    right=-80, bottom=-80
                ),
                # 核心布局
                ft.Column([
                    # Header
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
                                on_click=lambda _: self.on_close_callback()
                            )
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                    ),
                    # 列表区域
                    ft.Container(
                        content=ft.ListView(list_items, expand=True, spacing=5),
                        expand=True,
                        padding=ft.Padding(20, 10, 20, 20)
                    )
                ], spacing=0)
            ])
        )
