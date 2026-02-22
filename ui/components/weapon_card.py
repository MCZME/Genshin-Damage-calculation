import flet as ft
from ui.theme import GenshinTheme

class WeaponCard(ft.Container):
    """
    一体化武器配置卡组件 (原子化重构版)。
    集成武器图标预览、等级与精炼的滑块控制。
    """
    def __init__(
        self, 
        member: dict, 
        slider_factory, # 外部传入的带焦点管理的滑块工厂
        on_picker_click = None,
        on_stat_change = None # callback(key, val)
    ):
        super().__init__()
        self.member = member
        self.slider_factory = slider_factory
        self.on_picker_click = on_picker_click
        self.on_stat_change = on_stat_change
        
        self._build_ui()

    def _build_ui(self):
        w = self.member.get('weapon', {"id": None, "level": "90", "refinement": "1"})
        is_empty = w.get('id') is None
        
        # 武器图标预览
        weapon_type = self.member.get('type', '单手剑')
        weapon_icon = GenshinTheme.get_weapon_icon(weapon_type)
        
        weapon_icon_container = ft.Container(
            content=ft.Icon(ft.Icons.SHIELD if is_empty else weapon_icon, size=30, color=ft.Colors.WHITE_24),
            width=80, height=80,
            bgcolor=ft.Colors.BLACK26,
            border_radius=8,
            border=ft.Border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
            alignment=ft.Alignment.CENTER,
            on_click=lambda _: self.on_picker_click() if self.on_picker_click else None
        )
        weapon_icon_container.mouse_cursor = ft.MouseCursor.CLICK
        
        # 组装 Row
        controls_row = ft.Row([
            weapon_icon_container,
            # 武器参数
            ft.Column([
                ft.Text(w['id'].upper() if not is_empty else "未装备武器", size=12, weight=ft.FontWeight.BOLD),
                self.slider_factory(
                    "精炼", value=int(w['refinement']), min_val=1, max_val=5, divisions=4, 
                    element=self.member['element'], 
                    on_change=lambda v: self.on_stat_change("refinement", str(v)) if self.on_stat_change else None
                ),
                self.slider_factory(
                    "等级", value=int(w['level']), discrete_values=[1, 20, 40, 50, 60, 70, 80, 90], 
                    element=self.member['element'], 
                    on_change=lambda v: self.on_stat_change("level", str(v)) if self.on_stat_change else None
                ),
            ], spacing=5)
        ], spacing=15)
        
        self.content = ft.Column([
            ft.Text("武器装备", size=14, weight=ft.FontWeight.BOLD, opacity=0.6),
            controls_row
        ], spacing=10)
        
        self.padding = ft.Padding(20, 15, 20, 15)
        self.bgcolor = ft.Colors.with_opacity(0.02, ft.Colors.WHITE)
        self.border = ft.Border.all(1, ft.Colors.with_opacity(0.05, ft.Colors.WHITE))
        self.border_radius = 12
        self.width = 380

    def update_state(self, member: dict):
        """同步武器状态"""
        self.member = member
        self._build_ui()
        try: self.update()
        except: pass
