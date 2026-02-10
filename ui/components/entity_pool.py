import flet as ft
from ui.theme import GenshinTheme

class SelectorItem(ft.Container):
    """
    通用选择项组件 (角色/目标)
    """
    def __init__(self, title, subtitle, icon, color, is_selected, on_click, on_delete=None, is_compact=False, element_icon=None, is_target=False):
        super().__init__(
            height=68 if not is_compact else (80 if not is_target else 56),
            border_radius=12,
            padding=ft.padding.symmetric(horizontal=12 if not is_compact else 4, vertical=8),
            bgcolor="rgba(255, 255, 255, 0.08)" if is_selected else "transparent",
            border=ft.border.only(left=ft.BorderSide(4, color)) if (is_selected and not is_compact) else None,
            animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
            on_click=on_click,
            tooltip=title if is_compact else None,
        )
        
        circle_node = ft.Container(
            width=12 if (is_target and not is_compact) else 40, 
            height=12 if (is_target and not is_compact) else 40,
            bgcolor=color,
            border_radius=6 if (is_target and not is_compact) else 20,
            alignment=ft.Alignment.CENTER,
            shadow=ft.BoxShadow(blur_radius=8, color=color, spread_radius=-2) if is_selected else None,
            content=ft.Icon(icon, size=20, color=ft.Colors.WHITE) if not is_target else None
        )

        if is_target:
            if not is_compact:
                self.content = ft.Row([
                    ft.Container(width=10),
                    circle_node,
                    ft.Text(title, size=13, weight=ft.FontWeight.BOLD, color=GenshinTheme.ON_SURFACE),
                    ft.Text(subtitle, size=11, color=color, opacity=0.8, expand=True), 
                    ft.IconButton(ft.Icons.CLOSE, icon_size=14, opacity=0.4, on_click=on_delete) if on_delete else ft.Container()
                ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            else:
                circle_node.width = 40
                circle_node.height = 40
                circle_node.border_radius = 20
                self.content = ft.Container(content=circle_node, alignment=ft.Alignment.CENTER)
        else:
            if not is_compact:
                self.content = ft.Row([
                    circle_node,
                    ft.Column([
                        ft.Row([
                            ft.Text(title, size=14, weight=ft.FontWeight.BOLD, color=GenshinTheme.ON_SURFACE),
                            ft.Text(element_icon if isinstance(element_icon, str) else "", size=10, weight=ft.FontWeight.W_900, color=color)
                        ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Text(subtitle, size=11, color=GenshinTheme.TEXT_SECONDARY),
                    ], spacing=2, expand=True, alignment=ft.MainAxisAlignment.CENTER),
                    ft.IconButton(ft.Icons.CLOSE, icon_size=14, opacity=0.4, on_click=on_delete) if on_delete else ft.Container()
                ], spacing=12)
            else:
                self.content = ft.Column([
                    circle_node,
                    ft.Text(title, size=9, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS, opacity=0.8)
                ], spacing=4, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

class AddButton(ft.Container):
    """
    改进的添加按钮：支持在极简模式下铺满宽度
    """
    def __init__(self, label, on_click, icon=ft.Icons.ADD, is_compact=False):
        super().__init__(
            height=44,
            bgcolor="rgba(255, 255, 255, 0.02)",
            border=ft.border.all(1, ft.Colors.with_opacity(0.2, GenshinTheme.PRIMARY)),
            border_radius=12,
            on_click=on_click,
            tooltip=label if is_compact else None,
            # 在极简模式下，依然保持内容居中，但容器会由于 CrossAxisAlignment.STRETCH 铺满
            content=ft.Row([
                ft.Icon(icon, size=16, color=GenshinTheme.PRIMARY),
                ft.Text(label, size=11, weight=ft.FontWeight.BOLD, color=GenshinTheme.PRIMARY)
            ], alignment=ft.MainAxisAlignment.CENTER) if not is_compact else \
            ft.Container(
                content=ft.Icon(icon, size=20, color=GenshinTheme.PRIMARY),
                alignment=ft.Alignment.CENTER
            )
        )

class EntityPool(ft.Column):
    def __init__(self, state):
        # 核心设置：使用 STRETCH 确保所有子组件水平铺满
        super().__init__(
            expand=True, 
            spacing=15, 
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH
        )
        self.state = state
        self.is_compact = False 

    def did_mount(self): self.refresh()

    def refresh(self):
        self.controls.clear()
        
        # 1. TEAM SECTION
        if not self.is_compact:
            self.controls.append(ft.Row([ft.Text("队伍配置", size=10, weight=ft.FontWeight.W_900, opacity=0.4), ft.Text(f"{len([m for m in self.state.team if m])}/4", size=10, opacity=0.3)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))
        
        team_col = ft.Column(spacing=4, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
        for i, member in enumerate(self.state.team):
            if member is None: continue
            is_selected = (self.state.selection and self.state.selection.get("type") == "character" and self.state.selection.get("index") == i)
            char_info = member["character"]
            color = GenshinTheme.get_element_color(char_info["element"])
            team_col.controls.append(SelectorItem(
                title=char_info["name"], subtitle=f"Lv.{char_info['level']} {char_info['type']}", 
                icon=ft.Icons.PERSON, element_icon=char_info["element"], color=color, 
                is_selected=is_selected, is_compact=self.is_compact, is_target=False, 
                on_click=lambda _, idx=i: self.state.select_character(idx), 
                on_delete=lambda e, idx=i: self._safe_remove_char(e, idx)
            ))
            
        if len([m for m in self.state.team if m]) < 4:
            try: next_idx = self.state.team.index(None)
            except ValueError: next_idx = len(self.state.team)
            team_col.controls.append(AddButton("添加角色", lambda _: self.state.select_character(next_idx), icon=ft.Icons.PERSON_ADD, is_compact=self.is_compact))
        
        self.controls.append(team_col)
        self.controls.append(ft.Divider(height=1, color="rgba(255, 255, 255, 0.05)"))

        # 2. TARGET SECTION
        if not self.is_compact:
            self.controls.append(ft.Text("怪物目标", size=10, weight=ft.FontWeight.W_900, opacity=0.4))
            
        target_col = ft.Column(spacing=4, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
        for i, target in enumerate(self.state.targets):
            is_selected = (self.state.selection and self.state.selection.get("type") == "target" and self.state.selection.get("index") == i)
            target_col.controls.append(SelectorItem(
                title=target["name"], subtitle=f"Lv.{target['level']}", 
                icon=ft.Icons.GPS_FIXED, color=ft.Colors.RED_ACCENT, is_selected=is_selected, 
                is_compact=self.is_compact, is_target=True, 
                on_click=lambda _, idx=i: self.state.select_target(idx), 
                on_delete=lambda e, idx=i: self._safe_remove_target(e, idx)
            ))
        target_col.controls.append(AddButton("新建目标", lambda _: self.state.add_target(), icon=ft.Icons.ADD_LOCATION_ALT, is_compact=self.is_compact))
        self.controls.append(target_col)
        
        self.controls.append(ft.Divider(height=1, color="rgba(255, 255, 255, 0.05)"))

        # 3. ENVIRONMENT SECTION
        is_env_selected = (self.state.selection and self.state.selection.get("type") == "env")
        env_icon = ft.Icon(ft.Icons.CLOUD, size=18 if not self.is_compact else 20, color=ft.Colors.CYAN_200)
        
        self.controls.append(
            ft.Container(
                content=ft.Row([
                    env_icon, ft.Text("环境配置", size=11, weight=ft.FontWeight.BOLD, expand=True), 
                    ft.Icon(ft.Icons.CHEVRON_RIGHT, size=16, opacity=0.5)
                ]) if not self.is_compact else ft.Container(content=env_icon, alignment=ft.Alignment.CENTER), 
                padding=12 if not self.is_compact else 0, 
                height=44, 
                bgcolor="rgba(255, 255, 255, 0.1)" if is_env_selected else "rgba(255, 255, 255, 0.02)", 
                border_radius=12, 
                border=ft.border.all(1, ft.Colors.CYAN_200 if is_env_selected else "transparent"), 
                on_click=lambda _: self.state.select_environment()
            )
        )
        
        if self.page:
            try: self.update()
            except: pass

    def _safe_remove_char(self, e, idx):
        self.state.remove_character(idx)

    def _safe_remove_target(self, e, idx):
        self.state.remove_target(idx)
