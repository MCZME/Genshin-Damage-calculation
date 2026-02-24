import flet as ft
from ui.theme import GenshinTheme
from ui.services.ui_formatter import UIFormatter
from ui.components.analysis.base_widget import AnalysisTile
from core.persistence.adapter import ReviewDataAdapter

class SummaryTile(AnalysisTile):
    """
    磁贴：全局战报看板。
    展示总伤害、平均 DPS、战斗时长等核心指标。
    """
    def __init__(self):
        super().__init__("全局战报看板", ft.Icons.DASHBOARD_ROUNDED)
        self.expand = False
        self.summary_data = {
            "total_dmg": 0,
            "avg_dps": 0,
            "duration": 0,
            "peak_dps": 0
        }

    def load_data(self, adapter: ReviewDataAdapter):
        pass # 由 AnalysisState 统一分发

    def _build_ui(self):
        def create_metric(label, value, color):
            return ft.Column([
                ft.Text(label, size=10, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE24),
                ft.Text(value, size=20, weight=ft.FontWeight.W_900, color=color),
            ], spacing=2, expand=True)

        self.content = ft.Row([
            create_metric("总伤害输出", UIFormatter.format_metric_value(self.summary_data['total_dmg']), ft.Colors.AMBER_400),
            create_metric("平均 DPS", UIFormatter.format_metric_value(self.summary_data['avg_dps']), GenshinTheme.PRIMARY),
            create_metric("战斗时长", f"{self.summary_data['duration']:.1f}s", ft.Colors.BLUE_200),
            create_metric("峰值 DPS", UIFormatter.format_metric_value(self.summary_data['peak_dps']), ft.Colors.RED_400),
        ], spacing=20, alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    def sync_to_frame(self, frame_id: int):
        pass # 静态汇总不随帧变动

    def update_data(self, data):
        self.summary_data = data
        self._build_ui()
        try: self.update()
        except: pass
