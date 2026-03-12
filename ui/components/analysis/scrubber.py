"""
[V9.2] 全局时间控制锚点
"""
import flet as ft
from ui.theme import GenshinTheme
from ui.states.analysis_state import AnalysisState

def format_time(frame: int) -> str:
    """时间格式化工具函数"""
    total_seconds = frame / 60.0
    minutes = int(total_seconds // 60)
    seconds = total_seconds % 60
    return f"{minutes:02d}:{seconds:05.2f}"

@ft.component
def GlobalScrubber(state: AnalysisState, on_change=None):
    """
    全局时间控制锚点 (声明式 V6.6)。
    实现拖动实时反馈与松开延迟同步。
    """
    # 1. 局部状态：管理标尺拖动时的临时位置 (不触发全局重绘)
    local_frame, set_local_frame = ft.use_state(state.vm.current_frame)

    # 2. 全局状态监听：当外部触发帧跳转时同步本地状态
    ft.use_effect(
        lambda: set_local_frame(state.vm.current_frame),
        [state.vm.current_frame]
    )

    # 3. 拖动中：仅更新本地显示，确保绝对丝滑
    def handle_change(e):
        val = int(float(e.data))
        set_local_frame(val)

    # 4. 松开后：同步到全局业务层，驱动所有磁贴
    def handle_change_end(e):
        val = int(float(e.data))
        state.set_frame(val)
        if on_change:
            on_change(val)

    # 计算最大帧数
    max_frames = max(state.vm.total_frames, 1)

    return ft.Container(
        content=ft.Row([
            # 当前时间显示
            ft.Text(
                format_time(local_frame),
                size=12,
                font_family="Consolas",
                weight=ft.FontWeight.W_600,
                color=GenshinTheme.PRIMARY,
                width=80,
                text_align=ft.TextAlign.CENTER
            ),

            # 核心标尺
            ft.Slider(
                min=0,
                max=max_frames,
                value=local_frame,
                divisions=max_frames,
                active_color=GenshinTheme.PRIMARY,
                label="{value}f",
                on_change=handle_change,
                on_change_end=handle_change_end, # 延迟同步
                expand=True,
            ),

            # 总时长显示
            ft.Container(
                content=ft.Text(format_time(max_frames), size=10, opacity=0.4),
                margin=ft.margin.only(right=10)
            )
        ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        expand=True,
        padding=ft.padding.symmetric(horizontal=10)
    )
