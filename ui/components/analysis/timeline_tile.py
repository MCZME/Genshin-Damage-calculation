import flet as ft
from ui.theme import GenshinTheme
from ui.components.analysis.base_widget import AnalysisTile
from core.persistence.adapter import ReviewDataAdapter

class TimelineTile(AnalysisTile):
    """
    磁贴：多轨时间轴。
    直观展示全队动作序列与目标元素状态。
    """
    def __init__(self):
        super().__init__("多轨仿真时间轴", ft.Icons.VIEW_TIMELINE_OUTLINED)
        self.action_tracks = {}
        self.aura_track = []
        self.max_frames = 1
        self.current_frame = 0
        self.expand = False # 显式声明不拉伸
        
        # UI 引用 - 移除滚动，让其高度由内容撑开
        self.track_container = ft.Column(spacing=5) 
        self.cursor = ft.Container(
            width=2, 
            bgcolor=GenshinTheme.PRIMARY, 
            height=100,
            offset=ft.Offset(0, 0),
            animate_offset=ft.Animation(100, ft.AnimationCurve.EASE_OUT)
        )
        
        self.content = ft.Stack([
            self.track_container,
            self.cursor
        ])

    def load_data(self, adapter: ReviewDataAdapter):
        pass # 已由 AnalysisState 统一加载并分发

    def update_data(self, action_tracks, aura_track, max_frames):
        self.action_tracks = action_tracks
        self.aura_track = aura_track
        self.max_frames = max_frames or 1
        self._build_ui()

    def _build_ui(self):
        self.track_container.controls.clear()
        
        # 1. 角色动作轨道
        for char_name, segments in self.action_tracks.items():
            self.track_container.controls.append(
                self._build_character_track(char_name, segments)
            )
            
        # 2. 目标元素轨道 (Aura)
        if self.aura_track:
            self.track_container.controls.append(
                self._build_aura_track("目标元素附着", self.aura_track)
            )

        # 3. 更新游标高度并显式设置磁贴高度 (压缩后的单行高度约 32px + 头部/间距补偿)
        track_count = len(self.track_container.controls)
        calc_height = track_count * 32 + 10
        self.cursor.height = calc_height
        
        # 强制设置组件和内容栈的高度，彻底锁死垂直拉伸
        self.height = calc_height
        self.content.height = calc_height
        
        try: self.update()
        except: pass

    def _build_character_track(self, name, segments):
        """为每个角色构建动作条"""
        bars = []
        for seg in segments:
            start = seg['start']
            end = seg['end']
            action = seg['action']
            
            # 根据动作类型着色
            color = ft.Colors.BLUE_400
            if "技能" in action or "E" in action: color = ft.Colors.PURPLE_400
            if "爆发" in action or "Q" in action: color = ft.Colors.AMBER_400
            if "闪避" in action: color = ft.Colors.GREEN_400
            
            # 转换帧为相对宽度 (%)
            left_pct = start / self.max_frames
            width_pct = (max(1, end - start)) / self.max_frames
            
            bars.append(
                ft.Container(
                    bgcolor=color,
                    left=2000 * left_pct,
                    width=2000 * width_pct,
                    height=12, # 压缩高度
                    border_radius=3,
                    tooltip=f"{action} ({start}-{end}f)",
                )
            )

        return ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.PERSON_OUTLINED, size=10, opacity=0.5), # 缩小图标
                ft.Text(name, size=10, weight=ft.FontWeight.BOLD, opacity=0.7), # 缩小字体
            ], spacing=5),
            ft.Container(
                content=ft.Stack(bars, height=14), # 压缩 Stack 高度
                bgcolor="rgba(255,255,255,0.03)",
                border_radius=4,
                padding=1,
                width=2000
            )
        ], spacing=2) # 压缩内部间距

    def _build_aura_track(self, name, pulses):
        """构建元素附着轨道"""
        # 为简化，仅展示主要元素
        bars = []
        # 将脉冲转换为片段
        for i in range(len(pulses) - 1):
            p = pulses[i]
            next_p = pulses[i+1]
            aura = p['aura']
            if not aura: continue
            
            # 找到最强附着元素
            main_elem = list(aura.keys())[0] if aura else None
            if not main_elem: continue
            
            color = GenshinTheme.get_element_color(main_elem)
            left_pct = p['frame'] / self.max_frames
            width_pct = (next_p['frame'] - p['frame']) / self.max_frames
            
            bars.append(
                ft.Container(
                    bgcolor=color,
                    left=2000 * left_pct,
                    width=2000 * width_pct,
                    height=8, # 压缩高度
                    border_radius=2,
                )
            )

        return ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.AUTO_AWESOME_ROUNDED, size=10, color=ft.Colors.AMBER_200, opacity=0.5),
                ft.Text(name, size=10, weight=ft.FontWeight.BOLD, opacity=0.7),
            ], spacing=5),
            ft.Container(
                content=ft.Stack(bars, height=10), # 压缩 Stack 高度
                bgcolor="rgba(255,255,255,0.03)",
                border_radius=4,
                padding=1,
                width=2000
            )
        ], spacing=2)

    def sync_to_frame(self, frame_id: int):
        """时间同步：移动垂直游标"""
        self.current_frame = frame_id
        # 游标位置 = 总宽度 * (当前帧 / 总帧数)
        pos = 2000 * (self.current_frame / self.max_frames)
        self.cursor.offset = ft.Offset(pos / 2, 0) # 修正 offset 逻辑或直接改 left
        # Offset 是比例，或者我们直接修改 cursor.left
        self.cursor.left = pos
        try: self.update()
        except: pass
