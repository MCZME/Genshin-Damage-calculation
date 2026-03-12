"""
[V9.2] 汇总统计磁贴组件

重构说明：
- 数据转换逻辑已迁移至 SummaryViewModel
- 组件仅负责 UI 渲染
- 使用统一签名 state: AnalysisState
"""
import flet as ft
from typing import TYPE_CHECKING

from ui.components.analysis.base_widget import AnalysisTile
from ui.view_models.analysis.tile_vms.summary_vm import SummaryViewModel

if TYPE_CHECKING:
    from ui.states.analysis_state import AnalysisState


class SummaryTile(AnalysisTile):
    """
    [V9.2] 全局战报看板
    规格: 2x1

    重构说明：
    - 数据转换逻辑已迁移至 SummaryViewModel
    - 组件仅负责 UI 渲染
    - 使用统一签名 state: AnalysisState
    """

    def __init__(self, state: 'AnalysisState'):
        super().__init__(
            "全局战报看板",
            ft.Icons.DASHBOARD_ROUNDED,
            "summary",
            state
        )
        self.expand = False
        self.theme_color = "#D3BC8E"
        self.gradient_top = "#2A2634"
        self._vm: SummaryViewModel | None = None

    def _get_vm(self) -> SummaryViewModel:
        """获取或创建 ViewModel"""
        if self._vm is None:
            self._vm = SummaryViewModel(
                state=self.state,
                instance_id=self.instance_id or "summary_unknown"
            )
        return self._vm

    @ft.component
    def render(self):
        vm = self._get_vm()
        slot = self.state.data_service.get_slot("summary")

        # 加载状态
        if not slot or slot.loading or slot.data is None:
            return ft.Container(
                content=ft.ProgressRing(width=20, height=20, color=self.theme_color),
                alignment=ft.Alignment.CENTER,
                expand=True
            )

        # 获取指标
        metrics = vm.get_metrics()

        def create_metric_box(
            label: str,
            value: str,
            color: str,
            icon: ft.IconData
        ) -> ft.Control:
            return ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(icon, size=14, color=ft.Colors.WHITE, opacity=0.4),
                        ft.Text(
                            label,
                            size=10,
                            weight=ft.FontWeight.W_600,
                            color=ft.Colors.WHITE,
                            opacity=0.5,
                            style=ft.TextStyle(letter_spacing=0.8)
                        ),
                    ], spacing=8),
                    ft.Text(
                        value,
                        size=22,
                        weight=ft.FontWeight.W_900,
                        color=color,
                        style=ft.TextStyle(letter_spacing=-0.5)
                    ),
                ], spacing=4, alignment=ft.MainAxisAlignment.CENTER),
                expand=True,
                alignment=ft.Alignment.CENTER_LEFT
            )

        # 2x2 布局在 (2, 1) 尺寸下会更加舒展
        return ft.Column([
            ft.Row([
                create_metric_box(
                    metrics[0]["label"],
                    metrics[0]["value"],
                    metrics[0]["color"],
                    metrics[0]["icon"]
                ),
                create_metric_box(
                    metrics[1]["label"],
                    metrics[1]["value"],
                    metrics[1]["color"],
                    metrics[1]["icon"]
                ),
            ], spacing=20, expand=True),
            ft.Row([
                create_metric_box(
                    metrics[2]["label"],
                    metrics[2]["value"],
                    metrics[2]["color"],
                    metrics[2]["icon"]
                ),
                create_metric_box(
                    metrics[3]["label"],
                    metrics[3]["value"],
                    metrics[3]["color"],
                    metrics[3]["icon"]
                ),
            ], spacing=20, expand=True),
        ], spacing=10, expand=True)
