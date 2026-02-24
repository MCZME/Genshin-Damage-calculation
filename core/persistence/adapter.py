import json
import os
from typing import Optional, List, Dict, Any, Tuple
from core.persistence.repository import SimulationRepository
from core.persistence.processor import AnalysisDataProcessor

class ReviewDataAdapter:
    """
    [V4.0 入口层] 战果复盘统一数据适配器。
    作为 Facade 模式，协调 Repository 拉取数据并调用 Processor 进行加工。
    """

    def __init__(self, db_path: str = "simulation_audit.db", session_id: Optional[int] = None):
        self.repo = SimulationRepository(db_path, session_id)
        self.processor = AnalysisDataProcessor()
        self._name_map: Dict[int, str] = {} # 缓存

    async def _ensure_name_map(self, sid: int):
        if not self._name_map:
            entities = await self.repo.fetch_entity_registry(sid)
            self._name_map = {e['id']: e['name'] for e in entities}

    async def get_all_sessions(self) -> List[Dict[str, Any]]:
        return await self.repo.fetch_all_sessions()

    async def get_summary_stats(self) -> Dict[str, Any]:
        sid = await self.repo.get_latest_session_id()
        if not sid: return {"total_damage": 0, "duration_seconds": 0, "avg_dps": 0, "peak_dps": 0}
        
        row = await self.repo.fetch_session_summary(sid)
        if row:
            return {
                "total_damage": row[0] or 0,
                "duration_seconds": (row[1] or 0) / 60.0,
                "avg_dps": row[2] or 0,
                "peak_dps": row[3] or 0,
                "total_frames": row[1] or 0
            }
        return {"total_damage": 0, "duration_seconds": 0, "avg_dps": 0, "peak_dps": 0}

    async def get_dps_data(self) -> List[Dict[str, Any]]:
        """获取原始伤害点记录 (用于 UI 点击下钻)"""
        sid = await self.repo.get_latest_session_id()
        if not sid: return []
        await self._ensure_name_map(sid)
        raw = await self.repo.fetch_raw_damage_events(sid)
        return [{
            "frame": r['frame'],
            "value": r['dmg'],
            "source": self._name_map.get(r['source_id'], f"ID:{r['source_id']}"),
            "element": r['element'],
            "event_id": r['event_id'],
            "action": r['action'] or "伤害触发"
        } for r in raw]

    async def get_stacked_dps_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """[V4.0 新接口] 获取分角色平滑堆叠 DPS 数据"""
        sid = await self.repo.get_latest_session_id()
        if not sid: return {}
        
        await self._ensure_name_map(sid)
        summary = await self.get_summary_stats()
        total_frames = summary.get("total_frames", 0)
        
        raw_events = await self.repo.fetch_raw_damage_events(sid)
        return self.processor.process_dps_series(raw_events, self._name_map, total_frames)

    async def get_action_tracks(self) -> Dict[str, List[Dict[str, Any]]]:
        sid = await self.repo.get_latest_session_id()
        if not sid: return {}
        await self._ensure_name_map(sid)
        raw_pulses = await self.repo.fetch_character_pulses(sid)
        return self.processor.process_action_segments(raw_pulses, self._name_map)

    async def get_all_pulses(self) -> Dict[str, List[Dict[str, Any]]]:
        sid = await self.repo.get_latest_session_id()
        if not sid: return {}
        await self._ensure_name_map(sid)
        raw_pulses = await self.repo.fetch_character_pulses(sid)
        return self.processor.process_trajectories(raw_pulses, self._name_map)

    async def get_aura_pulses(self) -> List[Dict[str, Any]]:
        sid = await self.repo.get_latest_session_id()
        if not sid: return []
        raw = await self.repo.fetch_aura_pulses(sid)
        return [{"frame": r['f'], "aura": json.loads(r['aura'])} for r in raw]

    async def get_reaction_stats(self) -> Dict[str, int]:
        sid = await self.repo.get_latest_session_id()
        if not sid: return {}
        raw_payloads = await self.repo.fetch_reaction_logs(sid)
        return self.processor.process_reaction_stats(raw_payloads)

    async def get_mechanism_data(self) -> Dict[str, List[Tuple[int, float]]]:
        sid = await self.repo.get_latest_session_id()
        if not sid: return {}
        await self._ensure_name_map(sid)
        raw_metrics = await self.repo.fetch_mechanism_metrics(sid)
        return self.processor.process_mechanism_trajectories(raw_metrics, self._name_map)

    async def get_energy_data(self) -> Dict[str, List[Tuple[int, float]]]:
        sid = await self.repo.get_latest_session_id()
        if not sid: return {}
        await self._ensure_name_map(sid)
        raw = await self.repo.fetch_energy_jumps(sid)
        trajectories = {}
        for r in raw:
            name = self._name_map.get(r['eid'], f"Entity_{r['eid']}")
            if name not in trajectories: trajectories[name] = []
            trajectories[name].append((r['f'], r['val']))
        return trajectories

    async def get_damage_audit(self, event_id: int) -> List[Dict[str, Any]]:
        raw = await self.repo.fetch_damage_audit_trail(event_id)
        return [{"modifier_id": r['mid'], "source": r['src'], "stat": r['stat'], "value": r['val'], "op": r['op']} for r in raw]

    async def get_frame(self, frame_id: int) -> Optional[dict]:
        """重建第 T 帧的全量快照 (Facade 转发)"""
        sid = await self.repo.get_latest_session_id()
        if not sid: return None
        await self._ensure_name_map(sid)
        
        import aiosqlite # 局部导入保持兼容
        async with aiosqlite.connect(self.repo.db_path) as db:
            snapshot = {
                "frame": frame_id,
                "team": [],
                "entities": [],
                "events": []
            }

            # 1. 确定当时存活的实体
            active_entities = await self.repo.fetch_entity_registry(sid)

            # 2. 轨道合成
            for ent in active_entities:
                eid, name, etype = ent['id'], ent['name'], ent['type']
                entity_snapshot = {"entity_id": eid, "name": name, "stats": {}, "active_modifiers": []}

                # --- A. 属性与状态 ---
                if etype == "CHARACTER":
                    async with db.execute("SELECT base_attributes FROM simulation_characters WHERE session_id=? AND entity_id=?", (sid, eid)) as sc:
                        row = await sc.fetchone()
                        if row: entity_snapshot["stats"] = json.loads(row[0])
                    
                    # 物理脉搏
                    async with db.execute(
                        "SELECT x, y, z, action_id, is_on_field FROM character_pulses "
                        "WHERE session_id = ? AND entity_id = ? AND frame_id <= ? "
                        "ORDER BY frame_id DESC LIMIT 1", (sid, eid, frame_id)
                    ) as sc:
                        row = await sc.fetchone()
                        if row:
                            entity_snapshot.update({"pos": [row[0], row[1], row[2]], "action_id": row[3], "on_field": bool(row[4])})
                            entity_snapshot["stats"].update({"坐标_X": round(row[0], 2), "坐标_Y": round(row[1], 2), "在场": "是" if row[4] else "否"})

                # --- B. 资源与机制 ---
                async with db.execute(
                    "SELECT jump_type, new_value FROM simulation_state_jumps "
                    "WHERE session_id = ? AND entity_id = ? AND frame_id <= ? GROUP BY jump_type", (sid, eid, frame_id)
                ) as sc:
                    async for row in sc: entity_snapshot["stats"][row[0]] = round(row[1], 1)

                # --- C. 生命周期 (增益/效果) ---
                async with db.execute(
                    "SELECT source_name, stat_type, value, op_type FROM modifier_lifecycles "
                    "WHERE session_id = ? AND entity_id = ? AND start_frame <= ? AND (end_frame IS NULL OR end_frame > ?)", (sid, eid, frame_id, frame_id)
                ) as sc:
                    async for r in sc: entity_snapshot["active_modifiers"].append({"name": r[0], "stat": r[1], "value": r[2], "op": r[3]})

                if etype == "CHARACTER": snapshot["team"].append(entity_snapshot)
                else: snapshot["entities"].append(entity_snapshot)

            # 3. 帧内事件记录
            async with db.execute(
                "SELECT event_id, event_type, source_id FROM simulation_event_log WHERE session_id = ? AND frame_id = ?", (sid, frame_id)
            ) as cursor:
                async for row in cursor:
                    snapshot["events"].append({"event_id": row[0], "type": row[1], "source_name": self._name_map.get(row[2], "Unknown")})

            return snapshot

    async def get_full_lifecycles(self) -> List[Dict[str, Any]]:
        sid = await self.repo.get_latest_session_id()
        if not sid: return []
        import aiosqlite
        async with aiosqlite.connect(self.repo.db_path) as db:
            results = []
            async with db.execute("SELECT source_name, start_frame, end_frame, stat_type FROM modifier_lifecycles WHERE session_id=?", (sid,)) as cur:
                async for r in cur: results.append({'name': f"{r[0]} ({r[3]})", 'start': r[1], 'end': r[2], 'type': 'MODIFIER'})
            async with db.execute("SELECT name, start_frame, end_frame, effect_type FROM simulation_effect_lifecycles WHERE session_id=?", (sid,)) as cur:
                async for r in cur: results.append({'name': r[0], 'start': r[1], 'end': r[2], 'type': r[3]})
            return results
