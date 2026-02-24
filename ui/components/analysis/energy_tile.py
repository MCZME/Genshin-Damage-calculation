import flet as ft
import flet_charts as fch
from ui.theme import GenshinTheme
from ui.components.analysis.base_widget import AnalysisTile
from core.persistence.adapter import ReviewDataAdapter

class EnergyTile(AnalysisTile):
    """
    磁贴：能量水位监控。
    展示全队角色的能量随时间的变化曲线。
    """
    def __init__(self):
        super().__init__("能量回转监控", ft.Icons.BOLT_ROUNDED)
        self.expand = True # 曲线图需要铺满
        self.energy_data = {}
        self.chart = None

    def load_data(self, adapter: ReviewDataAdapter):
        pass

    def update_data(self, energy_data):
        self.energy_data = energy_data
        self._build_ui()

    def _build_ui(self):
        if not self.energy_data:
            self.content = ft.Container(
                content=ft.Text("无能量变化数据", size=12, opacity=0.3),
                alignment=ft.Alignment.CENTER
            )
            return

        series = []
        colors = [ft.Colors.AMBER, ft.Colors.BLUE, ft.Colors.PURPLE, ft.Colors.RED]
        
        for i, (name, points) in enumerate(self.energy_data.items()):
            chart_points = [fch.LineChartDataPoint(p[0], p[1]) for p in points]
            series.append(
                fch.LineChartData(
                    points=chart_points,
                    color=colors[i % len(colors)],
                    stroke_width=2,
                    curved=True,
                    # 可以添加 label 区分角色，但 LineChartLabel 的支持取决于 flet_charts 版本
                )
            )

        self.chart = fch.LineChart(
            data_series=series,
            interactive=True,
            expand=True,
            # 可以在这里添加轴标签等
        )
        
        self.content = ft.Column([
            ft.Row([
                ft.Container(bgcolor=colors[i % len(colors)], width=10, height=10, border_radius=5)
                for i in range(len(self.energy_data))
            ], spacing=10, alignment=ft.MainAxisAlignment.CENTER),
            self.chart
        ], expand=True)

    def sync_to_frame(self, frame_id: int):
        # 能量曲线也可以实现游标联动
        pass
