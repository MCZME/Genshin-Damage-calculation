import flet as ft
import asyncio
import uuid
from typing import List, Dict, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from core.persistence.adapter import ReviewDataAdapter
from core.persistence.processors.damage_dist import DamageDistProcessor
from core.logger import get_ui_logger

@ft.observable
@dataclass
class DataSlot:
    """[V4.8] 响应式数据槽位：支持基于订阅者集合的自动清理"""
    key: str
    data: Any = None
    loading: bool = False
    subscribers: set = field(default_factory=set)

    @property
    def ref_count(self) -> int:
        return len(self.subscribers)

class AnalysisDataManager:
    """
    [V4.8] 复盘数据生命周期管理器 (集合驱动版)
    """
    def __init__(self, state: 'AnalysisState'):
        self.state = state
        self._slots: Dict[str, DataSlot] = {
            "dps": DataSlot(key="dps"),
            "summary": DataSlot(key="summary"),
            "audit": DataSlot(key="audit"),
            "damage_dist": DataSlot(key="damage_dist"), # 新增伤害分布槽位
        }
        self._lock = asyncio.Lock()

    def get_slot(self, key: str) -> Optional[DataSlot]:
        return self._slots.get(key)

    async def subscribe(self, key: str, instance_id: str):
        if key not in self._slots:
            return None
        
        async with self._lock:
            slot = self._slots[key]
            slot.subscribers.add(instance_id)
            get_ui_logger().log_debug(f"DataManager: [{key}] subscribed by {instance_id}. Total: {slot.ref_count}")
            
            if slot.ref_count > 0 and slot.data is None and not slot.loading:
                await self._fetch_data(key)
            return slot

    async def unsubscribe(self, key: str, instance_id: str):
        if key not in self._slots:
            return
        
        async with self._lock:
            slot = self._slots[key]
            if instance_id in slot.subscribers:
                slot.subscribers.remove(instance_id)
                get_ui_logger().log_debug(f"DataManager: [{key}] unsubscribed {instance_id}. Remaining: {slot.ref_count}")
            
            if slot.ref_count == 0:
                slot.data = None
                slot.loading = False
                get_ui_logger().log_debug(f"DataManager: [{key}] data cleared (No references).")

    async def _fetch_data(self, key: str):
        if not self.state.adapter:
            return
            
        slot = self._slots[key]
        slot.loading = True
        get_ui_logger().log_debug(f"DataManager: Fetching data for [{key}]...")
        
        try:
            if key == "dps":
                raw_events = await self.state.adapter.get_dps_data()
                stacked_pts = await self.state.adapter.get_stacked_dps_data()
                slot.data = {
                    "raw_events": raw_events,
                    "frame_indices": [p['frame'] for p in raw_events],
                    "stacked_points": stacked_pts
                }
            elif key == "summary":
                slot.data = await self.state.adapter.get_summary_stats()
            elif key == "damage_dist":
                # [V6.6] 编排逻辑：从适配器拉取原始事件流 -> 传给专项处理器加工 ViewModel
                raw_events = await self.state.adapter.get_raw_damage_events()
                slot.data = DamageDistProcessor.process(raw_events)
                
                # 注入总帧数支持 (如果数据中不包含)
                if slot.data:
                    slot.data["total_frames"] = self.state.model.total_frames
            
            get_ui_logger().log_debug(f"DataManager: [{key}] data ready.")
        except Exception as e:
            get_ui_logger().log_error(f"DataManager Error [{key}]: {str(e)}")
        finally:
            slot.loading = False
            # [V6.3] 数据就绪后强制通知 UI 刷新
            if hasattr(self.state, '_notify_update'):
                self.state._notify_update()

@ft.observable
@dataclass
class AnalysisStateModel:
    """全局仿真复盘元状态模型"""
    current_session_id: Optional[int] = None
    loading: bool = False
    sessions_history: List[Dict[str, Any]] = field(default_factory=list)
    current_frame: int = 0
    total_frames: int = 0
    active_tiles: List[Dict[str, Any]] = field(default_factory=list)
    # [V6.1] 强制更新触发器：用于解决复杂嵌套下的重绘失效
    update_counter: int = 0

