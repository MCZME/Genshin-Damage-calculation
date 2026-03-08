from __future__ import annotations
import asyncio
import flet as ft
from typing import TYPE_CHECKING, Any, Callable
from ui.states.analysis_state import AnalysisState
from ui.components.analysis.scrubber import GlobalScrubber
from ui.components.analysis.floating_drawer import FloatingDrawer
from ui.components.analysis.tile_container import TileContainer
from ui.components.analysis.dps_tile import DPSChartTile
from ui.components.analysis.summary_tile import SummaryTile
from ui.components.analysis.damage_dist_tile import DamageDistributionTile
from ui.components.analysis.stats_tile import CharacterStatsTile
from ui.components.analysis.history_dialog import HistoryDialog
from ui.components.analysis.toolbox import AnalysisToolbox
from core.logger import get_ui_logger

if TYPE_CHECKING:
    from ui.states.app_state import AppState

# --- Grid Configuration [V4.0 Final] ---
CELL_SIZE = 160
GUTTER = 16

def calculate_grid_layout(items: list[dict], available_width: float) -> tuple[list[dict], float]:
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
def TileWrapper(item: dict, state: AnalysisState, set_maximized_tile_id: Callable):
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
    def __init__(self, app_state: AppState | None = None, state: AnalysisState | None = None):
        self.app_state = app_state
        self.state = state or AnalysisState(app_state=app_state)
        # GlobalScrubber 是一个被 @ft.component 装饰的函数，因此 Ref 类型应为 Control
        self.scrubber_ref = ft.Ref[ft.Control]()
        # self.drawer_comp = FloatingDrawer(width=450)

    @ft.component
    def build(self):
        # 1. 订阅核心状态
        active_tiles = self.state.model.active_tiles 
        _trigger = self.state.model.update_counter
        # [V8.1] 历史弹窗状态直接从模型读取
        is_history_open = self.state.model.history_dialog_visible
        
        # 2. 本地 UI 状态
        maximized_tile_id, set_maximized_tile_id = ft.use_state(None)
        
        # 强刷钩子与响应式宽度
        dummy, set_dummy = ft.use_state(0)
        
        # 安全获取页面宽度
        current_page_width = 1200.0
        if self.app_state and self.app_state.page and self.app_state.page.width:
            current_page_width = float(self.app_state.page.width)
            
        container_width, set_container_width = ft.use_state(current_page_width - 140)
        
        # 3. 事件绑定
        def setup_events():
            # PubSub 订阅需要包含清理逻辑，防止订阅累积导致卡死
            def on_force_refresh(e):
                async def _update():
                    set_dummy(lambda d: d + 1)
                    if self.app_state and self.app_state.page and self.app_state.page.width:
                        set_container_width(float(self.app_state.page.width) - 140)
                if self.app_state and self.app_state.page:
                    self.app_state.page.run_task(_update)
            
            if self.app_state and self.app_state.page:
                self.app_state.page.pubsub.subscribe(on_force_refresh)

            def cleanup():
                # 必须显式取消订阅
                if self.app_state and self.app_state.page:
                    self.app_state.page.pubsub.unsubscribe()
            return cleanup
        ft.use_effect(setup_events, [])

        def on_resize(e: Any):
            if self.app_state and self.app_state.page and self.app_state.page.width:
                set_container_width(float(self.app_state.page.width) - 140)
        
        def setup_resize() -> None:
            if self.app_state and self.app_state.page:
                self.app_state.page.on_resize = on_resize
            
        ft.use_effect(setup_resize, [])

        # 4. 业务逻辑绑定
        def handle_drill_down(point):
            """下钻：切换帧并打开审计抽屉"""
            self.state.set_frame(int(point['frame']))
            self.state.open_drawer(side="right")
            if 'event_id' in point:
                # 异步加载该事件的审计详情
                asyncio.create_task(self.state.load_audit_detail(point['event_id']))

        def tile_factory(state_obj, iid):
            tile_type = iid.rsplit('_', 1)[0]
            if tile_type == "dps":
                return DPSChartTile(state_obj, on_drill_down=handle_drill_down), (2, 2)
            elif tile_type == "damage_dist":
                # 伤害分布图点击也会同步 Frame 并建议打开审计
                return DamageDistributionTile(state_obj, on_drill_down=handle_drill_down), (4, 2)
            elif tile_type == "summary":
                return SummaryTile(state_obj), (2, 1)
            elif tile_type == "stats":
                return CharacterStatsTile(state_obj, iid), (2, 2)
            return None, (1, 1)

        def handle_toolbox_action(tid):
            if tid == "history":
                self.state.load_history_list()
                return
            self.state.add_tile(tid, tile_factory)

        # 5. 计算网格布局
        visible_tiles = [t for t in active_tiles if t['instance_id'] != maximized_tile_id]
        layout_items, total_grid_height = calculate_grid_layout(visible_tiles, container_width)

        # 6. 聚焦层 (对话框/全屏磁贴)
        focus_content = None
        if is_history_open:
            focus_content = HistoryDialog(
                sessions=self.state.model.sessions_history,
                on_select=lambda sid: [self.state.load_session(sid), self.state.close_history()],
                on_close=lambda: self.state.close_history()
            )
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
        for t in active_tiles:
            type_counts[t['type']] += 1

        # 7. 获取数据槽位供抽屉使用
        dist_slot = self.state.data_manager.get_slot("damage_dist")
        audit_slot = self.state.data_manager.get_slot("audit")

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
                        padding=ft.Padding(left=30, top=20, right=30, bottom=80), expand=True
                    ),
                    ft.Container(
                        content=GlobalScrubber(
                            state=self.state, 
                        ),
                        height=45, bgcolor="#1E1A2A", border=ft.border.only(top=ft.border.BorderSide(1, "rgba(255, 255, 255, 0.08)")),
                        padding=ft.Padding(left=20, top=0, right=30, bottom=0), alignment=ft.Alignment(0, 0)
                    )
                ], spacing=0, expand=True)
            ], spacing=0, expand=True),
            
            # [V7.0] 侧边审计抽屉
            FloatingDrawer(
                state=self.state,
                model=self.state.model,
                dist_slot=dist_slot,
                detail_slot=audit_slot,
                on_fetch_detail=lambda eid: asyncio.create_task(self.state.load_audit_detail(eid)),
                on_close=lambda: self.state.close_drawer()
            ),

            ft.Container(
                content=ft.Stack([
                    ft.Container(bgcolor="rgba(0,0,0,0.7)", on_click=lambda _: [self.state.close_history(), set_maximized_tile_id(None)]),
                    ft.Container(content=focus_content, padding=40, alignment=ft.Alignment.CENTER),
                ]),
                visible=focus_content is not None, expand=True
            )
        ], expand=True)
