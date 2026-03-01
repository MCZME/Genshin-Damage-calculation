import flet as ft
import asyncio
from ui.states.analysis_state import AnalysisState
from ui.theme import GenshinTheme
from ui.services.ui_formatter import UIFormatter
from ui.components.analysis.base_widget import AnalysisTile

class SummaryTile(AnalysisTile):
    """
    磁贴：全局战报看板 (V5.1 Pro 适配版)
    """
    def __init__(self, state: AnalysisState):
        super().__init__("全局战报看板", ft.Icons.DASHBOARD_ROUNDED, "summary", state)
        self.expand = False
        # V4.5 Pro 视觉属性
        self.theme_color = "#D3BC8E" # 琥珀金
        self.gradient_top = "#2A2634" # 深紫过渡

    @ft.component
    def render(self):
        # 1. 获取中心化数据槽位
        slot = self.state.data_manager.get_slot("summary")
        
        if not slot or slot.loading or slot.data is None:
            return ft.Container(
                content=ft.ProgressRing(width=20, height=20, color=self.theme_color), 
                alignment=ft.Alignment.CENTER, 
                expand=True
            )

        d = slot.data

        def create_metric_box(label, value, color, icon):
            return ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(icon, size=14, color=ft.Colors.WHITE, opacity=0.4),
                        ft.Text(label, size=10, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE, opacity=0.5, style=ft.TextStyle(letter_spacing=0.8)),
                    ], spacing=8),
                    ft.Text(value, size=22, weight=ft.FontWeight.W_900, color=color, style=ft.TextStyle(letter_spacing=-0.5)),
                ], spacing=4, alignment=ft.MainAxisAlignment.CENTER),
                expand=True,
                alignment=ft.Alignment.CENTER_LEFT
            )

        # 2x2 布局在 (2, 1) 尺寸下会更加舒展
        return ft.Column([
            ft.Row([
                create_metric_box("TOTAL DMG", UIFormatter.format_metric_value(d.get("total_damage", 0)), ft.Colors.AMBER_ACCENT_200, ft.Icons.AUTO_GRAPH_ROUNDED),
                create_metric_box("AVG DPS", UIFormatter.format_metric_value(d.get("avg_dps", 0)), self.theme_color, ft.Icons.TIMELINE_ROUNDED),
            ], spacing=20, expand=True),
            ft.Row([
                create_metric_box("DURATION", f"{d.get('duration_seconds', 0):.1f}s", ft.Colors.LIGHT_BLUE_ACCENT_100, ft.Icons.TIMER_ROUNDED),
                create_metric_box("PEAK DMG", UIFormatter.format_metric_value(d.get("peak_dps", 0)), ft.Colors.RED_ACCENT_200, ft.Icons.BOLT_ROUNDED),
            ], spacing=20, expand=True),
        ], spacing=10, expand=True)

    def sync_to_frame(self, frame_id: int):
        pass # 汇总数据不随帧同步变动
