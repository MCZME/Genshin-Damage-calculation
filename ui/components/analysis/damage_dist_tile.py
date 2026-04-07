"""
[V9.2] 伤害分布脉冲图磁贴组件

重构说明：
- 数据转换逻辑已迁移至 DamageDistViewModel
- 组件仅负责 UI 渲染
- 使用统一签名 state: AnalysisState
- [V10.0] 添加范围高亮层组件
"""
import flet as ft
import flet.canvas as cv
from typing import TYPE_CHECKING, Any, Callable

from ui.components.analysis.base_widget import AnalysisTile
from ui.view_models.analysis.tile_vms.damage_dist_vm import DamageDistViewModel
from ui.theme import GenshinTheme
from core.logger import get_ui_logger

if TYPE_CHECKING:
    from ui.states.analysis_state import AnalysisState


# 绘制区域常量
STD_WIDTH = 636


def format_science(val: float) -> str:
    """科学计数法格式化"""
    if val >= 1_000_000:
        return f"{val / 1_000_000:.1f}M"
    if val >= 1_000:
        return f"{val / 1_000:.1f}k"
    return str(int(val))


class IsolatedPulseCanvas(ft.Container):
    """
    [V9.1] 纯净数据层版。
    移除所有内部背景绘制，仅负责数据脉冲与刻度标签。
    """

    def __init__(self, data: dict, canvas_height: int):
        super().__init__()
        self.data = data
        self.canvas_height = canvas_height
        self.clip_behavior = ft.ClipBehavior.NONE
        self._build_canvas()

    def is_isolated(self) -> bool:
        return True

    def _build_canvas(self):
        try:
            frame_map = self.data.get("frame_map", {})
            sorted_frames = self.data.get("sorted_frames", [])
            global_peak = self.data.get("global_peak", 1.0)
            split_threshold = self.data.get("split_threshold", global_peak)
            noise_threshold = self.data.get("noise_threshold", 0.0)
            is_split = self.data.get("is_split_axis", False)
            total_frames = max(self.data.get("total_frames", 1), 1)

            draw_h = self.canvas_height - 10
            split_y = draw_h * 0.25 if is_split else 0
            normal_zone_h = draw_h - split_y
            burst_zone_h = split_y

            def get_y_pos(val: float) -> float:
                if not is_split:
                    h = (val / global_peak) * draw_h if global_peak > 0 else 0
                    return draw_h - h
                if val <= split_threshold:
                    h = (val / split_threshold) * normal_zone_h if split_threshold > 0 else 0
                    return draw_h - h
                else:
                    burst_val = val - split_threshold
                    burst_range = global_peak - split_threshold
                    h_offset = (burst_val / burst_range) * burst_zone_h if burst_range > 0 else 0
                    return split_y - h_offset

            shapes = []

            # --- 1. 坐标轴标签与参考线 ---
            label_style = ft.TextStyle(size=9, color="#8E96AD", weight=ft.FontWeight.W_600)
            if is_split:
                shapes.append(cv.Text(STD_WIDTH - 25, 5, format_science(global_peak), style=label_style))
                shapes.append(cv.Text(STD_WIDTH - 25, split_y - 12, format_science(split_threshold), style=label_style))
                shapes.append(cv.Text(STD_WIDTH - 25, draw_h - (normal_zone_h / 2) - 12, format_science(split_threshold / 2), style=label_style))
            else:
                shapes.append(cv.Text(STD_WIDTH - 25, 5, format_science(global_peak), style=label_style))
                shapes.append(cv.Text(STD_WIDTH - 25, draw_h / 2 - 12, format_science(global_peak / 2), style=label_style))

            # --- 2. 脉冲柱渲染 ---
            px_step = 3.0
            buckets = {}
            for f in sorted_frames:
                x_pos = (f / total_frames) * STD_WIDTH
                bid = int(x_pos / px_step)
                if bid not in buckets or frame_map[f]["total"] > frame_map[buckets[bid]]["total"]:
                    buckets[bid] = f

            for f in sorted(buckets.values()):
                f_data = frame_map[f]
                x_pos = (f / total_frames) * STD_WIDTH
                total_val = f_data["total"]
                if total_val < noise_threshold:
                    continue
                target_y = get_y_pos(total_val)
                total_h = draw_h - target_y
                if total_h < 1.0:
                    continue

                curr_y_offset = 0.0
                for ev in f_data["events"]:
                    ev_ratio = ev['dmg'] / total_val if total_val > 0 else 0
                    h = ev_ratio * total_h
                    y = draw_h - curr_y_offset - h
                    color = GenshinTheme.get_element_color(ev.get('element', 'Neutral'))
                    shapes.append(cv.Rect(
                        x=x_pos - 2.5,
                        y=y,
                        width=5,
                        height=h,
                        paint=ft.Paint(color=color, style=ft.PaintingStyle.FILL)
                    ))
                    curr_y_offset += h

            self.content = cv.Canvas(shapes=shapes, height=self.canvas_height, expand=True)
        except Exception as e:
            get_ui_logger().log_error(f"DamageDist Canvas Error: {e}")
            self.content = ft.Container(
                content=ft.Text("Canvas Error", color=ft.Colors.RED_400),
                alignment=ft.Alignment(0, 0)
            )


