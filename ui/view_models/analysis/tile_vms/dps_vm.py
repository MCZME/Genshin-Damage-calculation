"""
[V9.1] DPS 图表 ViewModel

职责：
1. 从缓存获取 DPS 数据
2. 将原始数据转换为图表格式
3. 提供图表交互所需的数据
"""
from __future__ import annotations

import flet as ft
import flet_charts as fch
import bisect
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from ui.services.analysis_data_service import AnalysisDataService


@ft.observable
class DPSChartViewModel:
    """
    DPS 图表 ViewModel - 从缓存获取数据并转换为图表格式
    """

    def __init__(
        self,
        data_service: 'AnalysisDataService',
        instance_id: str,
        on_drill_down: Callable[[dict[str, Any]], None] | None = None
    ):
        self.data_service = data_service
        self.instance_id = instance_id
        self.on_drill_down = on_drill_down
        self.theme_color = "#FFD700"

    # ============================================================
    # 状态属性
    # ============================================================

    @property
    def loading(self) -> bool:
        """数据是否正在加载"""
        slot = self.data_service.get_cached("dps")
        return slot.loading if slot else True

    @property
    def has_data(self) -> bool:
        """是否有数据"""
        slot = self.data_service.get_cached("dps")
        return slot is not None and slot.data is not None

    @property
    def total_frames(self) -> int:
        """总帧数 (V9.2: 直接访问 vm)"""
        return max(self.data_service.vm.total_frames, 1)

    # ============================================================
    # 数据转换
    # ============================================================

    @property
    def chart_data(self) -> list[fch.LineChartData]:
        """缓存数据 → 图表格式"""
        slot = self.data_service.get_cached("dps")
        if not slot or not slot.data:
            return []

        stacked_points = slot.data.get("stacked_points", [])
        if not stacked_points:
            return []

        return [
            fch.LineChartData(
                data_points=[
                    fch.LineChartDataPoint(p['x'], p['y'])
                    for p in stacked_points
                ],
                stroke_width=2,
                color=self.theme_color,
                curved=True,
                stroke_cap_round=True,
                below_line_bgcolor=ft.Colors.with_opacity(0.1, self.theme_color),
                below_line_area_stops=[0.0, 1.0],
                below_line_area_colors=[
                    ft.Colors.with_opacity(0.3, self.theme_color),
                    ft.Colors.with_opacity(0.0, self.theme_color)
                ]
            )
        ]

    @property
    def max_y(self) -> float:
        """Y 轴最大值"""
        slot = self.data_service.get_cached("dps")
        if not slot or not slot.data:
            return 100

        stacked_points = slot.data.get("stacked_points", [])
        if not stacked_points:
            return 100

        return max([p['y'] for p in stacked_points]) * 1.1

    # ============================================================
    # 交互处理
    # ============================================================

    def handle_chart_event(self, e: fch.LineChartEvent) -> None:
        """处理图表交互事件"""
        slot = self.data_service.get_cached("dps")
        if not slot or not slot.data:
            return

        raw_events = slot.data.get("raw_events", [])
        frame_indices = slot.data.get("frame_indices", [])

        if e.event_type == "click" and e.x is not None:
            clicked_frame = int(e.x)
            self.data_service.state.set_frame(clicked_frame)

            # 下钻逻辑
            if self.on_drill_down and raw_events:
                closest = self._find_closest_event(clicked_frame, raw_events, frame_indices)
                if closest:
                    self.on_drill_down(closest)

    def _find_closest_event(
        self,
        clicked_frame: int,
        raw_events: list[dict[str, Any]],
        frame_indices: list[int]
    ) -> dict[str, Any] | None:
        """找到最接近点击帧的事件"""
        if not frame_indices:
            return None

        idx = bisect.bisect_left(frame_indices, clicked_frame)

        if idx == 0:
            return raw_events[0]
        elif idx >= len(raw_events):
            return raw_events[-1]
        else:
            p1, p2 = raw_events[idx - 1], raw_events[idx]
            if abs(p1['frame'] - clicked_frame) < abs(p2['frame'] - clicked_frame):
                return p1
            return p2
