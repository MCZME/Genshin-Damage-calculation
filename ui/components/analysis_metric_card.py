import flet as ft

class AnalysisMetricCard(ft.Container):
    """
    分析指标卡片组件 (原子化重构版)。
    展示关键数值指标（如总伤、DPS、时长）。
    """
    def __init__(self, label: str, value: str, color: str):
        super().__init__()
        self.label = label
        self.value = value
        self.theme_color = color
        
        self._build_ui()

    def _build_ui(self):
        self.content = ft.Column([
            ft.Text(self.label, size=10, weight=ft.FontWeight.W_600, color=ft.Colors.with_opacity(0.5, ft.Colors.WHITE)),
            ft.Text(self.value, size=24, weight=ft.FontWeight.W_900, color=self.theme_color),
        ], spacing=2)
        
        self.padding = ft.Padding(25, 20, 25, 20)
        self.bgcolor = ft.Colors.with_opacity(0.06, ft.Colors.WHITE)
        self.border = ft.Border.all(1, ft.Colors.with_opacity(0.08, ft.Colors.WHITE))
        self.border_radius = 15
        self.expand = True

    def update_value(self, new_value: str):
        self.value = new_value
        self._build_ui()
        try: self.update()
        except: pass