@ft.component
def FrequencyHeatmap(data: dict, width: float):
    """频率热力图"""
    frame_map = data.get("frame_map", {})
    sorted_frames = data.get("sorted_frames", [])
    max_hits = max(data.get("max_hit_count", 1), 1)
    total_frames = max(data.get("total_frames", 1), 1)

    shapes = []
    px_step = 2.0
    buckets = {}

    for f in sorted_frames:
        x_pos = (f / total_frames) * width
        bid = int(x_pos / px_step)
        buckets[bid] = buckets.get(bid, 0) + frame_map[f].get("hit_count", 0)

    for bid, hits in buckets.items():
        intensity = min(hits / (max_hits * 1.2), 1.0)
        if intensity < 0.02:
            continue
        final_opacity = max(intensity, 0.2)
        color = ft.Colors.with_opacity(final_opacity, "#6495ED")
        shapes.append(cv.Rect(
            x=bid * px_step,
            y=0,
            width=px_step,
            height=4,
            paint=ft.Paint(color=color, style=ft.PaintingStyle.FILL)
        ))

    return ft.Container(
        content=cv.Canvas(shapes=shapes, height=4),
        width=width,
        height=6,
        bgcolor=ft.Colors.WHITE_10,
        border_radius=3,
        margin=ft.margin.only(top=-8, bottom=2)
    )


@ft.component
def DamageCursorLayer(state: 'AnalysisState', canvas_height: int):
    """游标层 (V9.2: state 为 AnalysisState)"""
    current_frame = state.vm.current_frame
    total_frames = max(state.vm.total_frames, 1)
    pos_ratio = current_frame / total_frames
    return ft.Container(
        bgcolor=ft.Colors.with_opacity(0.6, "#6495ED"),
        width=2,
        height=canvas_height - 6,
        left=pos_ratio * STD_WIDTH - 1,
        top=0,
        border_radius=1,
        animate_position=100,
        shadow=ft.BoxShadow(blur_radius=12, color="#6495ED", spread_radius=-1)
    )


@ft.component
def RangeHighlightLayer(state: 'AnalysisState', canvas_height: int):
    """[V10.0] 范围高亮层 - 显示选中帧范围的半透明蓝色区域"""
    selection = state.vm.frame_range_selection
    if not selection:
        return ft.Container()

    total_frames = max(state.vm.total_frames, 1)

    # 计算范围的像素位置
    start_ratio = selection.start_frame / total_frames
    end_ratio = selection.end_frame / total_frames

    # 如果选择范围已经完全超出了当前会话的总帧数（例如切换会话后旧数据残留），不渲染
    if selection.start_frame >= total_frames:
        return ft.Container()

    start_x = max(0.0, start_ratio * STD_WIDTH)
    # 限制宽度不超出画布右边缘
    width = min(STD_WIDTH - start_x, (end_ratio - start_ratio) * STD_WIDTH)

    if width <= 0:
        return ft.Container()

    return ft.Container(
        bgcolor=ft.Colors.with_opacity(0.15, "#6495ED"),
        width=max(width, 4),  # 最小宽度 4px
        height=canvas_height - 6,
        left=start_x,
        top=0,
        border_radius=2,
        border=ft.Border.all(1, ft.Colors.with_opacity(0.4, "#6495ED")),
        animate_position=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
        animate_size=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
    )


@ft.component
def TimeAxis(total_frames: int, width: float):
    """时间轴"""
    total_seconds = total_frames / 60
    if total_seconds <= 0:
        return ft.Container()

    if total_seconds <= 5:
        step = 1.0
    elif total_seconds <= 15:
        step = 2.0
    elif total_seconds <= 30:
        step = 5.0
    elif total_seconds <= 60:
        step = 10.0
    else:
        step = 20.0

    shapes = []
    labels: list[ft.Control] = []

    shapes.append(cv.Line(0, 0, width, 0, paint=ft.Paint(color=ft.Colors.WHITE_12, stroke_width=1)))
    label_w = 40
    num_ticks = int(total_seconds / (step / 2)) + 1

    for i in range(num_ticks):
        sec = i * (step / 2)
        x = (sec / total_seconds) * width
        if x > width - 5:
            break

        is_major = i % 2 == 0
        h = 6 if is_major else 3
        color = ft.Colors.WHITE_38 if is_major else ft.Colors.WHITE_12
        shapes.append(cv.Line(x, 0, x, h, paint=ft.Paint(color=color, stroke_width=1)))

        if is_major:
            m, s = divmod(int(sec), 60)
            time_str = f"{s}s" if m == 0 else f"{m}:{s:02d}s"
            align = ft.TextAlign.LEFT if i == 0 else ft.TextAlign.CENTER
            pos_left = x if i == 0 else x - label_w / 2
            labels.append(ft.Container(
                content=ft.Text(
                    time_str,
                    size=10,
                    color=ft.Colors.WHITE_54,
                    weight=ft.FontWeight.W_600,
                    text_align=align
                ),
                left=pos_left,
                width=label_w,
                top=14
            ))

    end_time_str = f"{total_seconds:.2f}s"
    labels.append(ft.Container(
        content=ft.Text(
            end_time_str,
            size=10,
            color=ft.Colors.WHITE_54,
            weight=ft.FontWeight.W_600,
            text_align=ft.TextAlign.RIGHT
        ),
        left=width - label_w,
        width=label_w,
        top=14
    ))

    return ft.Container(
        content=ft.Stack(
            [cv.Canvas(shapes=shapes, height=10), *labels],
            width=width,
            clip_behavior=ft.ClipBehavior.NONE
        ),
        width=width,
        height=35,
        margin=ft.margin.only(top=-18)
    )


