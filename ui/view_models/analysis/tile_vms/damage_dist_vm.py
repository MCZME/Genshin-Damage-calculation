"""
[V9.2] 伤害分布 ViewModel

职责：
1. 从缓存获取伤害分布数据
2. 提供脉冲图渲染所需的数据结构
3. 处理交互事件

重构说明：
- 使用统一签名 state: AnalysisState
- 通过 state.data_service 访问数据服务
- 通过 state.vm 访问 ViewModel
- [V10.0] 帧选择改为范围选择（0.5秒窗口）
"""
from __future__ import annotations

import flet as ft
import bisect
from typing import TYPE_CHECKING, Any, Callable

from ui.theme import GenshinTheme
from ui.view_models.analysis.tile_vms.types import FrameRangeSelection

if TYPE_CHECKING:
    from ui.states.analysis_state import AnalysisState


@ft.observable
class DamageDistViewModel:
    """
    伤害分布 ViewModel - 从缓存获取数据并处理交互
    """

    # 绘制区域常量
    STD_WIDTH = 636

    def __init__(
        self,
        state: 'AnalysisState',
        instance_id: str,
        on_drill_down: Callable[[dict[str, Any]], None] | None = None
    ):
        self.state = state
        self.instance_id = instance_id
        self.on_drill_down = on_drill_down
        self.theme_color = "#6495ED"

    # ============================================================
    # 状态属性
    # ============================================================

    @property
    def loading(self) -> bool:
        """数据是否正在加载"""
        slot = self.state.data_service.get_cached("damage_dist")
        return slot.loading if slot else True

    @property
    def has_data(self) -> bool:
        """是否有数据"""
        slot = self.state.data_service.get_cached("damage_dist")
        return slot is not None and slot.data is not None

    @property
    def data(self) -> dict[str, Any]:
        """原始数据"""
        slot = self.state.data_service.get_cached("damage_dist")
        return slot.data if slot and slot.data else {}

    # ============================================================
    # 数据属性
    # ============================================================

    @property
    def frame_map(self) -> dict[int, dict[str, Any]]:
        """帧 -> 伤害数据映射"""
        return self.data.get("frame_map", {})

    @property
    def sorted_frames(self) -> list[int]:
        """排序后的帧列表"""
        return self.data.get("sorted_frames", [])

    @property
    def total_frames(self) -> int:
        """总帧数"""
        return max(self.data.get("total_frames", 1), 1)

    @property
    def global_peak(self) -> float:
        """全局峰值"""
        return self.data.get("global_peak", 1.0)

    @property
    def split_threshold(self) -> float:
        """分段阈值"""
        return self.data.get("split_threshold", self.global_peak)

    @property
    def is_split_axis(self) -> bool:
        """是否使用分段轴"""
        return self.data.get("is_split_axis", False)

    @property
    def noise_threshold(self) -> float:
        """噪声阈值"""
        return self.data.get("noise_threshold", 0.0)

    @property
    def max_hit_count(self) -> int:
        """最大命中数"""
        return max(self.data.get("max_hit_count", 1), 1)

    # ============================================================
    # 常量
    # ============================================================

    # 帧范围选择窗口大小（帧数）- 固定 0.5 秒
    FRAME_RANGE_WINDOW = 30  # 0.5s * 60fps

    # ============================================================
    # 交互处理
    # ============================================================

    def handle_tap(self, e: ft.TapEvent, canvas_height: int) -> None:
        """[V10.0] 处理点击事件 - 范围选择模式

        点击脉冲图时，收集以点击帧为中心、前后各 15 帧（共 30 帧/0.5秒）范围内的所有伤害事件。
        """
        if not e.local_position:
            return

        logical_x = max(0, min(e.local_position.x - 10, self.STD_WIDTH))
        clicked_f = max(0, min((logical_x / self.STD_WIDTH) * self.total_frames, float(self.total_frames)))

        if not self.sorted_frames:
            return

        # 计算帧范围
        half_window = self.FRAME_RANGE_WINDOW // 2
        start_frame = max(0, int(clicked_f) - half_window)
        end_frame = min(self.total_frames, int(clicked_f) + half_window)

        # 收集范围内所有事件
        events_in_range: list[dict] = []
        total_damage = 0.0

        for f in self.sorted_frames:
            if start_frame <= f <= end_frame:
                f_data = self.frame_map.get(f, {})
                f_events = f_data.get("events", [])
                for ev in f_events:
                    # 添加帧信息
                    ev_copy = ev.copy()
                    ev_copy['frame'] = f
                    events_in_range.append(ev_copy)
                    total_damage += ev.get('dmg', 0)

        # 按伤害降序排序
        events_in_range.sort(key=lambda x: x.get('dmg', 0), reverse=True)

        # 创建范围选择对象
        selection = FrameRangeSelection(
            center_frame=int(clicked_f),
            start_frame=start_frame,
            end_frame=end_frame,
            events=events_in_range,
            total_damage=total_damage,
            time_range_seconds=0.5
        )

        # 更新状态
        self.state.vm.set_frame(int(clicked_f))
        self.state.vm.set_frame_range_selection(selection)

        # 下钻逻辑 - 选择伤害最高的事件
        if self.on_drill_down and events_in_range:
            max_ev = events_in_range[0]  # 已按伤害降序排序
            self.on_drill_down(max_ev)

    def handle_hover(
        self,
        e: ft.HoverEvent,
        set_hover_frame: Callable[[int | None], None],
        set_hover_dmg: Callable[[float], None]
    ) -> None:
        """处理悬停事件"""
        if not e.local_position:
            set_hover_frame(None)
            return

        logical_x = max(0, min(e.local_position.x - 10, self.STD_WIDTH))
        clicked_f = max(0, min((logical_x / self.STD_WIDTH) * self.total_frames, float(self.total_frames)))

        if not self.sorted_frames:
            return

        idx = bisect.bisect_left(self.sorted_frames, clicked_f)
        candidates = self.sorted_frames[max(0, idx - 1):min(len(self.sorted_frames), idx + 1)]

        if candidates:
            closest = min(candidates, key=lambda f: abs(f - clicked_f))
            tolerance = (15 / self.STD_WIDTH) * self.total_frames

            if abs(closest - clicked_f) < tolerance:
                set_hover_frame(closest)
                set_hover_dmg(self.frame_map.get(closest, {}).get("total", 0))
            else:
                set_hover_frame(None)
        else:
            set_hover_frame(None)

    # ============================================================
    # 辅助方法
    # ============================================================

    def get_element_color(self, element: str) -> str:
        """获取元素颜色"""
        return GenshinTheme.get_element_color(element)
