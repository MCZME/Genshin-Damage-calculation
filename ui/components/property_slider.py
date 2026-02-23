import flet as ft
from ui.theme import GenshinTheme

class PropertySlider(ft.Container):
    """
    无抖动状态感知型属性滑块。
    锁定外部尺寸，通过内部内容置换实现双态切换，不影响全局布局。
    """
    def __init__(
        self,
        label: str,
        value: int,
        min_val: int = 0,
        max_val: int = 100,
        divisions: int = None,
        discrete_values: list = None,
        element: str = "Neutral",
        on_change=None,
        on_focus=None # 新增焦点申请回调
    ):
        super().__init__()
        self.label = label
        self.val = value
        self.min_val = min_val
        self.max_val = max_val
        self.divisions = divisions
        self.discrete_values = discrete_values
        self.element = element
        self.on_change_callback = on_change
        self.on_focus_callback = on_focus
        
        # 核心状态：是否处于编辑模式
        self.is_edit_mode = False
        
        self._build_ui()

    def _build_ui(self):
        elem_color = GenshinTheme.get_element_color(self.element)
        
        # --- 浏览态组件 ---
        self.label_text_browse = ft.Text(self.label, size=11, color=GenshinTheme.TEXT_SECONDARY, weight=ft.FontWeight.W_400)
        self.val_text_browse = ft.Text(str(self.val), size=18, weight=ft.FontWeight.W_900, color=ft.Colors.WHITE)
        self.browse_view = ft.Container(
            content=ft.Row([
                self.label_text_browse,
                self.val_text_browse
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.Padding(12, 0, 12, 0),
            alignment=ft.Alignment.CENTER,
            expand=True
        )

        # --- 编辑态组件 ---
        slider_val = self.val
        if self.discrete_values:
            try: slider_val = self.discrete_values.index(self.val)
            except: slider_val = 0
            s_min, s_max, s_div = 0, len(self.discrete_values)-1, len(self.discrete_values)-1
        else:
            s_min, s_max, s_div = self.min_val, self.max_val, self.divisions

        self.label_text_edit = ft.Text(self.label, size=11, weight=ft.FontWeight.BOLD, color=elem_color)
        self.slider_ctrl = ft.Slider(
            value=slider_val,
            min=s_min, max=s_max, divisions=s_div,
            active_color=elem_color,
            on_change=self._handle_change,
            expand=True,
        )
        self.val_text_edit = ft.Text(str(self.val), size=13, weight=ft.FontWeight.BOLD, width=35, text_align=ft.TextAlign.RIGHT)
        
        self.edit_view = ft.Container(
            content=ft.Row([
                self.label_text_edit,
                self.slider_ctrl,
                self.val_text_edit
            ], spacing=5),
            padding=ft.Padding(8, 0, 8, 0),
            alignment=ft.Alignment.CENTER,
            expand=True
        )

        # --- 使用 AnimatedSwitcher 实现无缝切换 ---
        self.switcher = ft.AnimatedSwitcher(
            content=self.edit_view if self.is_edit_mode else self.browse_view,
            transition=ft.AnimatedSwitcherTransition.FADE,
            duration=200,
            reverse_duration=100,
            switch_in_curve=ft.AnimationCurve.EASE_OUT,
        )

        # 容器属性设置
        self.content = self.switcher
        self.width = 220
        self.height = 45 # 严格锁定高度，防止布局抖动
        self.border_radius = 8
        self.bgcolor = ft.Colors.with_opacity(0.05, ft.Colors.WHITE) if self.is_edit_mode else ft.Colors.with_opacity(0.02, ft.Colors.WHITE)
        self.border = ft.Border.all(1, ft.Colors.with_opacity(0.2, elem_color)) if self.is_edit_mode else ft.Border.all(1, ft.Colors.with_opacity(0.05, ft.Colors.WHITE))
        self.on_click = self._toggle_edit_mode
        self.mouse_cursor = ft.MouseCursor.CLICK # 属性赋值方式
        
        # 增加提示感
        self.tooltip = f"Click to edit {self.label}"

    def _toggle_edit_mode(self, e):
        # 如果即将进入编辑态，先申请焦点
        if not self.is_edit_mode:
            if self.on_focus_callback:
                self.on_focus_callback(self) # 告诉父级：我要开始编辑了
        
        self.is_edit_mode = not self.is_edit_mode
        self._refresh_ui()

    def set_edit_mode(self, is_edit: bool):
        """外部控制接口：强制设定编辑态"""
        if self.is_edit_mode != is_edit:
            self.is_edit_mode = is_edit
            self._refresh_ui()

    def _refresh_ui(self):
        elem_color = GenshinTheme.get_element_color(self.element)
        # 更新背景与边框
        self.bgcolor = ft.Colors.with_opacity(0.08, ft.Colors.WHITE) if self.is_edit_mode else ft.Colors.with_opacity(0.02, ft.Colors.WHITE)
        self.border = ft.Border.all(1, ft.Colors.with_opacity(0.3, elem_color)) if self.is_edit_mode else ft.Border.all(1, ft.Colors.with_opacity(0.05, ft.Colors.WHITE))
        
        # 切换内容
        self.switcher.content = self.edit_view if self.is_edit_mode else self.browse_view
        
        try:
            self.update()
        except: pass

    def _handle_change(self, e):
        new_val = int(e.control.value)
        if self.discrete_values:
            self.val = self.discrete_values[new_val]
        else:
            self.val = new_val
            
        # 同步更新编辑态和浏览态的文本
        self.val_text_edit.value = str(self.val)
        self.val_text_browse.value = str(self.val)
        
        if self.on_change_callback:
            self.on_change_callback(self.val)
        
        # 实时更新内部文本显示
        try:
            self.val_text_edit.update()
        except: pass

    def update_state(self, new_val: int, element: str, skip_update: bool = False):
        self.val = new_val
        self.element = element
        self.is_edit_mode = False
        
        # 非破坏性更新：修改现有控件属性
        elem_color = GenshinTheme.get_element_color(self.element)
        
        self.val_text_browse.value = str(self.val)
        self.val_text_edit.value = str(self.val)
        self.label_text_edit.color = elem_color
        
        # 更新滑块位置
        slider_val = self.val
        if self.discrete_values:
            try: slider_val = self.discrete_values.index(self.val)
            except: slider_val = 0
        self.slider_ctrl.value = slider_val
        self.slider_ctrl.active_color = elem_color
        
        # 更新外观
        self.bgcolor = ft.Colors.with_opacity(0.02, ft.Colors.WHITE)
        self.border = ft.Border.all(1, ft.Colors.with_opacity(0.05, ft.Colors.WHITE))
        self.switcher.content = self.browse_view

        if not skip_update:
            try:
                self.update()
            except: pass
