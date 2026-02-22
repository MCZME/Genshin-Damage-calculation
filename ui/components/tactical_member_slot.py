import flet as ft
from ui.theme import GenshinTheme

class TacticalMemberSlot(ft.Container):
    """
    战术视图侧边栏成员槽位 (原子化重构版)。
    仅显示头像、名字与元素，高度固定。
    """
    def __init__(
        self, 
        index: int, 
        member: dict, 
        is_selected: bool = False,
        on_click = None
    ):
        super().__init__()
        self.index = index
        self.member = member
        self.is_selected = is_selected
        self.on_click_callback = on_click
        
        self._build_ui()

    def _build_ui(self):
        is_empty = self.member.get("id") is None
        elem_color = GenshinTheme.get_element_color(self.member.get("element", "Neutral"))

        if is_empty:
            self.content = ft.Text("未配置角色", size=11, color=ft.Colors.WHITE_24)
            self.height = 60
            self.alignment = ft.Alignment.CENTER
            self.bgcolor = ft.Colors.with_opacity(0.03, ft.Colors.WHITE)
            self.border_radius = 12
            self.border = ft.Border.all(1, ft.Colors.with_opacity(0.12, ft.Colors.WHITE))
            return

        bg_opacity = 0.28 if self.is_selected else 0.10
        avatar = ft.Container(
            content=ft.Text(self.member.get("name", "?")[0], size=15, weight=ft.FontWeight.W_900, color=ft.Colors.WHITE),
            width=36, height=36, bgcolor=ft.Colors.with_opacity(0.3, elem_color),
            border_radius=18, alignment=ft.Alignment.CENTER,
            border=ft.Border.all(1.5, ft.Colors.with_opacity(0.6 if self.is_selected else 0.25, elem_color))
        )

        self.content = ft.Row([
            avatar,
            ft.Column([
                ft.Text(self.member.get("name", "未选定"), size=13, weight=ft.FontWeight.W_900 if self.is_selected else ft.FontWeight.BOLD),
                ft.Text(self.member.get("element", "Neutral"), size=10, opacity=0.5),
            ], spacing=1, expand=True)
        ], spacing=9, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        
        self.padding = ft.Padding(11, 11, 11, 11)
        self.height = 60
        self.border_radius = 12
        self.bgcolor = ft.Colors.with_opacity(bg_opacity, elem_color)
        self.border = ft.Border.all(2 if self.is_selected else 1, ft.Colors.with_opacity(0.65 if self.is_selected else 0.12, elem_color))
        self.on_click = lambda _: self.on_click_callback(self.index) if self.on_click_callback else None
        self.offset = ft.Offset(0.04, 0) if self.is_selected else ft.Offset(0, 0)
        self.animate = ft.Animation(300, ft.AnimationCurve.DECELERATE)
        self.animate_offset = ft.Animation(300, ft.AnimationCurve.EASE_OUT_BACK)
        self.mouse_cursor = ft.MouseCursor.CLICK

    def update_state(self, member: dict, is_selected: bool):
        self.member = member
        self.is_selected = is_selected
        self._build_ui()
        try: self.update()
        except: pass
