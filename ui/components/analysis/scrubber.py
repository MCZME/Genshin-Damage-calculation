import flet as ft
from ui.theme import GenshinTheme

class GlobalScrubber(ft.Container):
    """
    全局时间控制锚点 (地平线)。
    提供总时长的宏观预览与精细步进控制。
    """
    def __init__(self, max_frames: int, on_change=None):
        super().__init__()
        self.max_frames = max_frames
        self.current_frame = 0
        self.on_change_callback = on_change
        
        # 基础样式 - 移除背景，由外部容器提供
        self.expand = True
        self.padding = ft.padding.symmetric(horizontal=10)
        
        self._build_ui()

    def _build_ui(self):
        # 1. 进度滑动条
        self.slider = ft.Slider(
            min=0,
            max=self.max_frames,
            value=0,
            active_color=GenshinTheme.PRIMARY,
            on_change=self._handle_slider_change,
            expand=True,
        )

        # 2. 时间显示气泡
        self.time_text = ft.Text(
            self._format_time(0),
            size=12,
            font_family="Consolas", # 使用等宽字体防止数字跳变
            weight=ft.FontWeight.W_600,
            color=GenshinTheme.PRIMARY,
            width=80,
            text_align=ft.TextAlign.CENTER
        )

        # 使用 Container 包装 Row 以确保在 45px 高度内完美居中
        self.total_time_text = ft.Text(f"{self._format_time(self.max_frames)}", size=10, opacity=0.4)
        self.content = ft.Row([
            self.time_text,
            
            # Slider 在 Row 中会自动拉伸并尝试垂直居中
            self.slider,
            
            ft.Container(
                content=self.total_time_text,
                margin=ft.margin.only(right=10)
            )
        ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER)

    def _handle_slider_change(self, e):
        self.set_frame(int(e.control.value))

    def update_range(self):
        """当仿真数据加载后，更新标尺的最大跨度"""
        self.slider.max = self.max_frames
        self.total_time_text.value = self._format_time(self.max_frames)
        try:
            self.slider.update()
            self.total_time_text.update()
        except:
            pass

    def set_frame(self, frame: int, notify: bool = True):
        """外部与内部统一的帧更新方法"""
        # 约束范围
        new_frame = max(0, min(frame, self.max_frames))
        if new_frame == self.current_frame and notify: return
        
        self.current_frame = new_frame
        self.slider.value = self.current_frame
        self.time_text.value = self._format_time(self.current_frame)
        
        if notify and self.on_change_callback:
            self.on_change_callback(self.current_frame)
            
        try:
            self.time_text.update()
            self.slider.update()
        except: pass

    def _format_time(self, frame: int) -> str:
        total_seconds = frame / 60.0
        minutes = int(total_seconds // 60)
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:05.2f}"
