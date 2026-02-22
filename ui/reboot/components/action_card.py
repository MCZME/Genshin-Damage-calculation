import flet as ft
from ui.theme import GenshinTheme

class ActionCard(ft.Container):
    """
    战术时间轴中的动作胶囊 (Action Capsule)。
    极简视觉，仅展示角色与招式标识。
    """
    def __init__(
        self,
        index: int,
        char_name: str,
        action_name: str,
        element: str = "Neutral",
        is_selected: bool = False,
        on_click=None,
        on_delete=None
    ):
        super().__init__()
        self.idx = index
        self.char_name = char_name
        self.action_name = action_name
        self.element = element
        self.is_selected = is_selected
        self.on_click_callback = on_click
        self.on_delete_callback = on_delete
        
        self._build_ui()

    def _build_ui(self):
        elem_color = GenshinTheme.get_element_color(self.element)
        
        # 背景渐变
        bg_opacity = 0.25 if self.is_selected else 0.08
        bg_gradient = ft.LinearGradient(
            begin=ft.Alignment(-1, -1),
            end=ft.Alignment(1, 1),
            colors=[
                ft.Colors.with_opacity(bg_opacity, elem_color),
                ft.Colors.with_opacity(bg_opacity * 0.4, elem_color),
            ]
        )

        # 映射显示名
        display_name = self.action_name
        if "normal" in self.action_name.lower(): display_name = "普攻"
        elif "skill" in self.action_name.lower(): display_name = "战技"
        elif "burst" in self.action_name.lower(): display_name = "爆发"
        elif "charged" in self.action_name.lower(): display_name = "重击"
        elif "plung" in self.action_name.lower(): display_name = "下落"
        elif "dash" in self.action_name.lower(): display_name = "冲刺"
        elif "skip" in self.action_name.lower(): display_name = "等待"

        # 内部显示：角色简称 + 动作大标识
        self.content = ft.Stack([
            ft.Container(expand=True, gradient=bg_gradient, border_radius=12),
            ft.Column([
                ft.Text(
                    self.char_name if self.char_name else "??", 
                    size=7, weight=ft.FontWeight.W_600, 
                    color=ft.Colors.with_opacity(0.5, ft.Colors.WHITE),
                    no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS
                ),
                ft.Text(
                    display_name, 
                    size=16, weight=ft.FontWeight.W_900, 
                    color=ft.Colors.WHITE,
                    no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS
                ),
            ], spacing=-2, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            
            # 右上角微型状态标识 (选中时增加一个光点)
            ft.Container(
                content=ft.CircleAvatar(radius=2, bgcolor=elem_color) if self.is_selected else None,
                alignment=ft.Alignment.TOP_RIGHT,
                padding=ft.Padding(0, 6, 6, 0),
            )
        ], alignment=ft.Alignment.CENTER)


        # 容器属性
        self.width = 80
        self.height = 55
        self.border_radius = 12
        self.border = ft.Border.all(
            2 if self.is_selected else 1, 
            ft.Colors.with_opacity(0.6 if self.is_selected else 0.15, elem_color)
        )
        self.shadow = GenshinTheme.get_element_glow(self.element, 0.4) if self.is_selected else None
        self.on_click = lambda _: self.on_click_callback(self.idx) if self.on_click_callback else None
        self.mouse_cursor = ft.MouseCursor.CLICK
        self.animate = ft.Animation(300, ft.AnimationCurve.DECELERATE)
        self.animate_scale = ft.Animation(300, ft.AnimationCurve.EASE_OUT_BACK)
        self.scale = 1.05 if self.is_selected else 1.0

    def _handle_delete(self, e):
        if self.on_delete_callback:
            self.on_delete_callback(self.idx)

    def update_selection(self, is_selected: bool):
        self.is_selected = is_selected
        self._build_ui()
        try: self.update()
        except: pass
