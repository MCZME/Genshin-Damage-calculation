"""
[V9.2] DPS 图表磁贴组件

重构说明：
- 数据转换逻辑已迁移至 DPSChartViewModel
- 组件仅负责 UI 渲染
- 使用统一签名 state: AnalysisState
"""
import flet as ft
import flet_charts as fch
from typing import TYPE_CHECKING, Callable, Any

from ui.components.analysis.base_widget import AnalysisTile
from ui.view_models.analysis.tile_vms.dps_vm import DPSChartViewModel

if TYPE_CHECKING:
    from ui.states.analysis_state import AnalysisState


class DPSChartTile(AnalysisTile):
    """
    [V9.2] 专业级 DPS 曲线组件
    支持：多轨堆叠、实时游标、区间缩放

    重构说明：
    - 数据转换逻辑已迁移至 DPSChartViewModel
    - 组件仅负责 UI 渲染
    - 使用统一签名 state: AnalysisState
    """

    def __init__(
        self,
        state: 'AnalysisState',
        on_drill_down: Callable[[dict[str, Any]], None] | None = None
    ):
        super().__init__(
            "实时秒伤曲线",
            ft.Icons.SHOW_CHART_ROUNDED,
            "dps",
            state
        )
        self.on_drill_down = on_drill_down
        self.expand = True
        self.canvas_height = 220
        self.theme_color = "#FFD700"
        self.gradient_top = "#2A2418"
        self._vm: DPSChartViewModel | None = None

    def _get_vm(self) -> DPSChartViewModel:
        """获取或创建 ViewModel"""
        if self._vm is None:
            self._vm = DPSChartViewModel(
                state=self.state,
                instance_id=self.instance_id or "dps_unknown",
                on_drill_down=self.on_drill_down
            )
        return self._vm

    def render(self):
        """核心渲染：使用 ViewModel 提供的数据"""
        vm = self._get_vm()

        # 检查数据状态
        slot = self.state.data_service.get_slot("dps")
        if not slot or slot.data is None:
            return ft.Container(
                content=ft.ProgressRing(color=self.theme_color),
                alignment=ft.Alignment.CENTER,
                expand=True
            )

        # 获取图表数据
        chart_data = vm.chart_data
        total_frames = vm.total_frames

        return ft.Container(
            content=fch.LineChart(
                data_series=chart_data,
                border=ft.Border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
                horizontal_grid_lines=fch.ChartGridLines(
                    interval=10000,
                    width=0.5,
                    color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE)
                ),
                vertical_grid_lines=fch.ChartGridLines(
                    interval=60,
                    width=0.5,
                    color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE)
                ),
                left_axis=fch.ChartAxis(
                    labels_size=40,
                    title=ft.Text("DPS", size=10, weight=ft.FontWeight.BOLD),
                    title_size=20,
                ),
                bottom_axis=fch.ChartAxis(
                    labels_size=20,
                    title=ft.Text("Time (s)", size=10, weight=ft.FontWeight.BOLD),
                    title_size=20,
                ),
                tooltip_bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.BLACK),
                min_y=0,
                max_y=vm.max_y,
                min_x=0,
                max_x=total_frames,
                expand=True,
                animate=False,
                on_chart_event=vm.handle_chart_event
            ),
            padding=ft.Padding(10, 10, 10, 0),
            expand=True
        )
