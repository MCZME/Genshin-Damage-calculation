import flet as ft
import asyncio
from typing import List, Dict, Any, Optional
from core.persistence.adapter import ReviewDataAdapter

class AnalysisState:
    """
    [V4.5 状态协调者]
    不再存储具体数据，仅管理 SessionID、加载状态和全局事件。
    """
    def __init__(self, app_state=None):
        self.app_state = app_state
        
        # 核心元数据
        self.current_session_id: Optional[int] = None
        self.loading = False
        self.adapter: Optional[ReviewDataAdapter] = None
        
        # 历史记录缓存 (仅保留轻量级索引)
        self.sessions_history = []
        
        # 审计交互状态 (保留)
        self.selected_audit_index = -1
        self.audit_logs = [] # 这是一个由 DPS 磁贴加载后同步回来的引用

    def load_session(self, session_id: int):
        """切换会话：仅设置 ID 并发出广播，驱动所有磁贴自主刷新"""
        self.current_session_id = session_id
        self.adapter = ReviewDataAdapter(session_id=session_id)
        
        # 发出广播信号：数据源已切换
        if self.app_state:
            self.app_state.events.notify("analysis_session_changed", session_id)

    def load_history_list(self):
        """加载历史列表 (轻量级请求)"""
        adapter = ReviewDataAdapter()
        async def _task():
            self.sessions_history = await adapter.get_all_sessions()
            if self.app_state:
                self.app_state.events.notify("analysis_history_ready")
        
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_task())
        except:
            asyncio.run(_task())

    def refresh_data(self):
        """外部主动触发刷新逻辑"""
        sid = getattr(self.app_state, "last_session_id", None)
        if sid: self.load_session(sid)
