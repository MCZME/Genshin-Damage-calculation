import flet as ft
from ui.theme import GenshinTheme
from ui.components.analysis.base_widget import BaseAnalysisWidget
from core.persistence.adapter import ReviewDataAdapter

class ViewLibraryItem(ft.Container):
# ... (ViewLibraryItem 实现保持不变)
    """
    视图资源库项：支持正常模式与迷你模式
    """
    def __init__(self, name: str, icon: ft.Icons, view_type: str, col_span: int, height: int, on_add, is_compact=False):
        super().__init__(
            padding=ft.Padding(left=12, right=12, top=10, bottom=10),
            border_radius=8,
            bgcolor="rgba(255,255,255,0.03)",
            on_hover=self._on_hover,
            on_click=lambda _: on_add(view_type, name, icon, col_span, height),
            tooltip=name if is_compact else None
        )
        self.is_compact = is_compact
        self.view_name = name
        self.view_icon = icon
        
        self._build_content()

    def _build_content(self):
        if self.is_compact:
            self.content = ft.Container(
                content=ft.Icon(self.view_icon, size=20, color=GenshinTheme.PRIMARY),
                alignment=ft.alignment.Alignment.CENTER
            )
        else:
            self.content = ft.Row([
                ft.Icon(self.view_icon, size=18, color=GenshinTheme.PRIMARY),
                ft.Column([
                    ft.Text(self.view_name, size=13, weight=ft.FontWeight.BOLD, no_wrap=True),
                    # ft.Text(f"占比: {self.col_span}/12", size=10, opacity=0.4), # 暂时隐藏以简化
                ], spacing=0, tight=True)
            ], spacing=10)

    def update_mode(self, is_compact):
        self.is_compact = is_compact
        self.tooltip = self.view_name if is_compact else None
        self._build_content()
        try:
            self.update()
        except: pass

    def _on_hover(self, e):
        e.control.bgcolor = "rgba(255,255,255,0.1)" if e.data == "true" else "rgba(255,255,255,0.03)"
        e.control.update()

