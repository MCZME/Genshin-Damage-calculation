"""
[V9.2 MVVM] 分析视图 ViewModel

重构说明 (V9.2):
- 原 AnalysisStateModel 字段已合并到此类
- 访问路径简化: vm.current_frame
- ViewModel 直接持有所有状态字段

职责:
1. 管理磁贴的网格布局计算
2. 磁贴管理 (添加/移除/创建)
3. 会话管理 (加载/历史)
4. 帧控制
5. 抽屉控制
6. 事件处理 (下钻/工具箱操作)
7. 审计详情加载
8. 角色焦点管理
"""
from __future__ import annotations

import flet as ft
import asyncio
import uuid
from typing import TYPE_CHECKING, Any, Callable

from core.persistence.adapter import ReviewDataAdapter
from core.logger import get_ui_logger
from ui.view_models.analysis.tile_vms.types import DEFAULT_STATS

if TYPE_CHECKING:
    from ui.states.app_state import AppState
    from ui.services.analysis_data_service import AnalysisDataService


# --- Grid Configuration [V4.0 Final] ---
CELL_SIZE = 160
GUTTER = 16


class AnalysisViewModel:
    """
    [V9.2] 分析视图 ViewModel - 状态与业务逻辑中心

    原 AnalysisStateModel 字段已合并于此:
    - current_session_id, loading, sessions_history
    - current_frame, total_frames
    - active_tiles, drawer_visible, drawer_side
    - selected_event, focus_char_id
    - tile_instance_configs, char_display_preferences
    - history_dialog_visible

    注意: 不再使用 @ft.observable 装饰器
    Flet 响应式机制不会递归追踪嵌套的 observable 对象，
    因此所有状态变更通过 AnalysisState.notify() 触发更新。
    """
    def __init__(self, app_state: 'AppState | None' = None):
        # ============================================================
        # 原 AnalysisStateModel 字段 (V9.2 合并)
        # ============================================================
        self.current_session_id: int | None = None
        self.loading: bool = False
        self.sessions_history: list[dict[str, Any]] = []
        self.current_frame: int = 0
        self.total_frames: int = 0
        self.active_tiles: list[dict[str, Any]] = []
        self.drawer_visible: bool = False
        self.drawer_side: str = "right"
        self.selected_event: dict[str, Any] | None = None
        self.focus_char_id: int | None = None
        self.tile_instance_configs: dict[str, dict[str, Any]] = {}
        self.char_display_preferences: dict[int, list[str]] = {}
        self.history_dialog_visible: bool = False

        # ============================================================
        # [V9.5 Pro V2] 状态条选中状态
        # ============================================================
        self.status_bar_selection: dict[str, list[str]] = {}  # instance_id -> ["血条", "能量条"]

        # ============================================================
        # 布局状态
        # ============================================================
        self.container_width: float = 1200.0
        self.layout_items: list[dict] = []
        self.total_grid_height: float = 0.0
        self.update_counter: int = 0

        # ============================================================
        # 服务引用
        # ============================================================
        self.app_state = app_state
        self.adapter: ReviewDataAdapter | None = None
        self.data_service: 'AnalysisDataService | None' = None

        # ============================================================
        # 响应式回调 (由 AnalysisState 注册)
        # ============================================================
        self._notify_callback: Callable[[], None] | None = None

    # ============================================================
    # 布局计算
    # ============================================================

    def set_container_width(
        self,
        width: float,
        active_tiles: list[dict] | None = None,
        maximized_tile_id: str | None = None
    ):
        """更新容器宽度并触发布局重算"""
        if self.container_width != width:
            self.container_width = width
            tiles = active_tiles if active_tiles is not None else self.active_tiles
            self.refresh_layout(tiles, maximized_tile_id)

    def refresh_layout(
        self,
        active_tiles: list[dict] | None = None,
        maximized_tile_id: str | None = None
    ):
        """[V5.0 核心逻辑] 自动计算网格布局结果并缓存"""
        tiles = active_tiles if active_tiles is not None else self.active_tiles
        visible_tiles = [
            t for t in tiles
            if t['instance_id'] != maximized_tile_id
        ]

        self.layout_items, self.total_grid_height = self._calculate_grid_layout(
            visible_tiles, self.container_width
        )
        self.update_counter += 1

    def _calculate_grid_layout(
        self,
        items: list[dict],
        available_width: float
    ) -> tuple[list[dict], float]:
        """[Internal] 核心网格布局算法"""
        if not available_width or available_width < 100:
            return [], 0

        cols = max(1, int((available_width + GUTTER) / (CELL_SIZE + GUTTER)))
        occupied: list[tuple[int, int]] = []
        max_y = 0
        layout_results = []

        for item in items:
            orig_w, orig_h = item.get('grid_size', (1, 1))
            eff_w = min(orig_w, cols)

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
                        if not is_free:
                            break

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

    # ============================================================
    # 磁贴管理
    # ============================================================

    def add_tile(
        self,
        tile_type: str,
        tile_factory: Callable[[str], tuple[Any, tuple[int, int]]]
    ) -> str | None:
        """添加磁贴"""
        instance_id = f"{tile_type}_{uuid.uuid4().hex[:8]}"
        tile_instance, grid_size = tile_factory(instance_id)

        if not tile_instance:
            return None

        tile_instance.instance_id = instance_id

        tile_data = {
            'instance_id': instance_id,
            'type': tile_type,
            'tile': tile_instance,
            'grid_size': grid_size if grid_size else (1, 1)
        }

        new_list = list(self.active_tiles)
        new_list.append(tile_data)
        self.active_tiles = new_list
        self._notify_update()

        if self.data_service:
            async def _sub():
                await self.data_service.subscribe(tile_type, instance_id)
            asyncio.create_task(_sub())

        return instance_id

    def remove_tile(self, instance_id: str):
        """移除磁贴"""
        target = next(
            (t for t in self.active_tiles if t['instance_id'] == instance_id),
            None
        )
        if not target:
            return

        self.active_tiles = [
            t for t in self.active_tiles
            if t['instance_id'] != instance_id
        ]
        self._notify_update()

        if self.data_service and target:
            async def _unsub():
                await self.data_service.unsubscribe(target['type'], instance_id)
            asyncio.create_task(_unsub())

    # ============================================================
    # 会话管理
    # ============================================================

    def load_session(self, session_id: int):
        """加载复盘会话"""
        self.current_session_id = session_id
        self.loading = True
        self.adapter = ReviewDataAdapter(session_id=session_id)

        # 同步 adapter 到 data_service
        if self.data_service:
            self.data_service.adapter = self.adapter
            self.data_service.invalidate_all_slots()

        async def _fetch_meta():
            if not self.adapter:
                return
            try:
                stats = await self.adapter.get_summary_stats()
                self.total_frames = int(stats.get("total_frames", 0))

                # 重新抓取活跃槽位数据
                if self.data_service:
                    await self.data_service.refresh_active_slots()

                get_ui_logger().log_info(
                    f"AnalysisViewModel: Session {session_id} loaded "
                    f"with {self.total_frames} frames."
                )
            except Exception as e:
                get_ui_logger().log_error(
                    f"AnalysisViewModel: Failed to load session meta: {e}"
                )
            finally:
                self.loading = False
                self._notify_update()

        asyncio.create_task(_fetch_meta())

    def load_history_list(self):
        """加载历史会话列表"""
        adapter = ReviewDataAdapter()

        async def _task():
            self.sessions_history = await adapter.get_all_sessions()
            self.history_dialog_visible = True
            self._notify_update()

        asyncio.create_task(_task())

    def close_history(self):
        """关闭历史记录对话框"""
        self.history_dialog_visible = False
        self._notify_update()

    # ============================================================
    # 帧控制
    # ============================================================

    def set_frame(self, frame_id: int):
        """设置当前帧"""
        if self.current_frame != frame_id:
            self.current_frame = frame_id

    # ============================================================
    # 抽屉控制
    # ============================================================

    def open_drawer(self, side: str = "right"):
        """打开侧边抽屉"""
        self.drawer_side = side
        self.drawer_visible = True
        self._notify_update()

    def close_drawer(self):
        """关闭侧边抽屉"""
        self.drawer_visible = False
        self._notify_update()

    # ============================================================
    # 事件处理 (从 View 迁移)
    # ============================================================

    def handle_drill_down(self, point: dict):
        """下钻：切换帧并打开审计抽屉"""
        self.set_frame(int(point['frame']))
        self.open_drawer(side="right")

        if 'event_id' in point:
            asyncio.create_task(self.load_audit_detail(point['event_id']))

    def handle_toolbox_action(
        self,
        action_id: str,
        tile_factory: Callable
    ):
        """处理工具箱操作"""
        if action_id == "history":
            self.load_history_list()
            return
        self.add_tile(action_id, tile_factory)

    def handle_tile_settings(
        self,
        instance_id: str,
        btn: ft.Control,
        active_tiles: list[dict]
    ):
        """处理磁贴设置点击"""
        target_tile = next(
            (t['tile'] for t in active_tiles if t['instance_id'] == instance_id),
            None
        )
        if target_tile and hasattr(target_tile, "on_settings_click"):
            target_tile.on_settings_click(btn)

    # ============================================================
    # 审计详情
    # ============================================================

    async def load_audit_detail(self, event_id: int):
        """异步加载 L2 审计详情"""
        if not self.adapter or not self.data_service:
            return

        from core.persistence.processors.audit_processor import AuditProcessor

        slot = self.data_service.get_slot("audit")
        if not slot:
            return

        slot.loading = True
        self._notify_update()

        try:
            # 查找基础事件信息 (用于判断是否暴击)
            dist_slot = self.data_service.get_slot("damage_dist")
            is_crit = False
            if dist_slot and dist_slot.data:
                for f_data in dist_slot.data.get("frame_map", {}).values():
                    for ev in f_data.get("events", []):
                        if ev['event_id'] == event_id:
                            is_crit = ev.get('is_crit', False)
                            break

            # 拉取原始审计链
            raw_trail = await self.adapter.get_damage_audit(event_id)

            # 聚合加工
            processed = AuditProcessor.process_detail(raw_trail, is_crit=is_crit)
            slot.data = processed

            get_ui_logger().log_debug(f"Audit: Event {event_id} processed.")
        except Exception as e:
            get_ui_logger().log_error(f"Audit Detail Error: {str(e)}")
        finally:
            slot.loading = False
            self._notify_update()

    # ============================================================
    # 角色焦点管理
    # ============================================================

    def set_tile_char(self, instance_id: str, char_id: int):
        """设置特定磁贴实例关注的角色"""
        if instance_id not in self.tile_instance_configs:
            self.tile_instance_configs[instance_id] = {}
        self.tile_instance_configs[instance_id]["target_char_id"] = char_id
        self._notify_update()

    def get_tile_char(self, instance_id: str) -> int:
        """获取磁贴实例关注的角色 ID，回退到全局焦点或 0"""
        config = self.tile_instance_configs.get(instance_id, {})
        return config.get("target_char_id") or self.focus_char_id or 0

    def toggle_stat_preference(self, char_id: int, stat_key: str):
        """[V9.5 Pro V2] 切换角色属性的展示偏好

        组件项（血条、能量条、状态效果）不受 8 项限制
        """
        # 组件项：控制状态条和效果墙显示，不受数量限制
        COMPONENT_KEYS = ["血条", "能量条", "状态效果"]

        if char_id not in self.char_display_preferences:
            # [V9.12] 修复：初次设置时应基于默认列表进行切换，防止“崩溃式添加”
            self.char_display_preferences[char_id] = list(DEFAULT_STATS)

        prefs = self.char_display_preferences[char_id]
        if stat_key in prefs:
            prefs.remove(stat_key)
        else:
            # 组件项不受 8 项限制
            if stat_key in COMPONENT_KEYS or len(prefs) < 8:
                prefs.append(stat_key)
        self._notify_update()

    def get_stat_preferences(self, char_id: int) -> list[str]:
        """获取角色的展示偏好"""
        return self.char_display_preferences.get(char_id, [])

    def toggle_status_bar_selection(self, instance_id: str, selection: str):
        """[V9.5 Pro V2] 切换状态条选中状态 (多选支持)

        Args:
            instance_id: 磁贴实例 ID
            selection: 要切换的状态项名称
        """
        if instance_id not in self.status_bar_selection:
            # [V9.11] 修复：初次从全显状态切换时，应初始化为全选，确保点击是“取消”逻辑
            self.status_bar_selection[instance_id] = ["血条", "能量条"]
        
        prefs = self.status_bar_selection[instance_id]
        if selection in prefs:
            prefs.remove(selection)
        else:
            prefs.append(selection)
            
        self._notify_update()

    def get_status_bar_selection(self, instance_id: str) -> list[str] | None:
        """[V9.5 Pro V2] 获取状态条选中状态

        Args:
            instance_id: 磁贴实例 ID

        Returns:
            选中项列表，若从未设置过则返回 None
        """
        return self.status_bar_selection.get(instance_id)

    def set_selected_event(self, event: dict[str, Any] | None):
        """设置当前选中的伤害事件"""
        self.selected_event = event
        self._notify_update()

    # ============================================================
    # 异步任务运行器
    # ============================================================

    def run_task(self, coro):
        """运行异步任务"""
        if self.app_state and self.app_state.page:
            self.app_state.page.run_task(coro)
        else:
            asyncio.create_task(coro)

    # ============================================================
    # 内部通知
    # ============================================================

    def _notify_update(self):
        """通知 State 触发 Flet 响应式更新"""
        if self._notify_callback:
            self._notify_callback()
