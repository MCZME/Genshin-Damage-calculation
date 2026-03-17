import json
from typing import Any, cast

from core.persistence.repository import SimulationRepository

class ReviewDataAdapter:
    """
    [V4.0 入口层] 战果复盘统一数据适配器。
    作为 Facade 模式，负责从 Repository 拉取原始数据流。
    [解耦说明] 自 V6.6 起，本类不再负责逻辑加工，仅作为 Data Fetcher 使用。
    """

    def __init__(self, db_path: str = "simulation_audit.db", session_id: int | None = None):
        self.repo = SimulationRepository(db_path, session_id)
        self._name_map: dict[int, str] = {} # 缓存

    async def _ensure_name_map(self, sid: int):
        if not self._name_map:
            entities = await self.repo.fetch_entity_registry(sid)
            self._name_map = {e['id']: e['name'] for e in entities}

    async def get_all_sessions(self) -> list[dict[str, Any]]:
        try:
            return await self.repo.fetch_all_sessions()
        except Exception as e:
            # 捕获如 "no such table" 等数据库异常，返回空列表
            from core.logger import get_ui_logger
            get_ui_logger().log_warning(f"ReviewDataAdapter: Failed to fetch sessions: {e}")
            return []

    async def get_summary_stats(self) -> dict[str, Any]:
        sid = await self.repo.get_latest_session_id()
        if not sid:
            return {"total_damage": 0, "duration_seconds": 0, "avg_dps": 0, "peak_dps": 0}
        
        row = await self.repo.fetch_session_summary(sid)
        if row:
            # 显式转换确保 Pylance 识别索引访问
            r = cast(tuple[Any, ...], row)
            return {
                "total_damage": r[0] or 0,
                "duration_seconds": (r[1] or 0) / 60.0,
                "avg_dps": r[2] or 0,
                "peak_dps": r[3] or 0,
                "total_frames": r[1] or 0
            }
        return {"total_damage": 0, "duration_seconds": 0, "avg_dps": 0, "peak_dps": 0}

    async def get_dps_data(self) -> list[dict[str, Any]]:
        """获取原始伤害点记录 (用于 UI 点击下钻)"""
        sid = await self.repo.get_latest_session_id()
        if not sid:
            return []
        await self._ensure_name_map(sid)
        raw = await self.repo.fetch_raw_damage_events(sid)
        return [{
            "frame": r['frame'],
            "value": r['dmg'],
            "source": self._name_map.get(r['source_id'], f"ID:{r['source_id']}"),
            "element": r['element'],
            "event_id": r['event_id'],
            "action": r['action'] or "伤害触发",
            "name": r['name']
        } for r in raw]

    async def get_damage_events_raw(self) -> list[dict[str, Any]]:
        """[V4.1] 获取原始伤害事件数据（纯 DB 数据，无名称映射）

        用于需要原始数据的场景，如堆叠 DPS 图表
        """
        sid = await self.repo.get_latest_session_id()
        if not sid:
            return []
        return await self.repo.fetch_raw_damage_events(sid)

    async def get_damage_events_ui(self) -> list[dict[str, Any]]:
        """[V4.1] 获取 UI 展示用伤害事件数据（含名称映射）

        用于 UI 展示场景，如伤害分布图表
        """
        return await self.get_dps_data()

    async def get_stacked_dps_data_raw(self) -> list[dict[str, Any]]:
        """获取用于堆叠 DPS 加工的原始事件

        [V4.1] 内部调用 get_damage_events_raw()
        """
        return await self.get_damage_events_raw()

    async def get_action_tracks_raw(self) -> list[dict[str, Any]]:
        sid = await self.repo.get_latest_session_id()
        if not sid:
            return []
        return await self.repo.fetch_character_pulses(sid)

    async def get_aura_pulses(self) -> list[dict[str, Any]]:
        sid = await self.repo.get_latest_session_id()
        if not sid:
            return []
        raw = await self.repo.fetch_aura_pulses(sid)
        return [{"frame": r['f'], "aura": json.loads(r['aura'])} for r in raw]

    async def get_all_characters_base_stats(self) -> dict[int, dict[str, Any]]:
        """[V8.3] 批量获取所有角色的初始面板快照（包含名称映射）

        [V4.1] 重构：调用 Repository 方法，消除直连 SQL
        """
        sid = await self.repo.get_latest_session_id()
        if not sid:
            return {}

        rows = await self.repo.fetch_all_characters_base_stats(sid)
        results = {}
        for row in rows:
            eid = row["entity_id"]
            name = row["name"]
            stats = json.loads(row["base_attributes"])
            stats["名称"] = name
            results[eid] = stats
        return results

    async def get_reaction_logs_raw(self) -> list[str]:
        sid = await self.repo.get_latest_session_id()
        if not sid:
            return []
        return await self.repo.fetch_reaction_logs(sid)

    async def get_mechanism_metrics_raw(self) -> list[dict[str, Any]]:
        sid = await self.repo.get_latest_session_id()
        if not sid:
            return []
        return await self.repo.fetch_mechanism_metrics(sid)

    async def get_energy_data_raw(self) -> list[dict[str, Any]]:
        sid = await self.repo.get_latest_session_id()
        if not sid:
            return []
        return await self.repo.fetch_energy_jumps(sid)

    async def get_damage_audit(self, event_id: int) -> list[dict[str, Any]]:
        raw = await self.repo.fetch_damage_audit_trail(event_id)
        return [{"modifier_id": r['mid'], "source": r['src'], "stat": r['stat'], "value": r['val'], "op": r['op']} for r in raw]

    async def get_event_metadata(self, event_id: int) -> dict | None:
        """[V2.5.5] 获取事件元数据（用于审计详情加载）

        Args:
            event_id: 事件 ID

        Returns:
            事件元数据字典
        """
        return await self.repo.fetch_event_with_damage(event_id)

    async def get_entity_modifiers_for_stat(
        self,
        event_id: int,
        stat_names: list[str]
    ) -> list[dict[str, Any]]:
        """获取指定事件相关实体的修饰符分项来源

        Args:
            event_id: 事件ID
            stat_names: 要筛选的属性名列表（如 ["伤害加成", "暴击伤害"]）

        Returns:
            修饰符分项列表 [{"source": str, "stat": str, "value": float, "op": str}, ...]
        """
        # 1. 获取事件元数据（包含 session_id, source_id, frame_id）
        meta = await self.get_event_metadata(event_id)
        if not meta:
            return []

        session_id = meta.get("session_id")
        entity_id = meta.get("source_id")
        frame = meta.get("frame_id")

        if session_id is None or entity_id is None or frame is None:
            return []

        # 2. 查询修饰符
        return await self.repo.fetch_entity_modifiers(
            int(session_id), int(entity_id), int(frame), stat_names
        )

    async def get_entity_snapshot(self, frame_id: int, entity_id: int) -> dict | None:
        """[V2.5.5] 获取实体在该帧的属性快照 [R] 项

        用于审计系统的脱水存储机制，从帧快照检索基础属性、面板百分比等数据。

        [V4.1] 重构：调用 Repository 方法，消除直连 SQL

        Args:
            frame_id: 帧编号
            entity_id: 实体 ID

        Returns:
            实体属性快照字典，包含：
            - stats: 属性字典
            - current_hp: 当前 HP
            - current_energy: 当前能量
            - active_modifiers: 活跃修饰符列表
            - metrics: 机制指标字典
        """
        sid = await self.repo.get_latest_session_id()
        if not sid:
            return None

        snapshot: dict[str, Any] = {
            "entity_id": entity_id,
            "frame": frame_id,
            "stats": {},
            "active_modifiers": [],
            "metrics": {}
        }

        # 1. 加载基础面板 (仅角色)
        base_attr = await self.repo.fetch_entity_base_attributes(sid, entity_id)
        if base_attr and base_attr.get("base_attributes"):
            snapshot["stats"] = json.loads(base_attr["base_attributes"])

        # 2. 资源跳变还原 (HP, ENERGY)
        state_jumps = await self.repo.fetch_entity_state_jumps(sid, entity_id, frame_id)
        for jump in state_jumps:
            jtype, jval = jump["jump_type"], jump["new_value"]
            snapshot["stats"][jtype] = round(jval, 1)
            if jtype == "HP":
                snapshot["current_hp"] = jval
            if jtype == "ENERGY":
                snapshot["current_energy"] = jval

        # 3. 属性修饰符还原
        modifiers = await self.repo.fetch_active_modifiers(sid, entity_id, frame_id)
        for m in modifiers:
            snapshot["active_modifiers"].append({
                "name": m["source_name"], "stat": m["stat_type"], "value": m["value"], "op": m["op_type"]
            })

        # 4. 机制指标
        snapshot["metrics"] = await self.repo.fetch_entity_mechanism_metrics(sid, entity_id, frame_id)

        return snapshot if snapshot["stats"] else None

    async def get_target_snapshot(self, frame_id: int, target_id: int) -> dict | None:
        """[V2.5.5] 获取目标在该帧的状态快照 [R] 项

        用于审计系统获取目标的抗性、防御等属性。

        [V4.1] 重构：调用 Repository 方法，消除直连 SQL
        [V14.0] 新增：获取目标修饰符（减防、减抗等）

        Args:
            frame_id: 帧编号
            target_id: 目标 ID

        Returns:
            目标状态快照字典，包含：
            - target_id: 目标 ID
            - frame: 帧编号
            - aura: 元素附着状态
            - resistance: 抗性字典
            - active_modifiers: 活跃修饰符列表
        """
        sid = await self.repo.get_latest_session_id()
        if not sid:
            return None

        snapshot: dict[str, Any] = {
            "target_id": target_id,
            "frame": frame_id,
            "aura": {},
            "resistance": {},
            "active_modifiers": []
        }

        # 1. 获取元素附着状态
        aura_data = await self.repo.fetch_target_aura_state(sid, frame_id)
        if aura_data and aura_data.get("aura_state"):
            snapshot["aura"] = json.loads(aura_data["aura_state"])

        # 2. 获取目标基础属性（如果有存储）
        registry_info = await self.repo.fetch_entity_registry_info(sid, target_id)
        if registry_info:
            snapshot["name"] = registry_info["name"]
            snapshot["type"] = registry_info["entity_type"]

        # 3. [V14.0] 获取目标修饰符（减防、减抗等）
        # 需要获取的属性类型列表
        target_modifier_stats = [
            "防御力%", "固定防御力", "防御力",
            "火元素抗性", "水元素抗性", "冰元素抗性", "雷元素抗性",
            "风元素抗性", "岩元素抗性", "草元素抗性", "物理元素抗性"
        ]
        modifiers = await self.repo.fetch_entity_modifiers(
            sid, target_id, frame_id, target_modifier_stats
        )
        if modifiers:
            # 转换格式以适配审计处理器
            snapshot["active_modifiers"] = [
                {
                    "name": m.get("source", "未知来源"),
                    "stat": m.get("stat", ""),
                    "value": m.get("value", 0.0),
                    "op": m.get("op", "ADD")
                }
                for m in modifiers
            ]

        return snapshot

    async def get_frame(self, frame_id: int) -> dict | None:
        """重建第 T 帧的全量快照 (包含 HP/能量/效果/护盾的离散还原)

        [V4.1] 重构：调用 Repository 方法，消除直连 SQL
        """
        sid = await self.repo.get_latest_session_id()
        if not sid:
            return None
        await self._ensure_name_map(sid)

        snapshot: dict[str, Any] = {
            "frame": frame_id,
            "team": [],
            "entities": [],
            "events": []
        }

        active_entities = await self.repo.fetch_entity_registry(sid)

        for ent in active_entities:
            eid, name, etype = ent['id'], ent['name'], ent['type']
            entity_snapshot: dict[str, Any] = {
                "entity_id": eid,
                "name": name,
                "stats": {},
                "active_modifiers": [],
                "active_effects": [],  # [V9.2] 活跃效果列表
                "shields": [],         # [V9.2] 活跃护盾列表
                "metrics": {}          # [V9.6] 机制指标字典
            }

            # 1. 加载基础面板 (仅角色)
            if etype == "CHARACTER":
                base_attr = await self.repo.fetch_entity_base_attributes(sid, eid)
                if base_attr and base_attr.get("base_attributes"):
                    entity_snapshot["stats"] = json.loads(base_attr["base_attributes"])

            # 2. 资源跳变还原 (HP, ENERGY)
            state_jumps = await self.repo.fetch_entity_state_jumps(sid, eid, frame_id)
            for jump in state_jumps:
                jtype, jval = jump["jump_type"], jump["new_value"]
                entity_snapshot["stats"][jtype] = round(jval, 1)
                if jtype == "HP":
                    entity_snapshot["current_hp"] = jval
                if jtype == "ENERGY":
                    entity_snapshot["current_energy"] = jval

            # 3. 属性修饰符还原 (Lifecycles)
            modifiers = await self.repo.fetch_active_modifiers(sid, eid, frame_id)
            for m in modifiers:
                entity_snapshot["active_modifiers"].append({
                    "name": m["source_name"], "stat": m["stat_type"],
                    "value": m["value"], "op": m["op_type"]
                })

            # 4. 效果与护盾还原 (Effect Lifecycles)
            effects = await self.repo.fetch_active_effects(sid, eid, frame_id)
            for eff in effects:
                eff_data = {
                    "instance_id": eff["instance_id"],
                    "name": eff["name"],
                    "start_frame": eff["start_frame"],
                    "end_frame": eff["end_frame"],
                    "duration": eff["duration"]
                }

                if eff["effect_type"] == "SHIELD":
                    # 查询护盾剩余量
                    shield_hp = await self.repo.fetch_shield_state(sid, eff["instance_id"], frame_id)
                    eff_data["current_hp"] = shield_hp
                    entity_snapshot["shields"].append(eff_data)
                else:
                    entity_snapshot["active_effects"].append(eff_data)

            # 5. 机制指标
            entity_snapshot["metrics"] = await self.repo.fetch_entity_mechanism_metrics(sid, eid, frame_id)

            if etype == "CHARACTER":
                snapshot["team"].append(entity_snapshot)
            else:
                snapshot["entities"].append(entity_snapshot)

        # 6. 事件日志同步
        event_logs = await self.repo.fetch_event_log_by_frame(sid, frame_id)
        for ev in event_logs:
            snapshot["events"].append({
                "event_id": ev["event_id"],
                "type": ev["event_type"],
                "source_name": self._name_map.get(ev["source_id"], "Unknown")
            })

        return snapshot

    async def get_full_lifecycles(self) -> list[dict[str, Any]]:
        """[V4.1] 重构：调用 Repository 方法，消除直连 SQL"""
        sid = await self.repo.get_latest_session_id()
        if not sid:
            return []

        results = []

        # 修饰符生命周期
        modifier_cycles = await self.repo.fetch_modifier_lifecycles(sid)
        for m in modifier_cycles:
            results.append({
                'name': f"{m['source_name']} ({m['stat_type']})",
                'start': m['start_frame'],
                'end': m['end_frame'],
                'type': 'MODIFIER'
            })

        # 效果生命周期
        effect_cycles = await self.repo.fetch_effect_lifecycles(sid)
        for e in effect_cycles:
            results.append({
                'name': e['name'],
                'start': e['start_frame'],
                'end': e['end_frame'],
                'type': e['effect_type']
            })

        return results
