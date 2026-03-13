"""
[V9.2 MVVM] 分析视图

重构说明 (V9.2):
- 使用简化后的 AnalysisState 和 AnalysisViewModel
- 磁贴工厂函数签名更新为接收 ViewModel

职责:
- 纯声明式渲染
- 订阅 ViewModel 状态
- 事件委托给 ViewModel

所有业务逻辑已迁移至 AnalysisViewModel
"""
from __future__ import annotations

import asyncio
import flet as ft
from typing import Any, Callable

from ui.states.analysis_state import AnalysisState
from ui.components.analysis.scrubber import GlobalScrubber
from ui.components.analysis.floating_drawer import FloatingDrawer
from ui.components.analysis.tile_container import TileContainer
from ui.components.analysis.history_dialog import HistoryDialog
from ui.components.analysis.toolbox import AnalysisToolbox
from core.logger import get_ui_logger


@ft.component
def TileWrapper(
    item: dict,
    state: AnalysisState,
    set_maximized_tile_id: Callable,
    on_settings: Callable | None = None
):
    """磁贴包装器 - 仅负责 UI 交互映射"""
    instance_id = item['instance_id']

    def handle_close(iid: str):
        get_ui_logger().log_debug(f"UI Triggered Closing: {iid}")
        state.remove_tile(iid)

    return TileContainer(
        key=instance_id,
        tile=item['tile'],
        on_close=handle_close,
        on_maximize=set_maximized_tile_id,
        on_settings=on_settings,
        is_maximized=False
    )


def _create_tile_factory(state: AnalysisState) -> Callable[[str], tuple[Any, tuple[int, int]]]:
    """创建磁贴工厂函数 (V9.2: 接收 State)"""
    def tile_factory(iid: str) -> tuple[Any, tuple[int, int]]:
        tile_type = iid.rsplit('_', 1)[0]
        # 创建下钻处理函数
        def on_drill_down(point: dict):
            state.handle_drill_down(point)

        if tile_type == "dps":
            from ui.components.analysis.dps_tile import DPSChartTile
            return DPSChartTile(state, on_drill_down=on_drill_down), (2, 2)
        elif tile_type == "damage_dist":
            from ui.components.analysis.damage_dist_tile import DamageDistributionTile
            return DamageDistributionTile(state, on_drill_down=on_drill_down), (4, 2)
        elif tile_type == "summary":
            from ui.components.analysis.summary_tile import SummaryTile
            return SummaryTile(state), (2, 1)
        elif tile_type == "stats":
            from ui.components.analysis.stats.stats_tile import CharacterStatsTile
            return CharacterStatsTile(state, iid), (2, 2)
        return None, (1, 1)

    return tile_factory


def _count_tiles_by_type(active_tiles: list[dict]) -> dict[str, int]:
    """统计各类型磁贴数量"""
    type_counts: dict[str, int] = {}
    for t in active_tiles:
        tile_type = t['type']
        type_counts[tile_type] = type_counts.get(tile_type, 0) + 1
    return type_counts


