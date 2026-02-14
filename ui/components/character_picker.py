import flet as ft
from ui.state import AppState
from ui.theme import GenshinTheme

class CharacterPicker(ft.AlertDialog):
    """
    Flet V3 版角色选择器
    """
    def __init__(self, state: AppState, on_select: callable):
        super().__init__()
        self.state = state
        self.on_select = on_select
        
        # UI 组件
        self.title = ft.Text("选择角色", weight=ft.FontWeight.BOLD, color=GenshinTheme.ON_SURFACE)
        self.search_field = ft.TextField(
            label="搜索角色名称...",
            prefix_icon=ft.Icons.SEARCH,
            on_change=self._filter_list,
            dense=True,
            bgcolor="rgba(255, 255, 255, 0.05)",
            border_color="rgba(255, 255, 255, 0.1)",
        )
        
        self.list_container = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=5
        )
        
        self.content = ft.Container(
            width=400,
            height=500,
            content=ft.Column([
                self.search_field,
                ft.Divider(height=20, color="transparent"),
                self.list_container
            ])
        )
        
        self._render_list()

    def _render_list(self, query=""):
        self.list_container.controls.clear()
        
        # 遍历 state 中的角色数据
        for name, info in self.state.char_map.items():
            if query.lower() not in name.lower():
                continue
                
            # 获取元素对应颜色
            accent_color = GenshinTheme.get_element_color(info["element"])
            
            self.list_container.controls.append(
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.PERSON, color=accent_color),
                    title=ft.Text(name, weight=ft.FontWeight.BOLD, color=GenshinTheme.ON_SURFACE),
                    subtitle=ft.Text(f"{info['element']} | {info['type']}", size=11, color=GenshinTheme.TEXT_SECONDARY),
                    on_click=lambda _, n=name: self._handle_select(n)
                )
            )
        
        if not self.list_container.controls:
            self.list_container.controls.append(
                ft.Text("未找到匹配角色", italic=True, opacity=0.4, color=GenshinTheme.ON_SURFACE)
            )
            
        try:
            self.update()
        except:
            pass

    def _filter_list(self, e):
        self._render_list(e.control.value)

    def _handle_select(self, char_name):
        self.on_select(char_name)
        self.page.pop_dialog()
