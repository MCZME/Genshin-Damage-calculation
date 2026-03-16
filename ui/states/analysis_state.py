"""
[V9.2 MVVM 重构] 分析状态模块

重构说明 (V9.2):
- AnalysisStateModel 已删除，字段合并到 AnalysisViewModel
- AnalysisState 简化为 ViewModel 工厂

架构分层:
- AnalysisViewModel: 状态持有 + 业务逻辑 (ui/view_models/analysis/main_vm.py)
- AnalysisDataService: 数据服务层，管理缓存和动态数据查询
- AnalysisState: 工厂
"""
from __future__ import annotations

import flet as ft
import asyncio
from typing import TYPE_CHECKING, Any

from core.persistence.adapter import ReviewDataAdapter
from core.logger import get_ui_logger

if TYPE_CHECKING:
    from ui.states.app_state import AppState
    from ui.view_models.analysis.main_vm import AnalysisViewModel


@ft.observable
class AnalysisState:
    """
    [V9.2 MVVM] ViewModel 工厂 + 兼容性代理

    职责：
    1. 创建并持有 AnalysisViewModel
    2. 创建并持有 DataService

    所有业务逻辑已迁移至 AnalysisViewModel
    """
    def __init__(self, app_state: 'AppState | None' = None):
        self.app_state = app_state

        # 延迟导入避免循环依赖
        from ui.view_models.analysis.main_vm import AnalysisViewModel
        from ui.services.analysis_data_service import AnalysisDataService

        # 创建 ViewModel
        self.vm: AnalysisViewModel = AnalysisViewModel(app_state=app_state)

        # 注册响应式回调 (VM 变更时触发 Flet 响应式更新)
        self.vm._notify_callback = self._notify_update

        # 创建 DataService 并关联
        self.data_service = AnalysisDataService(self.vm)
        self.vm.data_service = self.data_service

        # 审计相关状态 (保留供兼容)
        self.selected_audit_index: int = -1
        self.current_audit: Any | None = None
        self.audit_logs: list[Any] = []

    def _notify_update(self):
        """触发 Observable 变更通知 (供 ViewModel 调用)"""
        self.notify()

    # ============================================================
    # 兼容性方法 (保持与现有组件的兼容性)
    # 这些方法代理到 ViewModel
    # ============================================================

    def set_frame(self, frame_id: int):
        """设置当前帧 (兼容性方法)"""
        self.vm.set_frame(frame_id)
        self._notify_update()

    def set_tile_char(self, instance_id: str, char_id: int):
        """设置特定磁贴实例关注的角色 (兼容性方法)"""
        self.vm.set_tile_char(instance_id, char_id)

    def get_tile_char(self, instance_id: str) -> int:
        """获取磁贴实例关注的角色 ID (兼容性方法)"""
        return self.vm.get_tile_char(instance_id)

    def get_stat_preferences(self, char_id: int) -> list[str]:
        """获取角色的展示偏好"""
        return self.vm.get_stat_preferences(char_id)

    def toggle_stat_preference(self, char_id: int, stat_key: str):
        """切换角色属性的展示偏好"""
        self.vm.toggle_stat_preference(char_id, stat_key)

    def run_task(self, coro):
        """运行异步任务"""
        self.vm.run_task(coro)

    def refresh_data(self):
        """刷新数据 (兼容性方法 - 供外部导航调用)"""
        sid = getattr(self.app_state, "last_session_id", None)
        if sid and self.vm.current_session_id != sid:
            self.vm.current_session_id = sid
            self.vm.loading = True
            self.vm.adapter = ReviewDataAdapter(session_id=sid)
            self.data_service.adapter = self.vm.adapter
            self.data_service.invalidate_all_slots()

            async def _fetch_meta():
                if not self.vm.adapter:
                    return
                try:
                    stats = await self.vm.adapter.get_summary_stats()
                    self.vm.total_frames = int(stats.get("total_frames", 0))
                    await self.data_service.refresh_active_slots()
                except Exception as e:
                    get_ui_logger().log_error(f"refresh_data error: {e}")
                finally:
                    self.vm.loading = False
                    self.vm._notify_update()

            asyncio.create_task(_fetch_meta())

    # ============================================================
    # 代理方法 (状态变更通过 State 触发响应式更新)
    # ============================================================

    def set_container_width(
        self,
        width: float,
        active_tiles: list[dict] | None = None,
        maximized_tile_id: str | None = None
    ):
        """更新容器宽度并触发布局重算"""
        self.vm.set_container_width(width, active_tiles, maximized_tile_id)

    def refresh_layout(
        self,
        active_tiles: list[dict] | None = None,
        maximized_tile_id: str | None = None
    ):
        """刷新布局"""
        self.vm.refresh_layout(active_tiles, maximized_tile_id)

    def add_tile(
        self,
        tile_type: str,
        tile_factory
    ) -> str | None:
        """添加磁贴"""
        return self.vm.add_tile(tile_type, tile_factory)

    def remove_tile(self, instance_id: str):
        """移除磁贴"""
        self.vm.remove_tile(instance_id)

    def load_session(self, session_id: int):
        """加载复盘会话"""
        self.vm.load_session(session_id)

    def load_history_list(self):
        """加载历史会话列表"""
        self.vm.load_history_list()

    def close_history(self):
        """关闭历史记录对话框"""
        self.vm.close_history()

    def open_drawer(self, side: str = "right"):
        """打开侧边抽屉"""
        self.vm.open_drawer(side)

    def close_drawer(self):
        """关闭侧边抽屉"""
        self.vm.close_drawer()

    def handle_drill_down(self, point: dict):
        """下钻：切换帧并打开审计抽屉"""
        self.vm.handle_drill_down(point)

    def handle_toolbox_action(self, action_id: str, tile_factory):
        """处理工具箱操作"""
        self.vm.handle_toolbox_action(action_id, tile_factory)

    async def load_audit_detail(self, event_id: int):
        """异步加载审计详情"""
        await self.vm.load_audit_detail(event_id)

    def set_selected_event(self, event: dict[str, Any] | None):
        """设置当前选中的伤害事件"""
        self.vm.set_selected_event(event)

    # ============================================================
    # [V11.0] 面板模式控制代理方法
    # ============================================================

    def set_panel_mode(self, mode: str):
        """设置面板模式"""
        self.vm.set_panel_mode(mode)

    def switch_to_audit(self, event: dict):
        """切换到审计面板并加载事件详情"""
        self.vm.switch_to_audit(event)

    def switch_to_selection(self):
        """返回选择面板"""
        self.vm.switch_to_selection()
