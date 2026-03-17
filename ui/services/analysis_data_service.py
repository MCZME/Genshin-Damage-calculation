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

    def __init__(self, vm: "AnalysisViewModel"):
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
    def state(self) -> "AnalysisViewModel":
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
                    "frame_indices": [p["frame"] for p in raw_events],
                    "stacked_points": stacked_pts,
                }
            elif key == "summary":
                slot.data = await adapter.get_summary_stats()
            elif key == "damage_dist":
                raw_events = await adapter.get_damage_events_ui()
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
            "stacked_points": await adapter.get_stacked_dps_data_raw(),
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
        return (await adapter.get_all_characters_base_stats()).get(char_id, {})

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

    # ============================================================
    # [V4.1] Audit 数据装填
    # ============================================================

    async def _fetch_audit_detail(self, event_id: int) -> dict[str, Any]:
        """
        获取审计详情数据（内部方法）

        [V15.0] 重构：业务逻辑移到处理器层，服务层只负责数据协调

        流程：
        1. 获取事件元数据
        2. 拉取原始数据
        3. 调用处理器处理（业务逻辑在处理器层）
        4. 验证（验证逻辑在处理器层）

        Args:
            event_id: 事件 ID

        Returns:
            处理后的审计详情字典
        """
        from core.persistence.processors.audit import AuditProcessor
        from core.persistence.processors.audit.types import (
            DamageType,
            DamageTypeContext,
        )

        adapter = self.adapter
        if not adapter:
            return {}

        # Step 1: 获取事件元数据
        event_meta = await adapter.get_event_metadata(event_id)
        if not event_meta:
            return {}

        frame_id = event_meta.get("frame_id", 0)
        source_id = event_meta.get("source_id")
        target_id = event_meta.get("target_id")
        is_crit = event_meta.get("is_crit", False)
        attack_tag = event_meta.get("attack_tag", "")
        reaction_data = event_meta.get("reaction")
        element_type = event_meta.get("element_type", "")
        final_damage = event_meta.get("final_damage", 0)

        # Step 2: 拉取原始数据
        raw_trail = await adapter.get_damage_audit(event_id)

        frame_snapshot = None
        if source_id is not None:
            frame_snapshot = await adapter.get_entity_snapshot(frame_id, source_id)

        target_snapshot = None
        if target_id is not None:
            target_snapshot = await adapter.get_target_snapshot(frame_id, target_id)

        # Step 3: 使用处理器检测伤害类型
        damage_type = AuditProcessor.detect_damage_type(attack_tag)

        # Step 4: 根据类型选择处理方法
        if damage_type == DamageType.TRANSFORMATIVE:
            # 剧变反应路径
            damage_type_ctx = DamageTypeContext(
                damage_type=DamageType.TRANSFORMATIVE,
                attack_tag=attack_tag,
                level_coeff=0.0,
                reaction_coeff=1.0,
                elemental_mastery=frame_snapshot.get("stats", {}).get("元素精通", 0.0)
                if frame_snapshot
                else 0.0,
                special_bonus=0.0,
            )
            processed = AuditProcessor.process_transformative(
                damage_type_ctx=damage_type_ctx,
                raw_trail=raw_trail,
                frame_snapshot=frame_snapshot,
                target_snapshot=target_snapshot,
                element_type=element_type,
            )
            processed["_damage_type_ctx"] = damage_type_ctx
        else:
            # 常规伤害路径
            processed = AuditProcessor.process_detail(
                raw_trail=raw_trail,
                frame_snapshot=frame_snapshot,
                target_snapshot=target_snapshot,
                is_crit=is_crit,
                element_type=element_type,
            )
            processed["_damage_type_ctx"] = DamageTypeContext()

            # 获取增伤/暴击伤害分项来源（仅常规伤害）
            bonus_stat_names = [
                "伤害加成",
                "火元素伤害加成",
                "水元素伤害加成",
                "冰元素伤害加成",
                "雷元素伤害加成",
                "风元素伤害加成",
                "岩元素伤害加成",
                "草元素伤害加成",
                "物理伤害加成",
            ]
            bonus_modifiers = await adapter.get_entity_modifiers_for_stat(
                event_id, bonus_stat_names
            )
            processed["bonus"]["modifiers"] = bonus_modifiers

            crit_stat_names = ["暴击伤害", "暴击率", "暴击伤害%", "暴击率%"]
            crit_modifiers = await adapter.get_entity_modifiers_for_stat(
                event_id, crit_stat_names
            )

            # [V4.2] 分离暴击率和暴击伤害修饰符
            crit_rate_modifiers = [
                m for m in crit_modifiers if "暴击率" in m.get("stat", "")
            ]
            crit_dmg_modifiers = [
                m for m in crit_modifiers if "暴击伤害" in m.get("stat", "")
            ]

            processed["crit"]["modifiers"] = crit_dmg_modifiers
            processed["crit"]["crit_rate_modifiers"] = crit_rate_modifiers

            # 从帧快照提取暴击率，支持域展示
            if frame_snapshot:
                base_crit_rate = frame_snapshot.get("stats", {}).get("暴击率", 0.0)
                rate_bonus = sum(m.get("value", 0) for m in crit_rate_modifiers)
                processed["crit"]["crit_rate"] = base_crit_rate + rate_bonus

            # [V4.3] 从数据库注入反应数据
            if reaction_data:
                rt_name = reaction_data.get("type", "")
                reaction_type_map = {
                    "VAPORIZE": "蒸发",
                    "MELT": "融化",
                    "AGGRAVATE": "激化",
                    "SPREAD": "超绽放",
                }
                processed["reaction"]["reaction_type"] = reaction_type_map.get(
                    rt_name, rt_name
                )
                processed["reaction"]["reaction_base"] = reaction_data.get(
                    "multiplier", 1.0
                )

                em_bonus = sum(
                    s.get("value", 0)
                    for s in processed["reaction"]["steps"]
                    if s.get("source") == "[精通转化]"
                )
                if em_bonus > 0:
                    processed["reaction"]["em_bonus"] = em_bonus

        # Step 5: [V15.0] 验证（验证逻辑在处理器层）
        validation = AuditProcessor.validate(
            buckets=processed,
            db_damage=final_damage,
            damage_type=damage_type,
            event_id=event_id,
        )
        processed["_validation"] = validation

        return processed

    async def load_audit_detail(self, event_id: int) -> dict[str, Any]:
        """
        公开接口：加载审计详情并填充到 audit slot

        替代 ViewModel 中的 load_audit_detail 逻辑

        Args:
            event_id: 事件 ID

        Returns:
            处理后的审计详情字典
        """
        slot = self._slots.get("audit")
        if not slot:
            return {}

        slot.loading = True
        self.vm._notify_update()

        try:
            processed = await self._fetch_audit_detail(event_id)
            slot.data = processed
            get_ui_logger().log_debug(f"Audit: Event {event_id} processed (V4.1).")
            return processed
        except Exception as e:
            get_ui_logger().log_error(f"Audit Detail Error: {str(e)}")
            return {}
        finally:
            slot.loading = False
            self.vm._notify_update()