class AnalysisView(ft.Container):
    """
    分析工作台主视图 (V3.2)
    """
    def __init__(self, state):
        super().__init__(expand=True, bgcolor=GenshinTheme.BACKGROUND)
        self.state = state
        self.adapter = ReviewDataAdapter()
        self.is_sidebar_collapsed = False
        
        # 统计文本
        self.total_dmg_text = ft.Text("0", size=16, weight=ft.FontWeight.W_900)
        self.avg_dps_text = ft.Text("0", size=12, opacity=0.7)
        self.duration_text = ft.Text("0s", size=12, opacity=0.7)
        
        self._build_ui()

    def _build_ui(self):
        # 1. 左侧资源库 (可折叠侧边栏)
        self.sidebar_items = [
            ViewLibraryItem("伤害曲线图", ft.Icons.TIMELINE, "trend", 12, 350, self._add_widget),
            ViewLibraryItem("双人对比曲线", ft.Icons.STACKED_LINE_CHART, "compare", 8, 300, self._add_widget),
            ViewLibraryItem("伤害分布饼图", ft.Icons.PIE_CHART, "pie", 4, 300, self._add_widget),
            ViewLibraryItem("角色快照面板", ft.Icons.ANALYTICS, "state", 6, 300, self._add_widget),
        ]
        
        # 战斗摘要概览
        self.summary_card = ft.Container(
            content=ft.Column([
                ft.Text("本次战斗摘要", size=10, opacity=0.5, weight=ft.FontWeight.BOLD),
                self.total_dmg_text,
                ft.Row([
                    ft.Icon(ft.Icons.SPEED, size=12, opacity=0.5),
                    self.avg_dps_text,
                    ft.VerticalDivider(width=1),
                    ft.Icon(ft.Icons.TIMER_OUTLINED, size=12, opacity=0.5),
                    self.duration_text,
                ], spacing=10)
            ], spacing=2),
            padding=15,
            bgcolor="rgba(255,255,255,0.02)",
            border_radius=10,
            border=ft.Border.all(1, "rgba(255,255,255,0.05)"),
            visible=not self.is_sidebar_collapsed
        )

        self.sidebar = ft.Container(
            width=260,
            padding=15,
            border=ft.Border.only(right=ft.BorderSide(1, "rgba(255,255,255,0.05)")),
            animate=ft.Animation(300, ft.AnimationCurve.DECELERATE),
            content=ft.Column([
                # Sidebar Toggle Header
                ft.Row([
                    ft.Text("分析工具箱", size=12, weight=ft.FontWeight.BOLD, opacity=0.5, visible=not self.is_sidebar_collapsed),
                    ft.IconButton(
                        icon=ft.Icons.KEYBOARD_DOUBLE_ARROW_LEFT if not self.is_sidebar_collapsed else ft.Icons.KEYBOARD_DOUBLE_ARROW_RIGHT,
                        icon_size=16,
                        on_click=self._toggle_sidebar
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN if not self.is_sidebar_collapsed else ft.MainAxisAlignment.CENTER),
                
                ft.Divider(height=10, color="transparent"),
                self.summary_card,
                ft.Divider(height=10, color="transparent"),
                ft.Column(self.sidebar_items, spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
            ])
        )

        # 2. 中心画布 (响应式栅格)
        self.canvas = ft.ResponsiveRow(
            controls=[],
            spacing=15,
            run_spacing=15,
        )
        
        self.canvas_area = ft.Container(
            expand=True,
            padding=20,
            content=ft.Column([self.canvas], scroll=ft.ScrollMode.AUTO)
        )

        # 3. 底部悬浮控制栏
        # (后续实装，先留出 Stack 结构)
        
        # 组装
        self.content = ft.Stack([
            ft.Row([
                self.sidebar,
                self.canvas_area
            ], expand=True, spacing=0),
            
            # 3. 底部悬浮控制栏
            ft.Container(
                content=self._build_floating_controller(),
                alignment=ft.alignment.Alignment.BOTTOM_CENTER,
                bottom=30, left=0, right=0, height=100,
            )
        ], expand=True)

    def get_header_tools(self):
        """为 AppLayout 提供 Header 区域的工具按钮"""
        # 预设模板配置
        self.PRESETS = {
            "全视角复盘": [
                ("trend", "伤害曲线图", ft.Icons.TIMELINE, 12, 350),
                ("state", "角色快照面板", ft.Icons.ANALYTICS, 6, 300),
                ("pie", "伤害分布饼图", ft.Icons.PIE_CHART, 6, 300),
            ],
            "数据审计": [
                ("pie", "伤害分布饼图", ft.Icons.PIE_CHART, 12, 320),
                ("trend", "伤害曲线图", ft.Icons.TIMELINE, 12, 320),
            ],
        }

        preset_menu = ft.PopupMenuButton(
            content=ft.Row([ft.Icon(ft.Icons.DASHBOARD_ROUNDED, size=16), ft.Text("布局预设", size=12)]),
            items=[
                ft.PopupMenuItem(
                    content=ft.Text(name), 
                    on_click=lambda e, n=name: self._apply_preset(n)
                ) for name in self.PRESETS.keys()
            ]
        )

        return ft.Row([
            preset_menu,
            ft.VerticalDivider(width=1, color="rgba(255,255,255,0.1)"),
            ft.TextButton("清空画布", icon=ft.Icons.CLEAR_ALL, on_click=self._clear_canvas)
        ], spacing=10)

    def _build_floating_controller(self):
        """构建底部悬浮播放器"""
        self.slider = ft.Slider(
            min=0, max=1000, value=0,
            on_change=self._handle_slider_sync
        )
        self.frame_text = ft.Text("0", size=14, weight=ft.FontWeight.W_900, color=GenshinTheme.PRIMARY)
        
        return ft.Container(
            content=ft.Row([
                ft.IconButton(ft.Icons.PLAY_ARROW_ROUNDED, icon_color=GenshinTheme.PRIMARY, icon_size=32),
                self.slider,
                ft.Row([ft.Text("Frame:", size=11, opacity=0.5), self.frame_text], spacing=5)
            ], spacing=15),
            width=900, height=70, padding=ft.Padding.symmetric(horizontal=25),
            bgcolor="rgba(35, 35, 45, 0.95)", blur=ft.Blur(10, 10),
            border=ft.Border.all(1, "rgba(255,255,255,0.15)"), border_radius=35,
            shadow=ft.BoxShadow(blur_radius=25, color="rgba(0,0,0,0.6)")
        )

    def _apply_preset(self, preset_name):
        """执行预设排版"""
        self.canvas.controls.clear()
        config = self.PRESETS.get(preset_name, [])
        for view_type, name, icon, col_span, height in config:
            self._add_widget(view_type, name, icon, col_span, height)
        self.update()

    def _handle_slider_sync(self, e):
        """全局帧同步广播"""
        frame_id = int(e.control.value)
        self.frame_text.value = str(frame_id)
        self.frame_text.update()
        for widget in self.canvas.controls:
            if hasattr(widget, "sync_frame"):
                # 注入 async 任务以处理各组件的同步
                self.page.run_task(widget.sync_frame, frame_id)

    def _toggle_sidebar(self, e):
        """切换侧边栏状态"""
        self.is_sidebar_collapsed = not self.is_sidebar_collapsed
        self.sidebar.width = 64 if self.is_sidebar_collapsed else 260
        self.summary_card.visible = not self.is_sidebar_collapsed
        
        # 更新按钮图标
        e.control.icon = ft.Icons.KEYBOARD_DOUBLE_ARROW_RIGHT if self.is_sidebar_collapsed else ft.Icons.KEYBOARD_DOUBLE_ARROW_LEFT
        
        # 更新标题显示
        self.sidebar.content.controls[0].controls[0].visible = not self.is_sidebar_collapsed
        self.sidebar.content.controls[0].alignment = ft.MainAxisAlignment.CENTER if self.is_sidebar_collapsed else ft.MainAxisAlignment.SPACE_BETWEEN
        
        # 通知所有子项更新模式
        for item in self.sidebar_items:
            item.update_mode(self.is_sidebar_collapsed)
            
        self.sidebar.update()

    def _add_widget(self, view_type, name, icon, col_span, height):
        """动态添加分析组件 (工厂模式)"""
        from ui.components.analysis.trend_chart import TrendChartWidget
        from ui.components.analysis.character_snapshot import CharacterSnapshotWidget
        from ui.components.analysis.damage_pie import DamageDistributionWidget
        
        # 定义视图映射
        view_map = {
            "trend": TrendChartWidget,
            "compare": TrendChartWidget,
            "state": CharacterSnapshotWidget,
            "pie": DamageDistributionWidget
        }
        
        widget_cls = view_map.get(view_type, BaseAnalysisWidget)
        
        widget = widget_cls(
            view_id=f"{view_type}_{len(self.canvas.controls)}",
            name=name,
            icon=icon,
            adapter=self.adapter,
            col_span=col_span,
            height=height,
            on_close=self._remove_widget,
            on_maximize=self._handle_widget_maximize # 实装最大化回调
        )
        
        self.canvas.controls.append(widget)
        
        # 立即异步加载数据
        self.page.run_task(widget.load_data)
        self.update()

    def _handle_widget_maximize(self, target_widget, is_maximized):
        """处理 Widget 的全屏/还原布局逻辑"""
        if is_maximized:
            # 1. 隐藏其他所有组件
            for w in self.canvas.controls:
                if w != target_widget:
                    w.visible = False
            # 2. 将目标组件设为全宽全屏
            target_widget.col = 12
            target_widget.height = 700 # 大尺寸展示
        else:
            # 1. 还原所有组件可见性
            for w in self.canvas.controls:
                w.visible = True
            # 2. 还原目标组件尺寸
            target_widget.col = target_widget.original_col
            target_widget.height = target_widget.original_height
            
        self.update()

    def _remove_widget(self, widget):
        self.canvas.controls.remove(widget)
        self.update()

    def _clear_canvas(self, e):
        self.canvas.controls.clear()
        self.update()

    async def load_data(self):
        """加载真实仿真汇总数据"""
        if self.state.last_session_id:
            self.adapter.session_id = self.state.last_session_id
            
        stats = await self.adapter.get_summary_stats()
        self.total_dmg_text.value = f"{stats['total_damage']:,}"
        self.avg_dps_text.value = f"{stats['avg_dps']:,}"
        self.duration_text.value = f"{stats['duration_seconds']:.1f}s"
        
        # 更新时间轴范围
        max_frames = int(stats['duration_seconds'] * 60)
        self.slider.max = max_frames
        
        try:
            self.update()
        except: pass
