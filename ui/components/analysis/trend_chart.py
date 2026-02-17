import flet as ft
import flet_charts as fch
from ui.components.analysis.base_widget import BaseAnalysisWidget
from ui.theme import GenshinTheme

class TrendChartWidget(BaseAnalysisWidget):
    """
    伤害趋势曲线组件 (V3.2)
    展示全场 DPS 或单人伤害趋势。
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._setup_chart()

    def _setup_chart(self):
        # 1. 定义数据序列 (Series)
        self.data_points = []
        self.indicator_series = fch.LineChartData(
            points=[fch.LineChartDataPoint(0, 0), fch.LineChartDataPoint(0, 1)],
            color=GenshinTheme.PRIMARY,
            stroke_width=2,
        )

        # 2. 构造 LineChart
        self.chart = fch.LineChart(
            data_series=[self.indicator_series],
            border=ft.Border.all(1, "rgba(255,255,255,0.05)"),
            horizontal_grid_lines=fch.ChartGridLines(interval=10000, color="rgba(255,255,255,0.02)"),
            vertical_grid_lines=fch.ChartGridLines(interval=60, color="rgba(255,255,255,0.02)"),
            left_axis=fch.ChartAxis(
                labels=[fch.ChartAxisLabel(value=0, label=ft.Text("0", size=9))],
                label_size=40,
            ),
            bottom_axis=fch.ChartAxis(
                labels=[fch.ChartAxisLabel(value=0, label=ft.Text("0", size=9))],
                label_size=30,
            ),
            expand=True,
            interactive=True,
            min_y=0,
            min_x=0,
        )

        # 3. 放入 BaseWidget 的 body 中
        self.body.content = self.chart
        self.body.expand = True

    async def load_data(self):
        """加载全量伤害趋势数据 (真实数据强化版)"""
        if not self.adapter: return
        
        raw_data = await self.adapter.get_dps_data()
        if not raw_data:
            self.update_subtitle("(无伤害记录)")
            return

        # 数据聚合
        frame_damage = {}
        for d in raw_data:
            f = d["frame"]
            frame_damage[f] = frame_damage.get(f, 0) + d["value"]
        
        sorted_frames = sorted(frame_damage.keys())
        self.data_points = [
            fch.LineChartDataPoint(float(f), float(frame_damage[f])) 
            for f in sorted_frames
        ]
        
        # 3. 创建主趋势序列
        self.trend_series = fch.LineChartData(
            points=self.data_points,
            stroke_width=2,
            color=GenshinTheme.PRIMARY,
            curved=False, # 优先保证基础线条渲染
        )
        
        # 4. 动态范围
        max_val = max(frame_damage.values()) if frame_damage else 1000
        max_f = max(sorted_frames) if sorted_frames else 600
        
        self.chart.max_y = float(max_val * 1.2)
        self.chart.max_x = float(max_f + 60)
        
        # 更新刻度
        self.chart.left_axis.labels = [
            fch.ChartAxisLabel(value=0, label=ft.Text("0", size=9, opacity=0.5)),
            fch.ChartAxisLabel(value=max_val, label=ft.Text(f"{max_val/10000:.1f}w", size=9, opacity=0.5)),
        ]
        
        # 5. 更新数据并重绘
        self.chart.data_series = [self.trend_series, self.indicator_series]
        self.update_subtitle(f"(全队 DPS 趋势 - {len(self.data_points)} 点)")
        
        try:
            self.chart.update()
            self.update()
        except:
            pass

    async def sync_frame(self, frame_id: int):
        """同步时间扫描线"""
        await super().sync_frame(frame_id)
        
        # 移动垂直扫描线
        self.indicator_series.points = [
            fch.LineChartDataPoint(float(frame_id), 0.0),
            fch.LineChartDataPoint(float(frame_id), float(self.chart.max_y or 1000.0))
        ]
        
        try:
            self.chart.update()
        except: pass

    def get_settings_items(self):
        return [
            ft.PopupMenuItem(content=ft.Text("观测: 全队总伤"), on_click=lambda _: self.update_subtitle("(全队总伤)")),
            ft.PopupMenuItem(content=ft.Text("观测: 当前活跃角色"), on_click=lambda _: self.update_subtitle("(活跃角色)")),
            ft.Divider(),
            ft.PopupMenuItem(content=ft.Text("导出数据 (.csv)")),
        ]
