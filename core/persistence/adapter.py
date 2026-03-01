import json
import os
from typing import Optional, List, Dict, Any, Tuple
from core.persistence.repository import SimulationRepository

class ReviewDataAdapter:
    """
    [V4.0 入口层] 战果复盘统一数据适配器。
    作为 Facade 模式，负责从 Repository 拉取原始数据流。
    [解耦说明] 自 V6.6 起，本类不再负责逻辑加工，仅作为 Data Fetcher 使用。
    """

    def __init__(self, db_path: str = "simulation_audit.db", session_id: Optional[int] = None):
        self.repo = SimulationRepository(db_path, session_id)
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

    async def get_raw_damage_events(self) -> List[Dict[str, Any]]:
        """[V6.6] 获取用于加工的原始伤害事件"""
        sid = await self.repo.get_latest_session_id()
        if not sid: return []
        await self._ensure_name_map(sid)
        return await self.get_dps_data()

    async def get_stacked_dps_data_raw(self) -> List[Dict[str, Any]]:
        """获取用于堆叠 DPS 加工的原始事件"""
        sid = await self.repo.get_latest_session_id()
        if not sid: return []
        return await self.repo.fetch_raw_damage_events(sid)

    async def get_action_tracks_raw(self) -> List[Dict[str, Any]]:
        sid = await self.repo.get_latest_session_id()
        if not sid: return []
        return await self.repo.fetch_character_pulses(sid)

    async def get_aura_pulses(self) -> List[Dict[str, Any]]:
        sid = await self.repo.get_latest_session_id()
        if not sid: return []
        raw = await self.repo.fetch_aura_pulses(sid)
        return [{"frame": r['f'], "aura": json.loads(r['aura'])} for r in raw]

    async def get_reaction_logs_raw(self) -> List[str]:
        sid = await self.repo.get_latest_session_id()
        if not sid: return []
        return await self.repo.fetch_reaction_logs(sid)

    async def get_mechanism_metrics_raw(self) -> List[Dict[str, Any]]:
        sid = await self.repo.get_latest_session_id()
        if not sid: return []
        return await self.repo.fetch_mechanism_metrics(sid)

    async def get_energy_data_raw(self) -> List[Dict[str, Any]]:
        sid = await self.repo.get_latest_session_id()
        if not sid: return []
        return await self.repo.fetch_energy_jumps(sid)

    async def get_damage_audit(self, event_id: int) -> List[Dict[str, Any]]:
        raw = await self.repo.fetch_damage_audit_trail(event_id)
        return [{"modifier_id": r['mid'], "source": r['src'], "stat": r['stat'], "value": r['val'], "op": r['op']} for r in raw]

    async def get_frame(self, frame_id: int) -> Optional[dict]:
        """重建第 T 帧的全量快照 (Facade 转发)"""
        sid = await self.repo.get_latest_session_id()
        if not sid: return None
        await self._ensure_name_map(sid)
        
        import aiosqlite 
        async with aiosqlite.connect(self.repo.db_path) as db:
            snapshot = {
                "frame": frame_id,
                "team": [],
                "entities": [],
                "events": []
            }

            active_entities = await self.repo.fetch_entity_registry(sid)

            for ent in active_entities:
                eid, name, etype = ent['id'], ent['name'], ent['type']
                entity_snapshot = {"entity_id": eid, "name": name, "stats": {}, "active_modifiers": []}

                if etype == "CHARACTER":
                    async with db.execute("SELECT base_attributes FROM simulation_characters WHERE session_id=? AND entity_id=?", (sid, eid)) as sc:
                        row = await sc.fetchone()
                        if row: entity_snapshot["stats"] = json.loads(row[0])
                    
                    async with db.execute(
                        "SELECT x, y, z, action_id, is_on_field FROM character_pulses "
                        "WHERE session_id = ? AND entity_id = ? AND frame_id <= ? "
                        "ORDER BY frame_id DESC LIMIT 1", (sid, eid, frame_id)
                    ) as sc:
                        row = await sc.fetchone()
                        if row:
                            entity_snapshot.update({"pos": [row[0], row[1], row[2]], "action_id": row[3], "on_field": bool(row[4])})
                            entity_snapshot["stats"].update({"坐标_X": round(row[0], 2), "坐标_Y": round(row[1], 2), "在场": "是" if row[4] else "否"})

                async with db.execute(
                    "SELECT jump_type, new_value FROM simulation_state_jumps "
                    "WHERE session_id = ? AND entity_id = ? AND frame_id <= ? GROUP BY jump_type", (sid, eid, frame_id)
                ) as sc:
                    async for row in sc: entity_snapshot["stats"][row[0]] = round(row[1], 1)

                async with db.execute(
                    "SELECT source_name, stat_type, value, op_type FROM modifier_lifecycles "
                    "WHERE session_id = ? AND entity_id = ? AND start_frame <= ? AND (end_frame IS NULL OR end_frame > ?)", (sid, eid, frame_id, frame_id)
                ) as sc:
                    async for r in sc: entity_snapshot["active_modifiers"].append({"name": r[0], "stat": r[1], "value": r[2], "op": r[3]})

                if etype == "CHARACTER": snapshot["team"].append(entity_snapshot)
                else: snapshot["entities"].append(entity_snapshot)

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
