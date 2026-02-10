import flet as ft
from ui.state import AppState
from ui.theme import GenshinTheme

class TargetPicker(ft.AlertDialog):
    """
    Flet V3 版目标选择器
    """
    def __init__(self, state: AppState, on_select: callable):
        super().__init__()
        self.state = state
        self.on_select = on_select
        
        self.title = ft.Text("选择打击目标", weight=ft.FontWeight.BOLD, color=GenshinTheme.ON_SURFACE)
        
        self.list_container = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=5
        )
        
        self.content = ft.Container(
            width=400,
            height=400,
            content=self.list_container
        )
        
        self._render_list()

    def _render_list(self):
        self.list_container.controls.clear()
        
        for name, info in self.state.target_map.items():
            self.list_container.controls.append(
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.PETS, color=ft.Colors.RED_ACCENT),
                    title=ft.Text(name, weight=ft.FontWeight.BOLD, color=GenshinTheme.ON_SURFACE),
                    subtitle=ft.Text(f"Lv.{info['level']}", size=11, color=GenshinTheme.TEXT_SECONDARY),
                    on_click=lambda _, n=name: self._handle_select(n)
                )
            )
        
        try: self.update()
        except: pass

    def _handle_select(self, target_name):
        self.on_select(target_name)
        self.open = False
        self.page.update()
