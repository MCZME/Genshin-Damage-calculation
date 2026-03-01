import asyncio
import uuid
import math
import bisect
import flet as ft
from ui.theme import GenshinTheme
from ui.states.analysis_state import AnalysisState
from ui.components.analysis.scrubber import GlobalScrubber
# from ui.components.analysis.floating_drawer import FloatingDrawer
from ui.components.analysis.tile_container import TileContainer
from ui.components.analysis.dps_tile import DPSChartTile
from ui.components.analysis.summary_tile import SummaryTile
from ui.components.analysis.damage_dist_tile import DamageDistributionTile
from ui.components.analysis.history_dialog import HistoryDialog
from ui.components.analysis.toolbox import AnalysisToolbox
from core.logger import get_ui_logger

# --- Grid Configuration [V4.0 Final] ---
CELL_SIZE = 160
GUTTER = 16

def calculate_grid_layout(items, available_width):
    """[Pure Function] 核心网格布局算法"""
    if not available_width or available_width < 100:
        return [], 0
        
    cols = max(1, int((available_width + GUTTER) / (CELL_SIZE + GUTTER)))
    occupied = [] 
    max_y = 0
    layout_results = []

    for item in items:
        # 获取 grid_size，默认 1x1
        orig_w, orig_h = item.get('grid_size', (1, 1))
        eff_w = min(orig_w, cols) # 自适应压缩
        
        phys_w = (eff_w * CELL_SIZE) + ((eff_w - 1) * GUTTER)
        phys_h = (orig_h * CELL_SIZE) + ((orig_h - 1) * GUTTER)
        
        found = False
        y = 0
        while not found and y < 1000:
            for x in range(cols - eff_w + 1):
                is_free = True
                for dx in range(eff_w):
                    for dy in range(orig_h):
                        if (x + dx, y + dy) in occupied:
                            is_free = False
                            break
                    if not is_free: break
                
                if is_free:
                    for dx in range(eff_w):
                        for dy in range(orig_h):
                            occupied.append((x + dx, y + dy))
                    
                    layout_results.append({
                        "item": item,
                        "left": x * (CELL_SIZE + GUTTER),
                        "top": y * (CELL_SIZE + GUTTER),
                        "width": phys_w,
                        "height": phys_h
                    })
                    max_y = max(max_y, y + orig_h)
                    found = True
                    break
            y += 1
            
    return layout_results, max_y * (CELL_SIZE + GUTTER)

@ft.component
def TileWrapper(item, state, set_maximized_tile_id):
    """磁贴包装器 [V6.0] 仅负责 UI 交互映射"""
    
    def handle_close(iid):
        get_ui_logger().log_debug(f"UI Triggered Closing: {iid}")
        state.remove_tile(iid)

    return TileContainer(
        key=item['instance_id'],
        tile=item['tile'],
        on_close=handle_close,
        on_maximize=set_maximized_tile_id,
        is_maximized=False
    )