class AnalysisView:
    """
    [V9.2 MVVM] 分析视图
    纯声明式渲染，所有业务逻辑委托给 ViewModel

    模式统一 (V9.2.1):
    - __init__ 接收 AppState（与其他 View 一致）
    - build 接收 AnalysisState 参数（激活 Flet 响应式追踪）
    """
    def __init__(self, app_state):
        self.app_state = app_state

    @ft.component
    def build(self, state: AnalysisState):
        # 通过 state 访问 vm，激活响应式追踪
        vm = state.vm

        # 1. 订阅核心状态 (通过 vm 直接访问)
        active_tiles = vm.active_tiles
        _trigger = vm.update_counter
        is_history_open = vm.history_dialog_visible

        # 2. 本地 UI 状态 (仅用于纯 UI 交互)
        maximized_tile_id, set_maximized_tile_id = ft.use_state(None)

        # 3. 创建磁贴工厂 (依赖 State)
        tile_factory = _create_tile_factory(state)

        # 4. 同步计算布局 (在渲染前)
        if vm.app_state and vm.app_state.page and vm.app_state.page.width:
            container_width = float(vm.app_state.page.width) - 140
        else:
            container_width = vm.container_width

        visible_tiles = [t for t in active_tiles if t['instance_id'] != maximized_tile_id]
        layout_items, total_grid_height = vm._calculate_grid_layout(visible_tiles, container_width)

        # 5. 事件订阅管理
        def setup_events():
            def on_force_refresh(e):
                async def _update():
                    if vm.app_state and vm.app_state.page and vm.app_state.page.width:
                        new_width = float(vm.app_state.page.width) - 140
                        state.set_container_width(
                            new_width, active_tiles, maximized_tile_id
                        )
                if vm.app_state and vm.app_state.page:
                    vm.app_state.page.run_task(_update)

            if vm.app_state and vm.app_state.page:
                vm.app_state.page.pubsub.subscribe(on_force_refresh)

            def cleanup():
                if vm.app_state and vm.app_state.page:
                    vm.app_state.page.pubsub.unsubscribe()
            return cleanup

        ft.use_effect(setup_events, [])

        # 6. Resize 监听 - 触发重新渲染
        def setup_resize() -> None:
            def on_resize(e: Any):
                # 通过 State 代理触发重新渲染
                state._notify_update()
            if vm.app_state and vm.app_state.page:
                vm.app_state.page.on_resize = on_resize

        ft.use_effect(setup_resize, [])

        # 7. 事件处理器 (委托给 VM)
        def handle_tile_settings(iid: str, btn: ft.Control):
            vm.handle_tile_settings(iid, btn, active_tiles)

        def handle_toolbox_action(tid: str):
            state.handle_toolbox_action(tid, tile_factory)

        # 8. 确保未最大化的磁贴状态正确 (已移到布局计算后)
        for t in visible_tiles:
            if hasattr(t['tile'], 'is_maximized'):
                t['tile'].is_maximized = False

        # 9. 聚焦层内容
        focus_content = None
        if is_history_open:
            focus_content = HistoryDialog(
                sessions=vm.sessions_history,
                on_select=lambda sid: [
                    state.load_session(sid),
                    state.close_history()
                ],
                on_close=lambda: state.close_history()
            )
        elif maximized_tile_id:
            max_item = next(
                (t for t in active_tiles if t['instance_id'] == maximized_tile_id),
                None
            )
            if max_item:
                if hasattr(max_item['tile'], 'is_maximized'):
                    max_item['tile'].is_maximized = True

                focus_content = TileContainer(
                    tile=max_item['tile'],
                    on_maximize=lambda _: set_maximized_tile_id(None),
                    on_settings=handle_tile_settings,
                    on_close=lambda _: set_maximized_tile_id(None),
                    is_maximized=True
                )

        # 10. 统计磁贴类型
        type_counts = _count_tiles_by_type(active_tiles)

        # 11. 获取数据槽位
        dist_slot = vm.data_service.get_slot("damage_dist") if vm.data_service else None
        audit_slot = vm.data_service.get_slot("audit") if vm.data_service else None

        # 12. 确保 char_base 数据在线
        async def ensure_base_data():
            if vm.data_service:
                await vm.data_service.subscribe("char_base", "GLOBAL_VIEW")
        ft.use_effect(lambda: [asyncio.create_task(ensure_base_data()), None][1], [])

        # 13. 渲染
        return ft.Stack([
            # 主内容区
            ft.Row([
                # 工具箱
                AnalysisToolbox(
                    active_counts=type_counts,
                    on_tile_action=handle_toolbox_action
                ),
                # 磁贴网格区
                ft.Column([
                    ft.Container(
                        content=ft.Column([
                            ft.Stack(
                                controls=[
                                    ft.Container(
                                        key=f"CONT_{res['item']['instance_id']}",
                                        content=TileWrapper(
                                            res['item'],
                                            state,
                                            set_maximized_tile_id,
                                            handle_tile_settings
                                        ),
                                        left=res['left'],
                                        top=res['top'],
                                        width=res['width'],
                                        height=res['height'],
                                        animate_position=ft.Animation(
                                            600, ft.AnimationCurve.EASE_OUT_EXPO
                                        )
                                    ) for res in layout_items
                                ],
                                height=total_grid_height,
                                expand=False
                            )
                        ], scroll=ft.ScrollMode.ADAPTIVE, expand=True),
                        padding=ft.Padding(left=30, top=20, right=30, bottom=80),
                        expand=True
                    ),
                    # 底部时间轴
                    ft.Container(
                        content=GlobalScrubber(state=state),
                        height=45,
                        bgcolor="#1E1A2A",
                        border=ft.border.only(
                            top=ft.border.BorderSide(1, "rgba(255, 255, 255, 0.08)")
                        ),
                        padding=ft.Padding(left=20, top=0, right=30, bottom=0),
                        alignment=ft.Alignment(0, 0)
                    )
                ], spacing=0, expand=True)
            ], spacing=0, expand=True),

            # 侧边审计抽屉
            FloatingDrawer(
                state=state,
                model=vm,
                dist_slot=dist_slot,
                detail_slot=audit_slot,
                on_fetch_detail=lambda eid: asyncio.create_task(
                    state.load_audit_detail(eid)
                ),
                on_close=lambda: state.close_drawer()
            ),

            # 聚焦层 (对话框/全屏磁贴)
            ft.Container(
                content=ft.Stack([
                    ft.Container(
                        bgcolor="rgba(0,0,0,0.7)",
                        on_click=lambda _: [
                            state.close_history(),
                            set_maximized_tile_id(None)
                        ]
                    ),
                    ft.Container(
                        content=focus_content,
                        padding=40,
                        alignment=ft.Alignment.CENTER
                    ),
                ]),
                visible=focus_content is not None,
                expand=True
            )
        ], expand=True)
