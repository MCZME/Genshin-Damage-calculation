import flet as ft
import asyncio
from typing import List, Dict, Any, Optional
from core.persistence.adapter import ReviewDataAdapter


class DamageAuditItem:
    """
    单笔伤害的审计数据模型。
    """
    def __init__(self, frame: int, char_name: str, action: str, total_dmg: float, event_id: int):
        self.frame = frame
        self.char_name = char_name
        self.action = action
        self.total_dmg = total_dmg
        self.event_id = event_id

        # 公式拆解 (扁平化展示) - 初始值
        self.multiplier_sum = 0.0
        self.atk_final = 0.0
        self.dmg_bonus = 0.0
        self.crit_factor = 1.0
        self.def_factor = 0.0
        self.res_factor = 0.0
        self.reaction_mult = 1.0

        # 审计标签 (谁给了加成)
        self.claims = []

    def update_from_audit(self, audit_steps: List[Dict[str, Any]]):
        """将 adapter.get_damage_audit 返回的步骤映射到公式因子"""
        # 简单实现：将所有 source_name 放入 claims
        self.claims = [f"{s['source']} ({s['stat']}: {s['value']})" for s in audit_steps]
        
        # 核心因子提取 (根据 core/systems/damage_system.py 中的 stat 命名)
        for s in audit_steps:
            st = s['stat']
            val = s['value']
            if st == "攻击力": self.atk_final = val
            elif st == "伤害加成": self.dmg_bonus = val / 100.0 # 存储的是百分比
            elif st == "暴击乘数": self.crit_factor = val
            elif st == "防御区系数": self.def_factor = val
            elif st == "抗性区系数": self.res_factor = val
            elif st == "反应基础倍率": self.reaction_mult = val
            elif st == "技能倍率": self.multiplier_sum = val / 100.0
            elif st == "最终伤害": self.total_dmg = val # 保底更新一次最终值

class AnalysisState:
    """
    分析视图的状态管理器 (同步接口版)。
    """
    def __init__(self, app_state=None):
        self.app_state = app_state

        self.summary = {
            "total_dmg": 0,
            "avg_dps": 0,
            "duration": 0,
            "peak_dps": 0
        }

        self.dps_points = []
        self.aura_track = []
        self.action_tracks = {} # 角色动作轨道
        self.trajectories = {} # 全场轨迹
        self.energy_data = {} # 角色能量轨道
        self.lifecycles = []
        self.reaction_stats = {}
        self.mechanism_trajectories = {}
        self.audit_logs: List[DamageAuditItem] = []
        self.selected_audit_index = -1
        self.sessions_history = [] # 历史会话列表

        self.loading = False
        self.adapter: Optional[ReviewDataAdapter] = None

    def load_session(self, session_id: int):
        """同步加载指定会话的所有分析数据 (内部处理异步)"""
        self.loading = True
        self.adapter = ReviewDataAdapter(session_id=session_id)

        # 检查当前是否已在运行的事件循环中
        try:
            loop = asyncio.get_running_loop()
            # 如果在循环中，通过 create_task 异步执行，不阻塞 UI
            loop.create_task(self._load_session_async())
        except RuntimeError:
            # 不在循环中，可以使用 asyncio.run
            asyncio.run(self._load_session_async())

    async def _load_session_async(self):
        """异步加载数据的实际实现"""
        from core.logger import get_ui_logger
        get_ui_logger().log_info(f"AnalysisState: _load_session_async started for SID {self.adapter.session_id}")
        try:
            # 1. 加载摘要
            stats = await self.adapter.get_summary_stats()
            self.summary = {
                "total_dmg": stats["total_damage"],
                "avg_dps": stats["avg_dps"],
                "duration": stats["duration_seconds"],
                "peak_dps": stats["peak_dps"]
            }
            get_ui_logger().log_info(f"AnalysisState: Summary loaded. DMG={self.summary['total_dmg']}")

            # 2. 加载伤害点 (用于曲线)
            raw_dps = await self.adapter.get_dps_data()
            self.dps_points = raw_dps
            get_ui_logger().log_info(f"AnalysisState: Loaded {len(raw_dps)} DPS points.")

            # 3. 加载元素与动作轨道
            self.aura_track = await self.adapter.get_aura_pulses()
            self.action_tracks = await self.adapter.get_action_tracks()
            self.trajectories = await self.adapter.get_all_pulses()
            self.energy_data = await self.adapter.get_energy_data()
            self.lifecycles = await self.adapter.get_full_lifecycles()
            self.reaction_stats = await self.adapter.get_reaction_stats()
            self.mechanism_trajectories = await self.adapter.get_mechanism_data()
            get_ui_logger().log_info(f"AnalysisState: All tracks loaded.")

            # 4. 初始化审计列表
            self.audit_logs = [
                DamageAuditItem(
                    frame=p["frame"],
                    char_name=p["source"],
                    action=p.get("action", "伤害触发"),
                    total_dmg=p["value"],
                    event_id=p["event_id"]
                ) for p in raw_dps
            ]
        except Exception as e:
            import traceback
            get_ui_logger().log_error(f"AnalysisState: Load failed: {e}\n{traceback.format_exc()}")
        finally:
            self.loading = False
            get_ui_logger().log_info("AnalysisState: Loading finished, notifying UI via 'analysis' event.")
            # 通知 UI 数据加载完成
            if self.app_state:
                self.app_state.events.notify("analysis")

    def refresh_data(self):
        """外部主动触发刷新"""
        sid = getattr(self.app_state, "last_session_id", None)
        if sid:
            self.state.load_session(sid)

    def load_history_list(self):
        """同步触发加载历史列表"""
        adapter = ReviewDataAdapter()
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._load_history_async(adapter))
        except RuntimeError:
            asyncio.run(self._load_history_async(adapter))

    async def _load_history_async(self, adapter):
        self.sessions_history = await adapter.get_all_sessions()
        if self.app_state:
            self.app_state.events.notify("analysis_history_ready")

    def select_audit(self, index: int):
        """同步下钻具体伤害点的审计明细 (内部处理异步)"""
        if 0 <= index < len(self.audit_logs):
            self.selected_audit_index = index
            item = self.audit_logs[index]

            # 如果尚未加载明细，则从数据库抓取
            if not item.claims and self.adapter:
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(self._select_audit_async(item))
                except RuntimeError:
                    asyncio.run(self._select_audit_async(item))

    async def _select_audit_async(self, item: DamageAuditItem):
        """异步加载审计明细的实际实现"""
        audit_steps = await self.adapter.get_damage_audit(item.event_id)
        item.update_from_audit(audit_steps)
        # 通知 UI 局部刷新审计面板，避免全量重绘
        if self.app_state:
            self.app_state.events.notify("audit_detail_ready")

    @property
    def current_audit(self):
        if 0 <= self.selected_audit_index < len(self.audit_logs):
            return self.audit_logs[self.selected_audit_index]
        return None
