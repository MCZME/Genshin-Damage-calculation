import flet as ft
from ui.theme import GenshinTheme
from core.registry import CharacterClassMap

class ActionInspector(ft.Container):
    """
    战术阶段右栏：动态指令检视器 (防闪烁优化版)
    """
    def __init__(self, state):
        super().__init__(expand=True)
        self.state = state
        self.is_compact = False
        
        # 1. 预置各个状态的容器
        self.empty_view = self._build_empty_view()
        self.compact_view = self._build_compact_view()
        self.content_view = ft.Column(spacing=20, scroll=ft.ScrollMode.AUTO, visible=False)
        
        # 2. 内部具体组件引用
        self.header_title = ft.Text("指令参数配置", size=14, weight=ft.FontWeight.BOLD)
        self.char_name_text = ft.Text("", size=16, weight=ft.FontWeight.W_900)
        self.action_label_text = ft.Text("", size=11, opacity=0.6)
        self.custom_params_col = ft.Column(spacing=12)
        self.custom_params_section = ft.Column([
            ft.Text("专属参数", size=10, weight=ft.FontWeight.BOLD, opacity=0.4),
            self.custom_params_col
        ], spacing=12, visible=False)

        # 3. 组装 Content View
        self.content_view.controls = [
            ft.Row([ft.Icon(ft.Icons.EDIT_NOTE, color=GenshinTheme.PRIMARY), self.header_title], spacing=10),
            ft.Divider(height=1, color="rgba(255,255,255,0.05)"),
            ft.Container(
                content=ft.Column([self.char_name_text, self.action_label_text], spacing=2),
                padding=16, bgcolor="rgba(255,255,255,0.02)", border_radius=12
            ),
            self.custom_params_section,
            ft.Container(key="no_params_hint", content=ft.Text("此动作无需额外参数", size=12, italic=True, opacity=0.3), visible=False)
        ]

        self.content = ft.Stack([
            self.empty_view,
            self.compact_view,
            self.content_view
        ], expand=True)

    def _build_empty_view(self):
        return ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.EDIT_NOTE, size=48, opacity=0.1),
                ft.Text("选择一个动作指令\n进行详细参数配置", text_align=ft.TextAlign.CENTER, size=12, italic=True, opacity=0.3)
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            expand=True, alignment=ft.Alignment.CENTER, visible=True
        )

    def _build_compact_view(self):
        return ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.TUNE, color=GenshinTheme.PRIMARY, size=20),
                ft.Text("INSPECTOR", size=9, rotate=ft.Rotate(1.57), weight=ft.FontWeight.W_900, opacity=0.3)
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
            alignment=ft.Alignment.CENTER, expand=True, visible=False
        )

    def did_mount(self): self.refresh()

    def refresh(self):
        try:
            if not self.page: return
        except: return

        # 控制主要视图显示
        self.compact_view.visible = self.is_compact
        self.empty_view.visible = not self.is_compact and (self.state.selected_action_index is None or self.state.selected_action_index >= len(self.state.action_sequence))
        self.content_view.visible = not self.is_compact and not self.empty_view.visible

        if self.content_view.visible:
            self._update_inspector_data()
            
        try: self.update()
        except: pass

    def _update_inspector_data(self):
        idx = self.state.selected_action_index
        action_entry = self.state.action_sequence[idx]
        char_name = action_entry["char_name"]
        action_id = action_entry["action_id"]
        
        if "params" not in action_entry: action_entry["params"] = {}
        p_values = action_entry["params"]

        # 1. 获取角色元数据
        char_cls = CharacterClassMap.get(char_name)
        color = GenshinTheme.get_element_color("Neutral")
        action_label = action_id.upper()
        params_def = []

        if char_cls:
            member = next((m for m in self.state.team if m and m["character"]["name"] == char_name), None)
            if member: color = GenshinTheme.get_element_color(member["character"]["element"])
            
            if hasattr(char_cls, "get_action_metadata"):
                meta = char_cls.get_action_metadata()
                mapped_id = action_id
                if action_id == "skill": mapped_id = "elemental_skill"
                elif action_id == "burst": mapped_id = "elemental_burst"
                elif action_id == "normal": mapped_id = "normal_attack"
                
                action_meta = meta.get(mapped_id, {})
                action_label = action_meta.get("label", action_label)
                params_def = action_meta.get("params", [])

        # 2. 更新静态文本
        self.char_name_text.value = char_name
        self.char_name_text.color = color
        self.action_label_text.value = action_label
        self.content_view.controls[0].controls[0].color = color # 图标颜色

        # 3. 更新动态参数列
        self.custom_params_col.controls.clear()
        if params_def:
            for d in params_def:
                ctrl = self._build_dynamic_control(d, p_values)
                if ctrl: self.custom_params_col.controls.append(ctrl)
            self.custom_params_section.visible = True
            self.content_view.controls[4].visible = False
        else:
            self.custom_params_section.visible = False
            self.content_view.controls[4].visible = True

    def _build_dynamic_control(self, d, p_values):
        key = d["key"]; label = d["label"]; p_type = d.get("type", "text"); default = d.get("default")
        if key not in p_values: p_values[key] = default

        if p_type == "select":
            options_map = d.get("options", {})
            return ft.Dropdown(
                label=label, value=str(p_values[key]), dense=True,
                options=[ft.dropdown.Option(key=str(k), text=str(v)) for k, v in options_map.items()],
                on_select=lambda e: self._update_param(p_values, key, e.control.value)
            )
        elif p_type == "number":
            return ft.TextField(
                label=label, value=str(p_values[key]), dense=True,
                on_change=lambda e: self._update_param(p_values, key, e.control.value, is_num=True),
                on_blur=lambda _: self.state.refresh(),
                input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9\.]", replacement_string="")
            )
        elif p_type == "bool":
            return ft.Switch(label=label, value=bool(p_values[key]), on_change=lambda e: self._update_param(p_values, key, e.control.value))
        return None

    def _update_param(self, params_dict, key, value, is_num=False):
        if is_num:
            try: params_dict[key] = float(value) if "." in str(value) else int(value)
            except: pass
        else:
            params_dict[key] = value
        if not is_num: self.state.refresh()
