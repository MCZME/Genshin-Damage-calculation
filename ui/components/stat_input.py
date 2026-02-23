import flet as ft
from ui.theme import GenshinTheme

class StatInputField(ft.Container):
    """
    原神风格属性输入框 (Reboot 版) - 适配 Flet 0.21+ 现代架构
    继承自 ft.Container 以获得完整的容器能力。
    """
    def __init__(
        self,
        label: str,
        value: str = "0",
        suffix: str = "",
        element: str = "Neutral",
        icon: str = None,
        on_change=None,
        on_label_change=None,
        label_options: list = None,
        width: float = 120
    ):
        super().__init__()
        self.label = label
        self.val = value
        self.suffix = suffix
        self.element = element
        self.icon_name = icon
        self.on_change_callback = on_change
        self.on_label_change_callback = on_label_change
        self.label_options = label_options
        self.input_width = width
        self.is_focused = False

        # 初始化 UI
        self._build_ui()

    def _build_ui(self):
        # 基础颜色
        elem_color = GenshinTheme.get_element_color(self.element)
        
        # 0. 图标 (可选)
        icon_ctrl = ft.Icon(self.icon_name, size=14, color=ft.Colors.with_opacity(0.5, elem_color)) if self.icon_name else ft.Container()

        # 1. 标签部分 (支持 Dropdown 或 Text)
        if self.label_options:
            self.label_ctrl = ft.Dropdown(
                value=self.label,
                options=[ft.dropdown.Option(opt) for opt in self.label_options],
                dense=True,
                text_size=11,
                width=100,
                border=ft.InputBorder.NONE,
                content_padding=ft.Padding(0, 0, 0, 0),
                on_select=self._handle_label_change,
            )
        else:
            self.label_ctrl = ft.Text(
                self.label, 
                size=10, 
                color=GenshinTheme.TEXT_SECONDARY, 
                weight=ft.FontWeight.W_400,
                style=ft.TextStyle(letter_spacing=0.5)
            )

        # 2. 输入控件
        self.text_field = ft.TextField(
            value=self.val,
            # 使用 suffix 组件替代 suffix_text 以增强兼容性
            suffix=ft.Text(self.suffix, size=12, color=GenshinTheme.TEXT_SECONDARY) if self.suffix else None,
            dense=True,
            content_padding=ft.Padding(8, 10, 8, 10),
            border=ft.InputBorder.NONE,
            cursor_color=elem_color,
            cursor_width=1,
            text_style=ft.TextStyle(size=14, color=GenshinTheme.ON_SURFACE, weight=ft.FontWeight.W_500),
            on_change=self._handle_change,
            on_focus=self._handle_focus,
            on_blur=self._handle_blur,
            text_align=ft.TextAlign.RIGHT,
            expand=True # 始终扩展以占据剩余空间，防止不显示
        )

        # 容器属性设置
        self.content = ft.Row(
            controls=[
                icon_ctrl,
                self.label_ctrl,
                self.text_field
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8
        )
        self.width = self.input_width
        self.height = 40 # 锁定高度确保显示
        self.padding = ft.Padding(12, 0, 12, 0)
        self.border_radius = 6
        self.bgcolor = ft.Colors.with_opacity(0.05, ft.Colors.WHITE)
        self.border = ft.border.all(1, ft.Colors.with_opacity(0.2, GenshinTheme.ON_SURFACE))
        self.animate = ft.Animation(200, ft.AnimationCurve.EASE_OUT)

    def _handle_change(self, e):
        self.val = self.text_field.value
        if self.on_change_callback:
            self.on_change_callback(self.val)

    def _handle_label_change(self, e):
        self.label = e.control.value
        if self.on_label_change_callback:
            self.on_label_change_callback(self.label)

    def _handle_focus(self, e):
        self.is_focused = True
        elem_color = GenshinTheme.get_element_color(self.element)
        self.border = ft.border.all(1.5, elem_color)
        self.shadow = GenshinTheme.get_element_glow(self.element, intensity=0.6)
        self.update()

    def _handle_blur(self, e):
        self.is_focused = False
        self.border = ft.border.all(1, ft.Colors.with_opacity(0.1, GenshinTheme.ON_SURFACE))
        self.shadow = None
        self.update()

    def update_state(self, new_val: str, new_element: str, skip_update: bool = False):
        """同步更新数值与元素主题，不重建 UI"""
        self.val = new_val
        self.element = new_element
        elem_color = GenshinTheme.get_element_color(self.element)
        
        self.text_field.value = self.val
        self.text_field.cursor_color = elem_color
        # 标签颜色更新 (如果是 Text)
        if isinstance(self.label_ctrl, ft.Text):
            self.label_ctrl.color = GenshinTheme.TEXT_SECONDARY
            
        # 焦点态逻辑同步
        if self.is_focused:
            self.border = ft.border.all(1.5, elem_color)
            self.shadow = GenshinTheme.get_element_glow(self.element, intensity=0.6)
        else:
            self.border = ft.border.all(1, ft.Colors.with_opacity(0.1, GenshinTheme.ON_SURFACE))

        if not skip_update:
            try: self.update()
            except: pass

