import flet as ft
import flet_charts as fch
from ui.theme import GenshinTheme
from ui.components.analysis.base_widget import AnalysisTile
from core.persistence.adapter import ReviewDataAdapter

class DPSChartTile(AnalysisTile):
    """
    磁贴：DPS 波动曲线。
    展示宏观伤害密度，支持点击下钻。
    """
    def __init__(self, on_drill_down=None):
        super().__init__("DPS 波动曲线", ft.Icons.AUTO_GRAPH)
        self.expand = True # 图表需要铺满空间
        self.on_drill_down = on_drill_down
        self.points_data = []
        self.chart = None

    def load_data(self, adapter: ReviewDataAdapter):
        # 此处本应调用 adapter.get_dps_data，暂时用 mock 或同步逻辑简化
        # 实际开发中会在 AnalysisState 中统一处理
        pass

    def _build_ui(self):
        # 骨架占位
        if not self.points_data:
            self.content = ft.Container(
                content=ft.Text("数据加载中...", size=12, opacity=0.3),
                alignment=ft.Alignment.CENTER
            )
            return

        chart_spots = [
            fch.LineChartDataPoint(p['frame'], p['value']) 
            for p in self.points_data
        ]

        self.chart = fch.LineChart(
            data_series=[
                fch.LineChartData(
                    points=chart_spots,
                    color=GenshinTheme.PRIMARY,
                    stroke_width=2,
                    curved=True,
                    below_line_bgcolor="rgba(209, 162, 255, 0.1)",
                )
            ],
            on_event=self._handle_event,
            interactive=True,
            expand=True
        )
        self.content = self.chart

    def _handle_event(self, e: fch.LineChartEvent):
        if e.type == "point_click" and self.on_drill_down:
            for spot in e.spots:
                if spot.spot_index != -1:
                    # 触发下钻
                    self.on_drill_down(self.points_data[spot.spot_index])

    def sync_to_frame(self, frame_id: int):
        # DPS 曲线通常作为全局背景，不需要随帧改变形态，
        # 但可以实现游标联动效果（后续扩展）
        pass

    def update_data(self, data):
        self.points_data = data
        self._build_ui()
        try: self.update()
        except: pass
