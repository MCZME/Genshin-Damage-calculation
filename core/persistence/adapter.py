import aiosqlite
import json
from typing import Optional, List, Dict, Any, Tuple

class ReviewDataAdapter:
    """
    [V3.0 投影还原引擎] 战果复盘专用数据适配器。
    负责将离散的多轨数据库记录重新聚合为 UI 可用的快照模型。
    """

    def __init__(self, db_path: str = "simulation_audit.db", session_id: Optional[int] = None):
        self.db_path = db_path
        self.session_id = session_id
        self._name_map: Dict[int, str] = {} # 实体 ID 到名字的缓存

    async def _get_latest_session(self, db) -> int:
        """获取最近一次仿真的 ID (如果未指定 session_id)"""
        if self.session_id:
            return self.session_id
        async with db.execute("SELECT id FROM simulation_sessions ORDER BY created_at DESC LIMIT 1") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 1

    async def get_summary_stats(self) -> Dict[str, Any]:
        """获取全局统计摘要 (直接查询汇总表)"""
        async with aiosqlite.connect(self.db_path) as db:
            sid = await self._get_latest_session(db)
            async with db.execute(
                "SELECT total_damage, duration_frames, avg_dps, peak_dps FROM simulation_sessions WHERE id = ?", (sid,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        "total_damage": row[0],
                        "duration_seconds": row[1] / 60.0,
                        "avg_dps": row[2],
                        "peak_dps": row[3]
                    }
                return {"total_damage": 0, "duration_seconds": 0, "avg_dps": 0, "peak_dps": 0}

    async def get_dps_data(self) -> List[Dict[str, Any]]:
        """从 event_damage_data 聚合伤害序列，用于绘制曲线"""
        async with aiosqlite.connect(self.db_path) as db:
            sid = await self._get_latest_session(db)
            # 联表查询：关联 log 表获取 frame_id 和 source_id
            sql = """
                SELECT l.frame_id, d.final_damage, l.source_id, d.element_type 
                FROM event_damage_data d
                JOIN simulation_event_log l ON d.event_id = l.event_id
                WHERE l.session_id = ? 
                ORDER BY l.frame_id
            """
            async with db.execute(sql, (sid,)) as cursor:
                results = []
                async for row in cursor:
                    results.append({
                        "frame": row[0],
                        "value": row[1],
                        "source_id": row[2],
                        "element": row[3]
                    })
                return results

    async def get_energy_data(self) -> Dict[int, List[Tuple[int, float]]]:
        """提取全队能量跳变轨迹"""
        async with aiosqlite.connect(self.db_path) as db:
            sid = await self._get_latest_session(db)
            trajectories: Dict[int, List[Tuple[int, float]]] = {}
            
            async with db.execute(
                "SELECT frame_id, entity_id, new_value FROM simulation_state_jumps "
                "WHERE session_id = ? AND jump_type = 'ENERGY' ORDER BY frame_id", (sid,)
            ) as cursor:
                async for row in cursor:
                    eid = row[1]
                    if eid not in trajectories:
                        trajectories[eid] = []
                    trajectories[eid].append((row[0], row[2]))
                return trajectories

    async def get_frame(self, frame_id: int) -> Optional[dict]:
        """
        [核心逻辑] 重建第 T 帧的全量快照。
        采用“追溯+应用”模式从各轨道合成数据。
        """
        async with aiosqlite.connect(self.db_path) as db:
            sid = await self._get_latest_session(db)
            
            snapshot = {
                "frame": frame_id,
                "team": [],
                "entities": [],
                "events": []
            }

            # 1. 确定活跃实体 (基于生命周期登记)
            active_entities = []
            async with db.execute(
                "SELECT entity_id, name, entity_type FROM simulation_entity_registry WHERE session_id = ?", (sid,)
            ) as cursor:
                # 注意：此处应根据 created_frame/destroyed_frame 进一步过滤 (如果后续增加了对应字段)
                async for row in cursor:
                    active_entities.append({"id": row[0], "name": row[1], "type": row[2]})

            # 2. 轨道合成
            for ent in active_entities:
                eid = ent["id"]
                etype = ent["type"]
                
                entity_snapshot = {
                    "entity_id": eid,
                    "name": ent["name"],
                    "stats": {},
                    "active_modifiers": []
                }

                # A. 物理与动作追溯 (Pulse)
                if etype == "CHARACTER":
                    async with db.execute(
                        "SELECT x, y, z, action_id, is_on_field FROM character_pulses "
                        "WHERE session_id = ? AND entity_id = ? AND frame_id <= ? "
                        "ORDER BY frame_id DESC LIMIT 1", (sid, eid, frame_id)
                    ) as sc:
                        row = await sc.fetchone()
                        if row:
                            entity_snapshot.update({
                                "pos": [row[0], row[2], row[1]],
                                "action_id": row[3],
                                "on_field": bool(row[4])
                            })
                
                # B. 资源追溯 (Jumps)
                async with db.execute(
                    "SELECT jump_type, new_value FROM simulation_state_jumps "
                    "WHERE session_id = ? AND entity_id = ? AND frame_id <= ? "
                    "GROUP BY jump_type HAVING MAX(frame_id)", (sid, eid, frame_id)
                ) as sc:
                    async for row in sc:
                        jtype, val = row[0], row[1]
                        entity_snapshot[jtype.lower()] = val
                        entity_snapshot["stats"][jtype] = val

                # C. 属性增益追溯 (Lifecycles)
                async with db.execute(
                    "SELECT modifier_id, source_name, stat_type, value, op_type FROM modifier_lifecycles "
                    "WHERE session_id = ? AND entity_id = ? AND start_frame <= ? "
                    "AND (end_frame IS NULL OR end_frame > ?)", (sid, eid, frame_id, frame_id)
                ) as sc:
                    async for row in sc:
                        entity_snapshot["active_modifiers"].append({
                            "modifier_id": row[0],
                            "name": row[1],
                            "stat": row[2],
                            "value": row[3],
                            "op": row[4]
                        })

                # 分发到快照列表
                if etype == "CHARACTER":
                    snapshot["team"].append(entity_snapshot)
                else:
                    snapshot["entities"].append(entity_snapshot)

            # 3. 瞬时事件获取
            async with db.execute(
                "SELECT event_id, event_type, source_id FROM simulation_event_log "
                "WHERE session_id = ? AND frame_id = ?", (sid, frame_id)
            ) as cursor:
                async for row in cursor:
                    snapshot["events"].append({
                        "event_id": row[0],
                        "type": row[1],
                        "source_id": row[2]
                    })

            return snapshot

    async def get_damage_audit(self, event_id: int) -> List[Dict[str, Any]]:
        """获取特定事件的完整计算审计明细 (瀑布图还原基础)"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT modifier_id, source_name, stat_type, value, op_type FROM event_audit_trail "
                "WHERE event_id = ? ORDER BY id", (event_id,)
            ) as cursor:
                steps = []
                async for row in cursor:
                    steps.append({
                        "modifier_id": row[0],
                        "source": row[1],
                        "stat": row[2],
                        "value": row[3],
                        "op": row[4]
                    })
                return steps
