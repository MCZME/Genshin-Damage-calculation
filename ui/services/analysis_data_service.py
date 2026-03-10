"""
[V9.2] 分析数据服务层

重构说明 (V9.2):
- 构造函数参数从 AnalysisState 改为 AnalysisViewModel
- 访问路径: vm.total_frames (原 state.model.total_frames)

职责:
1. 管理缓存（DataSlot）
2. 提供动态数据查询
3. 统一数据访问接口

此服务层替代原有的 AnalysisDataManager，提供更清晰的数据访问抽象。
"""
from __future__ import annotations

import asyncio
import flet as ft
from typing import TYPE_CHECKING, Any
from dataclasses import dataclass, field
from core.persistence.adapter import ReviewDataAdapter
from core.persistence.processors.damage_dist import DamageDistProcessor
from core.logger import get_ui_logger

if TYPE_CHECKING:
    from ui.view_models.analysis.main_vm import AnalysisViewModel


@ft.observable
@dataclass
class DataSlot:
    """[V9.1] 响应式数据槽位：支持基于订阅者集合的自动清理"""
    key: str
    data: Any = None
    loading: bool = False
    subscribers: set = field(default_factory=set)

    @property
    def ref_count(self) -> int:
        return len(self.subscribers)


class AnalysisDataService:
    """
    [V9.2] 数据服务中间层

    重构说明:
    - 构造函数参数从 AnalysisState 改为 AnalysisViewModel
    - 通过 vm 访问状态，无需再通过 state.model

    职责：
    1. 管理缓存（DataSlot）
    2. 提供动态数据查询
    3. 统一数据访问接口
    """

    def __init__(self, vm: 'AnalysisViewModel'):
        self.vm = vm
        self._slots: dict[str, DataSlot] = {
            "dps": DataSlot(key="dps"),
            "summary": DataSlot(key="summary"),
            "audit": DataSlot(key="audit"),
            "damage_dist": DataSlot(key="damage_dist"),
            "char_base": DataSlot(key="char_base"),
        }
        self._lock = asyncio.Lock()
        self._adapter: ReviewDataAdapter | None = None

    @property
    def adapter(self) -> ReviewDataAdapter | None:
        """获取当前适配器"""
        return self._adapter or self.vm.adapter

    @adapter.setter
    def adapter(self, value: ReviewDataAdapter | None):
        """设置适配器"""
        self._adapter = value

    # ============================================================
    # 兼容性属性: state 指向 vm
    # ============================================================

    @property
    def state(self) -> 'AnalysisViewModel':
        """[兼容性] 返回 vm，支持 data_service.state.xxx 访问模式"""
        return self.vm

    # ============================================================
    # 缓存操作
    # ============================================================

    def get_slot(self, key: str) -> DataSlot | None:
        """获取缓存槽位"""
        return self._slots.get(key)

    def get_cached(self, key: str) -> DataSlot | None:
        """获取缓存槽位 (别名)"""
        return self._slots.get(key)

    async def subscribe(self, key: str, instance_id: str) -> DataSlot | None:
        """
        订阅缓存（带引用计数）
        当首个订阅者加入且数据为空时，自动触发数据获取
        """
        if key not in self._slots:
            return None

        async with self._lock:
            slot = self._slots[key]
            slot.subscribers.add(instance_id)
            get_ui_logger().log_debug(
                f"DataService: [{key}] subscribed by {instance_id}. Total: {slot.ref_count}"
            )

            if slot.ref_count > 0 and slot.data is None and not slot.loading:
                await self._fetch_to_cache(key)
            return slot

    async def unsubscribe(self, key: str, instance_id: str) -> None:
        """
        取消订阅
        当引用计数归零时，自动清理缓存
        """
        if key not in self._slots:
            return

        async with self._lock:
            slot = self._slots[key]
            if instance_id in slot.subscribers:
                slot.subscribers.remove(instance_id)
                get_ui_logger().log_debug(
                    f"DataService: [{key}] unsubscribed {instance_id}. Remaining: {slot.ref_count}"
                )

            if slot.ref_count == 0:
                slot.data = None
                slot.loading = False
                get_ui_logger().log_debug(
                    f"DataService: [{key}] data cleared (No references)."
                )

    # ============================================================
    # 内部数据获取
    # ============================================================

    async def _fetch_to_cache(self, key: str) -> None:
        """将数据获取到缓存槽位"""
        adapter = self.adapter
        if not adapter:
            return

        slot = self._slots[key]
        slot.loading = True
        get_ui_logger().log_debug(f"DataService: Fetching data for [{key}]...")

        try:
            if key == "dps":
                raw_events = await adapter.get_dps_data()
                stacked_pts = await adapter.get_stacked_dps_data_raw()
                slot.data = {
                    "raw_events": raw_events,
                    "frame_indices": [p['frame'] for p in raw_events],
                    "stacked_points": stacked_pts
                }
            elif key == "summary":
                slot.data = await adapter.get_summary_stats()
            elif key == "damage_dist":
                raw_events = await adapter.get_raw_damage_events()
                slot.data = DamageDistProcessor.process(raw_events)
                if slot.data:
                    slot.data["total_frames"] = self.vm.total_frames
            elif key == "char_base":
                slot.data = await adapter.get_all_characters_base_stats()

            get_ui_logger().log_debug(f"DataService: [{key}] data ready.")
        except Exception as e:
            get_ui_logger().log_error(f"DataService Error [{key}]: {str(e)}")
        finally:
            slot.loading = False
            # 通知状态更新
            self.vm._notify_update()

    async def refresh_active_slots(self) -> None:
        """重新抓取所有活跃槽位的数据"""
        for key, slot in self._slots.items():
            if slot.ref_count > 0:
                await self._fetch_to_cache(key)

    def invalidate_all_slots(self) -> None:
        """标记所有槽位数据失效"""
        for slot in self._slots.values():
            slot.data = None

    # ============================================================
    # 动态查询（绕过缓存）
    # ============================================================

    async def query_dps_data(self) -> dict[str, Any]:
        """直接查询 DPS 数据（绕过缓存）"""
        adapter = self.adapter
        if not adapter:
            return {}
        return {
            "raw_events": await adapter.get_dps_data(),
            "stacked_points": await adapter.get_stacked_dps_data_raw()
        }

    async def query_frame_snapshot(self, frame_id: int) -> dict[str, Any] | None:
        """查询指定帧的快照数据"""
        adapter = self.adapter
        if not adapter:
            return None
        return await adapter.get_frame(frame_id)

    async def query_char_base_stats(self, char_id: int) -> dict[str, Any]:
        """
        查询角色基础属性
        优先从缓存获取，缓存未命中时从数据库获取
        """
        slot = self._slots.get("char_base")
        if slot and slot.data and char_id in slot.data:
            return slot.data[char_id]

        # 缓存未命中时从数据库获取
        adapter = self.adapter
        if not adapter:
            return {}
        return await adapter.get_all_characters_base_stats().get(char_id, {})

    async def query_damage_audit(self, event_id: int) -> list[dict[str, Any]]:
        """查询伤害审计详情"""
        adapter = self.adapter
        if not adapter:
            return []
        return await adapter.get_damage_audit(event_id)

    async def query_summary_stats(self) -> dict[str, Any]:
        """直接查询汇总统计数据"""
        adapter = self.adapter
        if not adapter:
            return {}
        return await adapter.get_summary_stats()
