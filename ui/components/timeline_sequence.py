import flet as ft
from ui.theme import GenshinTheme
from core.logger import get_ui_logger

class TimelineSequence(ft.Column):
    """
    战术阶段中栏：支持拖拽排序的流式动作序列
    """
    ACTION_META = {
        "normal": ("普通攻击", "普"),
        "charged": ("重击", "重"),
        "skill": ("元素战技", "技"),
        "burst": ("元素爆发", "爆"),
        "plunging": ("下落攻击", "坠"),
        "dash": ("冲刺", "闪"),
        "jump": ("跳跃", "跳")
    }

    def __init__(self, state):
        super().__init__(expand=True, spacing=15)
        self.state = state

    def did_mount(self): self.refresh()

    def refresh(self):
        try:
            if not self.page: return
        except: return

        self.controls.clear()
        
        # 1. 头部
        self.controls.append(
            ft.Row([
                ft.Text("动作执行序列", size=12, weight=ft.FontWeight.W_900, opacity=0.5),
                ft.Row([
                    ft.Text(f"共 {len(self.state.action_sequence)} 步", size=10, opacity=0.3),
                    ft.TextButton("清空", icon=ft.Icons.DELETE_SWEEP, on_click=self._clear_all)
                ], spacing=15)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        )

        # 2. 序列流 (Wrap 布局)
        self.flow_container = ft.Row(
            spacing=0,
            run_spacing=16,
            wrap=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )
        
        for i, action in enumerate(self.state.action_sequence):
            # 构建带拖拽功能的动作块
            block = self._build_action_block(i, action)
            
            # 包装为可拖拽对象
            draggable_block = ft.Draggable(
                group="action_sort",
                data=str(i), # 传递当前索引
                content=block,
                content_feedback=ft.Container(
                    content=ft.Text("移动中...", size=10, weight=ft.FontWeight.BOLD),
                    padding=10, bgcolor="rgba(209, 162, 255, 0.5)", border_radius=8
                )
            )
            
            # 包装为拖拽目标 (用于接收放置)
            target_wrapper = ft.DragTarget(
                group="action_sort",
                content=draggable_block,
                on_accept=lambda e, idx=i: self._handle_drag_accept(e, idx),
                # 悬停反馈
                on_will_accept=lambda _: True
            )
            
            self.flow_container.controls.append(target_wrapper)
            
            # 添加连接符 (非最后一个)
            if i < len(self.state.action_sequence) - 1:
                self.flow_container.controls.append(
                    ft.Container(
                        content=ft.Icon(ft.Icons.CHEVRON_RIGHT, size=16, opacity=0.2),
                        width=30, alignment=ft.Alignment.CENTER
                    )
                )
            
        self.controls.append(
            ft.Column(
                [self.flow_container],
                expand=True,
                scroll=ft.ScrollMode.AUTO
            )
        )
        
        try: self.update()
        except: pass

    def _build_action_block(self, index, action):
        """构建高辨识度无边框块"""
        is_selected = (self.state.selected_action_index == index)
        char_name = action["char_name"]
        char_entry = next((m for m in self.state.team if m and m["character"]["name"] == char_name), None)
        color = GenshinTheme.get_element_color(char_entry["character"]["element"] if char_entry else "Neutral")
        full_label, first_char = self.ACTION_META.get(action["action_id"], (action["action_id"].upper(), "?"))

        return ft.Container(
            width=130, height=54,
            content=ft.Stack([
                ft.Container(bgcolor=ft.Colors.with_opacity(0.15 if is_selected else 0.05, color), border_radius=10),
                ft.Container(height=3, bgcolor=color if is_selected else "transparent", bottom=0, left=10, right=10, border_radius=2),
                ft.Row([
                    ft.Container(width=8),
                    ft.Text(first_char, size=22, weight=ft.FontWeight.W_900, color=color),
                    ft.Column([
                        ft.Text(char_name, size=9, weight=ft.FontWeight.BOLD, opacity=0.6, color=color, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text(full_label[1:], size=11, weight=ft.FontWeight.BOLD),
                    ], spacing=-2, expand=True, alignment=ft.MainAxisAlignment.CENTER),
                ], spacing=8),
                ft.Container(
                    content=ft.Text(str(index + 1), size=8, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
                    bgcolor=color if is_selected else ft.Colors.with_opacity(0.4, color),
                    width=16, height=16, border_radius=8, top=-4, left=-4, alignment=ft.Alignment.CENTER
                )
            ]),
            on_click=lambda _, idx=index: self._select_action(idx),
        )

    def _handle_drag_accept(self, e, target_idx):
        """处理排序逻辑"""
        try:
            # 修正：从源 ID 获取对应的控件并读取其 data 属性
            src_control = self.page.get_control(e.src_id)
            if not src_control or src_control.data is None: return
            
            source_idx = int(src_control.data)
            if source_idx == target_idx: return
            
            # 范围校验
            if source_idx >= len(self.state.action_sequence): return
            
            # 执行位置交换
            item = self.state.action_sequence.pop(source_idx)
            self.state.action_sequence.insert(target_idx, item)
            
            # 同步更新选中索引
            if self.state.selected_action_index == source_idx:
                self.state.selected_action_index = target_idx
                
            self.state.refresh()
        except Exception as ex:
            get_ui_logger().log_error(f"Sort Error: {ex}")

    def _select_action(self, index):
        self.state.selected_action_index = index
        self.state.refresh()

    def _clear_all(self, _):
        self.state.action_sequence.clear()
        self.state.selected_action_index = None
        self.state.refresh()