import flet as ft
from ui.theme import GenshinTheme

class GlobalScrubber(ft.Container):
    """
    全局时间控制锚点 (V5.0 延迟同步版)。
    彻底移除 on_change 事件，利用原生 label 实现 0 延迟反馈。
    """
    def __init__(self, max_frames: int, on_change=None):
        super().__init__()
        self.max_frames = max_frames
        self.current_frame = 0
        self.on_change_callback = on_change
        
        self.expand = True
        self.padding = ft.padding.symmetric(horizontal=10)
        self._build_ui()

    def _build_ui(self):
        # 核心：使用 on_change_end 并在 label 中定义时间格式
        # 注意：必须设置 divisions 才会显示 label 气泡
        self.slider = ft.Slider(
            min=0, max=self.max_frames, value=0,
            divisions=self.max_frames if self.max_frames > 0 else 1,
            active_color=GenshinTheme.PRIMARY,
            label="{value}f", # 原生气泡提示
            on_change_end=self._handle_change_end, 
            expand=True,
        )

        self.time_text = ft.Text(
            "00:00.00", size=12, font_family="Consolas",
            weight=ft.FontWeight.W_600, color=GenshinTheme.PRIMARY,
            width=80, text_align=ft.TextAlign.CENTER
        )

        self.total_time_text = ft.Text(
            self._format_time(self.max_frames), 
            size=10, opacity=0.4
        )

        self.content = ft.Row([
            self.time_text,
            self.slider,
            ft.Container(content=self.total_time_text, margin=ft.margin.only(right=10))
        ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER)

    def _handle_change_end(self, e):
        """仅在鼠标松开时触发"""
        val = int(e.control.value)
        self.current_frame = val
        
        # 1. 同步侧边文字
        self.time_text.value = self._format_time(val)
        self.time_text.update()
        
        # 2. 通知 AnalysisView 同步所有磁贴
        if self.on_change_callback:
            self.on_change_callback(val)

    def _format_time(self, frame: int) -> str:
        total_seconds = frame / 60.0
        minutes = int(total_seconds // 60)
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:05.2f}"

    def update_range(self):
        self.slider.max = self.max_frames
        self.slider.divisions = self.max_frames if self.max_frames > 0 else 1
        self.total_time_text.value = self._format_time(self.max_frames)
        self.update()

    def set_frame(self, frame: int, notify: bool = True):
        self.current_frame = frame
        self.slider.value = frame
        self.time_text.value = self._format_time(frame)
        if notify and self.on_change_callback:
            self.on_change_callback(frame)
        try: self.update()
        except: pass