class DamageDistributionTile(AnalysisTile):
    """
    [V9.2] 伤害分布脉冲图
    规格: 4x2

    重构说明：
    - 数据转换逻辑已迁移至 DamageDistViewModel
    - 组件仅负责 UI 渲染
    - 使用统一签名 state: AnalysisState
    """

    def __init__(
        self,
        state: 'AnalysisState',
        on_drill_down: Callable[[dict[str, Any]], None] | None = None
    ):
        super().__init__(
            "伤害分布脉冲图",
            ft.Icons.QUERY_STATS_ROUNDED,
            "damage_dist",
            state
        )
        self.on_drill_down = on_drill_down
        self.expand = True
        self.canvas_height = 240
        self.theme_color = "#6495ED"
        self.gradient_top = "#161B2E"
        self._vm: DamageDistViewModel | None = None

    def _get_vm(self) -> DamageDistViewModel:
        """获取或创建 ViewModel"""
        if self._vm is None:
            self._vm = DamageDistViewModel(
                state=self.state,
                instance_id=self.instance_id or "damage_dist_unknown",
                on_drill_down=self.on_drill_down
            )
        return self._vm

    @ft.component
    def render(self):
        vm = self._get_vm()
        slot = self.state.data_service.get_slot("damage_dist")

        if not slot or slot.data is None:
            return ft.Container(
                content=ft.ProgressRing(color=self.theme_color),
                alignment=ft.Alignment.CENTER,
                expand=True
            )

        data = slot.data
        hover_frame, set_hover_frame = ft.use_state(None)
        hover_dmg, set_hover_dmg = ft.use_state(0)

        isolated_canvas = ft.use_memo(
            lambda: IsolatedPulseCanvas(data=data, canvas_height=self.canvas_height),
            [data.get('global_peak'), data.get('total_frames'), data.get('split_threshold'), data.get('is_split_axis')]
        )

        is_split = data.get("is_split_axis", False)
        panel_w = 656
        burst_h = (self.canvas_height - 10) * 0.25 + 15 if is_split else 0

        def handle_hover(e: ft.HoverEvent):
            vm.handle_hover(e, set_hover_frame, set_hover_dmg)

        def handle_tap(e: ft.TapEvent):
            vm.handle_tap(e, self.canvas_height)

        return ft.Container(
            bgcolor=ft.Colors.with_opacity(0.3, ft.Colors.BLACK),
            border=ft.Border.all(0.5, ft.Colors.WHITE_10),
            border_radius=0,
            content=ft.Stack([
                # --- 1.0 溢出区背景 ---
                ft.Container(
                    bgcolor="#1A1C2E",
                    width=panel_w,
                    height=burst_h,
                    visible=is_split,
                    border=ft.Border.only(bottom=ft.BorderSide(0.8, "rgba(100, 149, 237, 0.3)"))
                ),
                # --- 2.0 内容层 ---
                ft.Container(
                    padding=ft.Padding(10, 15, 10, 5),
                    content=ft.Column([
                        ft.Container(
                            content=ft.Stack([
                                isolated_canvas,
                                RangeHighlightLayer(state=self.state, canvas_height=self.canvas_height),
                                DamageCursorLayer(state=self.state, canvas_height=self.canvas_height),
                                # 读数面板
                                ft.Container(
                                    content=ft.Column([
                                        ft.Text(
                                            f"帧伤害: {format_science(hover_dmg)}" if hover_frame is not None else "等待扫描",
                                            size=11,
                                            color=self.theme_color if hover_frame else ft.Colors.WHITE_24,
                                            weight=ft.FontWeight.W_900
                                        )
                                    ], spacing=4),
                                    left=10,
                                    top=0,
                                ),
                                ft.GestureDetector(
                                    on_tap_up=handle_tap,
                                    on_hover=handle_hover,
                                    expand=True,
                                    mouse_cursor=ft.MouseCursor.BASIC
                                )
                            ], width=STD_WIDTH, height=self.canvas_height),
                        ),
                        FrequencyHeatmap(data=data, width=STD_WIDTH),
                        TimeAxis(total_frames=data.get('total_frames', 0), width=STD_WIDTH)
                    ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                )
            ]),
            expand=True
        )
