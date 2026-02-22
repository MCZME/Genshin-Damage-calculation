import flet as ft
from ui.theme import GenshinTheme
from ui.reboot.components.stat_input import StatInputField

class TargetSlot(ft.Container):
    """
    目标配置卡片 (Target Configuration Slot)。
    展示怪物基本信息及全元素抗性编辑。
    """
    def __init__(
        self,
        data: dict, # StrategicState 中的 target_data
        on_change=None,
        on_pick=None
    ):
        super().__init__()
        self.data = data
        self.on_change_callback = on_change
        self.on_pick_callback = on_pick
        self.element = "Neutral" # 目标色调默认为中性
        
        self._build_ui()

    def _build_ui(self):
        elem_color = GenshinTheme.get_element_color(self.element)
        
        # 1. 顶部：资产头部 (怪物名称与等级)
        self.header = ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text(self.data.get('name', "未选择目标"), size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Text("点击切换怪物类型", size=10, color=GenshinTheme.TEXT_SECONDARY),
                ], spacing=2, expand=True),
                ft.Container(
                    content=ft.Text(f"Lv.{self.data['level']}", size=12, weight=ft.FontWeight.W_900),
                    padding=ft.Padding(8, 4, 8, 4),
                    bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.BLACK),
                    border_radius=4,
                    on_click=lambda _: None # 预留等级修改滑块
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.Padding(15, 12, 15, 12),
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
            border_radius=8,
            on_click=self._handle_pick
        )

        # 2. 抗性配置网格 (Resistances)
        # 将抗性分为两列展示
        res_keys = list(self.data['resists'].keys())
        res_controls = []
        for k in res_keys:
            res_controls.append(
                StatInputField(
                    label=k,
                    value=self.data['resists'][k],
                    suffix="%",
                    element="Neutral",
                    width=135,
                    on_change=lambda v, key=k: self._handle_res_change(key, v)
                )
            )

        self.res_grid = ft.Column([
            ft.Text("元素/物理抗性 (%)", size=11, weight=ft.FontWeight.BOLD, color=GenshinTheme.TEXT_SECONDARY),
            ft.ResponsiveRow([
                ft.Column([res_controls[i] for i in range(0, 4)], col={"sm": 6}, spacing=5),
                ft.Column([res_controls[i] for i in range(4, 8)], col={"sm": 6}, spacing=5),
            ], spacing=10)
        ], spacing=8)

        # 3. 组装内容
        self.content = ft.Column([
            self.header,
            ft.Divider(height=1, color=ft.Colors.WHITE_10),
            self.res_grid
        ], spacing=12)
        
        # 样式
        self.padding = ft.Padding(15, 15, 15, 15)
        self.bgcolor = GenshinTheme.SURFACE_VARIANT
        self.border_radius = 12
        self.border = ft.Border.all(1, ft.Colors.with_opacity(0.1, GenshinTheme.ON_SURFACE))
        self.width = 320 # 相比圣遗物稍宽一些
        self.mouse_cursor = ft.MouseCursor.BASIC

    def _handle_res_change(self, key, value):
        self.data['resists'][key] = value
        if self.on_change_callback:
            self.on_change_callback()

    def _handle_pick(self, e):
        if self.on_pick_callback:
            self.on_pick_callback()

    def refresh(self):
        self._build_ui()
        try: self.update()
        except: pass
