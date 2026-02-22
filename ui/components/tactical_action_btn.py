import flet as ft
from ui.theme import GenshinTheme
from ui.services.ui_formatter import UIFormatter

class TacticalActionBtn(ft.Container):
    """
    战术招式指令按钮 (原子化重构版)。
    展示简化的招式标签，并根据角色元素提供主题色。
    """
    def __init__(self, action_key: str, label: str, element: str, on_click=None):
        super().__init__()
        self.action_key = action_key
        self.label = label
        self.element = element
        self.on_click_callback = on_click
        
        self._build_ui()

    def _build_ui(self):
        elem_color = GenshinTheme.get_element_color(self.element)
        
        # 简化显示标签
        short_label = UIFormatter.shorten_action_label(self.label)
        
        self.content = ft.Text(short_label, size=12, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER)
        self.width = 100
        self.height = 45
        self.bgcolor = ft.Colors.with_opacity(0.1, elem_color)
        self.border = ft.Border.all(1, ft.Colors.with_opacity(0.4, elem_color))
        self.border_radius = 8
        self.alignment = ft.Alignment.CENTER
        self.on_click = lambda _: self.on_click_callback(self.action_key) if self.on_click_callback else None
        self.tooltip = self.label
        self.mouse_cursor = ft.MouseCursor.CLICK

    def update_state(self, element: str):
        self.element = element
        self._build_ui()
        try: self.update()
        except: pass