class AnalysisView:
    """
    分析视图 V6.8 (模块化网格 - 160px 固化版)
    """
    def __init__(self, app_state=None, state=None):
        self.app_state = app_state
        self.state = state or AnalysisState(app_state=app_state)
        self.scrubber_ref = ft.Ref[GlobalScrubber]()
        # self.drawer_comp = FloatingDrawer(width=450)

    @ft.component
    def build(self):
        # 1. 订阅核心状态
        active_tiles = self.state.model.active_tiles 
        _trigger = self.state.model.update_counter
        
        # 2. 本地 UI 状态
        is_history_open, set_is_history_open = ft.use_state(False)
        maximized_tile_id, set_maximized_tile_id = ft.use_state(None)
        
        # 强刷钩子与响应式宽度
        dummy, set_dummy = ft.use_state(0)
        page_width = self.app_state.page.width if (self.app_state and self.app_state.page) else 1200
        container_width, set_container_width = ft.use_state(page_width - 140)
        
        def on_audit_ready():
            if self.state.current_audit:
                self.drawer_comp.update_audit(self.state.current_audit)

        # 3. 事件绑定
        def setup_events():
            subs = []
            if self.app_state:
                subs.append(self.app_state.events.subscribe("analysis_history_ready", lambda: set_is_history_open(True)))
                subs.append(self.app_state.events.subscribe("audit_detail_ready", on_audit_ready))
            def cleanup():
                for unsub in subs:
                    if callable(unsub): 
                        try: unsub()
                        except: pass
            return cleanup
        ft.use_effect(setup_events, [])

        def on_resize(e):
            if self.app_state and self.app_state.page:
                set_container_width(self.app_state.page.width - 140)
        ft.use_effect(lambda: setattr(self.app_state.page, "on_resize", on_resize), [])

        def on_force_refresh(e):
            async def _update():
                set_dummy(lambda d: d + 1)
                if self.app_state and self.app_state.page:
                    set_container_width(self.app_state.page.width - 140)
            if self.app_state and self.app_state.page:
                self.app_state.page.run_task(_update)
        ft.use_effect(lambda: self.app_state.page.pubsub.subscribe(on_force_refresh), [])

        # 4. 业务逻辑绑定
        def handle_drill_down(point):
            idx = next((i for i, a in enumerate(self.state.audit_logs) if a.event_id == point['event_id']), -1)
            if idx != -1:
                self.drawer_comp.show_loading(f"伤害审计 - Frame {point['frame']}")
                self.state.select_audit(idx)

        def tile_factory(state_obj, iid):
            tile_type = iid.rsplit('_', 1)[0]
            if tile_type == "dps":
                return DPSChartTile(state_obj, on_drill_down=handle_drill_down), (2, 2)
            elif tile_type == "damage_dist":
                return DamageDistributionTile(state_obj), (4, 2)
            elif tile_type == "summary":
                return SummaryTile(state_obj), (2, 1)
            return None, (1, 1)

        def handle_toolbox_action(tid):
            if tid == "history": self.state.load_history_list(); return
            self.state.add_tile(tid, tile_factory)

        # 5. 计算网格布局
        visible_tiles = [t for t in active_tiles if t['instance_id'] != maximized_tile_id]
        layout_items, total_grid_height = calculate_grid_layout(visible_tiles, container_width)

        # 6. 聚焦层
        focus_content = None
        if is_history_open:
            focus_content = HistoryDialog(
                sessions=self.state.model.sessions_history,
                on_select=lambda sid: [self.state.load_session(sid), set_is_history_open(False)],
                on_close=lambda: set_is_history_open(False)
            ).build()
        elif maximized_tile_id:
            max_item = next((t for t in active_tiles if t['instance_id'] == maximized_tile_id), None)
            if max_item:
                focus_content = TileContainer(
                    tile=max_item['tile'], 
                    on_maximize=lambda _: set_maximized_tile_id(None),
                    on_close=lambda _: set_maximized_tile_id(None), 
                    is_maximized=True
                )

        type_counts = {t['type']: 0 for t in active_tiles}
        for t in active_tiles: type_counts[t['type']] += 1

        return ft.Stack([
            ft.Row([
                AnalysisToolbox(active_counts=type_counts, on_tile_action=handle_toolbox_action),
                ft.Column([
                    ft.Container(
                        content=ft.Column([
                            # 核心网格容器
                            ft.Stack(
                                controls=[
                                    ft.Container(
                                        key=f"CONT_{res['item']['instance_id']}",
                                        content=TileWrapper(res['item'], self.state, set_maximized_tile_id),
                                        left=res['left'],
                                        top=res['top'],
                                        width=res['width'],
                                        height=res['height'],
                                        animate_position=ft.Animation(600, ft.AnimationCurve.EASE_OUT_EXPO)
                                    ) for res in layout_items
                                ],
                                height=total_grid_height,
                                expand=False
                            )
                        ], scroll=ft.ScrollMode.ADAPTIVE, expand=True),
                        padding=ft.Padding(30, 20, 30, 80), expand=True
                    ),
                    ft.Container(
                        content=GlobalScrubber(
                            state=self.state, 
                            on_change=lambda f: [item['tile'].sync_to_frame(f) for item in active_tiles]
                        ),
                        height=45, bgcolor="#1E1A2A", border=ft.border.only(top=ft.border.BorderSide(1, "rgba(255, 255, 255, 0.08)")),
                        padding=ft.Padding(20, 0, 30, 0), alignment=ft.Alignment(0, 0)
                    )
                ], spacing=0, expand=True)
            ], spacing=0, expand=True),
            # self.drawer_comp.build(),
            ft.Container(
                content=ft.Stack([
                    ft.Container(bgcolor="rgba(0,0,0,0.7)", on_click=lambda _: [set_is_history_open(False), set_maximized_tile_id(None)]),
                    ft.Container(content=focus_content, padding=40, alignment=ft.Alignment.CENTER),
                ]),
                visible=focus_content is not None, expand=True
            )
        ], expand=True)