class AnalysisState:
    """
    [V6.1 业务驱动生命周期协调者]
    """
    def __init__(self, app_state=None):
        self.app_state = app_state
        self.model = AnalysisStateModel()
        self.adapter: Optional[ReviewDataAdapter] = None
        self.data_manager = AnalysisDataManager(self)
        
        self.selected_audit_index = -1
        self.current_audit = None
        self.audit_logs = []

    def _notify_update(self):
        """强制触发 Observable 变更通知"""
        self.model.update_counter += 1
        # [V6.2] 暴力强刷：通过 PubSub 通知 View 层重绘
        if self.app_state and self.app_state.page:
            self.app_state.page.pubsub.send_all("analysis_view_refresh")

    def add_tile(self, tile_type: str, factory_func: Callable):
        """[Mutation] 添加磁贴 (V6.5 模块化尺寸适配)"""
        instance_id = f"{tile_type}_{uuid.uuid4().hex[:8]}"
        
        # 工厂函数现在返回 (tile_instance, grid_size)
        # grid_size 是一个 (width_units, height_units) 元组
        tile_instance, grid_size = factory_func(self, instance_id)
        tile_instance.instance_id = instance_id
        
        tile_data = {
            'instance_id': instance_id,
            'type': tile_type,
            'tile': tile_instance,
            'grid_size': grid_size if grid_size else (1, 1) # 默认 1x1
        }
        
        # 不可变更新
        new_list = list(self.model.active_tiles)
        new_list.append(tile_data)
        self.model.active_tiles = new_list
        self._notify_update()
        
        async def _sub():
            await self.data_manager.subscribe(tile_type, instance_id)
        asyncio.create_task(_sub())
        return instance_id

    def remove_tile(self, instance_id: str):
        """[Mutation] 移除磁贴"""
        target = next((t for t in self.model.active_tiles if t['instance_id'] == instance_id), None)
        if not target:
            return

        self.model.active_tiles = [t for t in self.model.active_tiles if t['instance_id'] != instance_id]
        self._notify_update()
        
        async def _unsub():
            await self.data_manager.unsubscribe(target['type'], instance_id)
        asyncio.create_task(_unsub())

    def load_session(self, session_id: int):
        self.model.current_session_id = session_id
        self.model.loading = True
        self.adapter = ReviewDataAdapter(session_id=session_id)
        
        for slot in self.data_manager._slots.values():
            slot.data = None
            
        async def _fetch_meta():
            stats = await self.adapter.get_summary_stats()
            self.model.total_frames = int(stats.get("total_frames", 0))
            self.model.loading = False
            
            if self.app_state:
                self.app_state.events.notify("analysis_session_changed", session_id)
                
            for tile in self.model.active_tiles:
                await self.data_manager.subscribe(tile['type'], tile['instance_id'])
            self._notify_update()
        
        asyncio.create_task(_fetch_meta())

    def set_frame(self, frame_id: int):
        if self.model.current_frame != frame_id:
            self.model.current_frame = frame_id

    def load_history_list(self):
        adapter = ReviewDataAdapter()
        async def _task():
            self.model.sessions_history = await adapter.get_all_sessions()
            if self.app_state:
                self.app_state.events.notify("analysis_history_ready")
            self._notify_update()
        asyncio.create_task(_task())

    def select_audit(self, index: int):
        if 0 <= index < len(self.audit_logs):
            self.selected_audit_index = index
            item = self.audit_logs[index]
            async def _load_detail():
                trail = await self.adapter.get_damage_audit(item['event_id'])
                item['audit_trail'] = trail
                self.current_audit = item
                if self.app_state:
                    self.app_state.events.notify("audit_detail_ready")
                self._notify_update()
            asyncio.create_task(_load_detail())

    def refresh_data(self):
        sid = getattr(self.app_state, "last_session_id", None)
        if sid:
            self.load_session(sid)
