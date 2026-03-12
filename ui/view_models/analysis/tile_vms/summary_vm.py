"""
[V9.2] 汇总统计 ViewModel

职责：
1. 从缓存获取汇总统计数据
2. 提供格式化的统计指标

重构说明：
- 使用统一签名 state: AnalysisState
- 通过 state.data_service 访问数据服务
"""
from __future__ import annotations

import flet as ft
from typing import TYPE_CHECKING, Any

from ui.services.ui_formatter import UIFormatter

if TYPE_CHECKING:
    from ui.states.analysis_state import AnalysisState


@ft.observable
class SummaryViewModel:
    """
    汇总统计 ViewModel - 从缓存获取汇总数据
    """

    def __init__(self, state: 'AnalysisState', instance_id: str):
        self.state = state
        self.instance_id = instance_id
        self.theme_color = "#D3BC8E"  # 琥珀金

    # ============================================================
    # 状态属性
    # ============================================================

    @property
    def loading(self) -> bool:
        """数据是否正在加载"""
        slot = self.state.data_service.get_cached("summary")
        return slot.loading if slot else True

    @property
    def has_data(self) -> bool:
        """是否有数据"""
        slot = self.state.data_service.get_cached("summary")
        return slot is not None and slot.data is not None

    # ============================================================
    # 数据属性
    # ============================================================

    @property
    def data(self) -> dict[str, Any]:
        """原始数据"""
        slot = self.state.data_service.get_cached("summary")
        return slot.data if slot and slot.data else {}

    @property
    def total_damage(self) -> str:
        """总伤害（格式化）"""
        return UIFormatter.format_metric_value(self.data.get("total_damage", 0))

    @property
    def avg_dps(self) -> str:
        """平均 DPS（格式化）"""
        return UIFormatter.format_metric_value(self.data.get("avg_dps", 0))

    @property
    def duration_seconds(self) -> str:
        """持续时间"""
        return f"{self.data.get('duration_seconds', 0):.1f}s"

    @property
    def peak_dps(self) -> str:
        """峰值 DPS（格式化）"""
        return UIFormatter.format_metric_value(self.data.get("peak_dps", 0))

    # ============================================================
    # 指标生成
    # ============================================================

    def get_metrics(self) -> list[dict[str, Any]]:
        """
        获取格式化的指标列表
        返回: [{"label": ..., "value": ..., "color": ..., "icon": ...}, ...]
        """
        return [
            {
                "label": "TOTAL DMG",
                "value": self.total_damage,
                "color": ft.Colors.AMBER_ACCENT_200,
                "icon": ft.Icons.AUTO_GRAPH_ROUNDED
            },
            {
                "label": "AVG DPS",
                "value": self.avg_dps,
                "color": self.theme_color,
                "icon": ft.Icons.TIMELINE_ROUNDED
            },
            {
                "label": "DURATION",
                "value": self.duration_seconds,
                "color": ft.Colors.LIGHT_BLUE_ACCENT_100,
                "icon": ft.Icons.TIMER_ROUNDED
            },
            {
                "label": "PEAK DMG",
                "value": self.peak_dps,
                "color": ft.Colors.RED_ACCENT_200,
                "icon": ft.Icons.BOLT_ROUNDED
            }
        ]
