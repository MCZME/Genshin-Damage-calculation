import flet as ft
from ui.theme import GenshinTheme

class ActionLibrary(ft.Column):
    """
    战术阶段左栏：可用动作库 (高辨识度精修版)
    """
    ACTION_META = {
        "normal": ("普通攻击", "普"),
        "charged": ("重击", "重"),
        "skill": ("元素战技", "战"),
        "burst": ("元素爆发", "爆"),
        "plunging": ("下落攻击", "下"),
        "dash": ("冲刺", "冲"),
        "jump": ("跳跃", "跳")
    }

    def __init__(self, state):
        super().__init__(expand=True, spacing=24, scroll=ft.ScrollMode.AUTO)
        self.state = state
        self.is_compact = False 

    def did_mount(self): self.refresh()

    def refresh(self):
        try:
            if not self.page: return
        except: return

        self.controls.clear()
        active_members = [m for m in self.state.team if m is not None]
        
        if not active_members:
            self.controls.append(ft.Text("请先添加角色", italic=True, opacity=0.3))
        else:
            if not self.is_compact:
                self.controls.append(ft.Text("可用动作库", size=10, weight=ft.FontWeight.W_900, opacity=0.4))
            
            for i, member in enumerate(active_members):
                char = member["character"]
                color = GenshinTheme.get_element_color(char["element"])
                self.controls.append(self._build_character_group(char, color))
                if not self.is_compact and i < len(active_members) - 1:
                    self.controls.append(ft.Divider(height=1, color="rgba(255,255,255,0.05)"))
            
        try: self.update()
        except: pass

    def _build_character_group(self, char, color):
        char_name = char["name"]
        if not self.is_compact:
            return ft.Column([
                # 角色标题
                ft.Row([
                    ft.Container(width=10, height=10, bgcolor=color, border_radius=5),
                    ft.Text(char_name, size=13, weight=ft.FontWeight.BOLD, color=GenshinTheme.ON_SURFACE),
                ], spacing=10),
                # 动作按钮流 (Wrap 布局)
                ft.Row([
                    self._build_action_button(char_name, act_id, color)
                    for act_id in self.ACTION_META.keys()
                ], wrap=True, spacing=10, run_spacing=10)
            ], spacing=12)
        else:
            # 极简模式：圆形头像
            return ft.Container(
                content=ft.Icon(ft.Icons.PERSON, color=ft.Colors.WHITE, size=20),
                width=48, height=48, bgcolor=color, border_radius=24,
                alignment=ft.Alignment.CENTER, tooltip=char_name,
                shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.3, color))
            )

    def _build_action_button(self, char_name, act_id, color):
        """构建与时间轴风格对齐的添加按钮"""
        full_label, first_char = self.ACTION_META[act_id]
        
        return ft.Container(
            content=ft.Row([
                # 强化首字
                ft.Text(first_char, size=16, weight=ft.FontWeight.W_900, color=color),
                ft.Text(full_label[1:], size=11, weight=ft.FontWeight.BOLD, opacity=0.8),
            ], spacing=4, tight=True),
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            bgcolor="rgba(255, 255, 255, 0.03)",
            border_radius=10,
            on_click=lambda _: self._add_to_sequence(char_name, act_id),
            on_hover=lambda e: self._handle_hover(e, color),
            animate=ft.Animation(200, ft.AnimationCurve.DECELERATE),
        )

    def _handle_hover(self, e, color):
        if e.data == "true":
            e.control.bgcolor = ft.Colors.with_opacity(0.15, color)
            e.control.scale = 1.05
        else:
            e.control.bgcolor = "rgba(255, 255, 255, 0.03)"
            e.control.scale = 1.0
        e.control.update()

    def _add_to_sequence(self, char_name, act_id):
        self.state.action_sequence.append({
            "char_name": char_name, "action_id": act_id, "params": {}
        })
        self.state.refresh()
