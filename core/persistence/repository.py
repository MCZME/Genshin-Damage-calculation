from __future__ import annotations
import aiosqlite
from typing import Any

class SimulationRepository:
    """
    [V4.0 数据仓库] 纯粹的数据库访问层。
    仅负责执行 SQL 并返回原始行数据，不涉及业务逻辑处理。
    """
    def __init__(self, db_path: str = "simulation_audit.db", session_id: int | None = None):
        self.db_path = db_path
        self.session_id = session_id

    async def get_latest_session_id(self) -> int | None:
        if self.session_id:
            return self.session_id
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT id FROM simulation_sessions ORDER BY id DESC LIMIT 1") as cursor:
                row = await cursor.fetchone()
                return int(row[0]) if row else None

    async def fetch_all_sessions(self) -> list[dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            sql = "SELECT id, created_at, total_damage, duration_frames, avg_dps FROM simulation_sessions ORDER BY id DESC"
            async with db.execute(sql) as cursor:
                rows = await cursor.fetchall()
                return [{"id": r[0], "time": r[1], "damage": r[2], "duration": r[3], "dps": r[4]} for r in rows]

    async def fetch_session_summary(self, sid: int) -> Any:
        """获取会话汇总行。由于 aiosqlite 返回 Row，返回类型设为 Any 以绕过静态检查。"""
        async with aiosqlite.connect(self.db_path) as db:
            sql = "SELECT total_damage, duration_frames, avg_dps, peak_dps FROM simulation_sessions WHERE id = ?"
            async with db.execute(sql, (sid,)) as cursor:
                return await cursor.fetchone()

    async def fetch_entity_registry(self, sid: int) -> list[dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            sql = "SELECT entity_id, name, entity_type FROM simulation_entity_registry WHERE session_id = ?"
            async with db.execute(sql, (sid,)) as cursor:
                rows = await cursor.fetchall()
                return [{"id": r[0], "name": r[1], "type": r[2]} for r in rows]

    async def fetch_raw_damage_events(self, sid: int) -> list[dict[str, Any]]:
        """获取所有原始伤害记录，包含来源 ID"""
        async with aiosqlite.connect(self.db_path) as db:
            sql = """
                SELECT l.frame_id, d.final_damage, l.source_id, d.element_type, l.event_id, p.action_id
                FROM event_damage_data d
                JOIN simulation_event_log l ON d.event_id = l.event_id
                LEFT JOIN character_pulses p ON l.session_id = p.session_id 
                    AND l.frame_id = p.frame_id 
                    AND l.source_id = p.entity_id
                WHERE l.session_id = ? 
                ORDER BY l.frame_id
            """
            async with db.execute(sql, (sid,)) as cursor:
                rows = await cursor.fetchall()
                return [{"frame": r[0], "dmg": r[1], "source_id": r[2], "element": r[3], "event_id": r[4], "action": r[5]} for r in rows]

    async def fetch_character_pulses(self, sid: int) -> list[dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            sql = "SELECT frame_id, entity_id, x, z, is_on_field, action_id FROM character_pulses WHERE session_id = ? ORDER BY frame_id"
            async with db.execute(sql, (sid,)) as cursor:
                rows = await cursor.fetchall()
                return [{"f": r[0], "eid": r[1], "x": r[2], "z": r[3], "on": r[4], "action": r[5]} for r in rows]

    async def fetch_aura_pulses(self, sid: int) -> list[dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            sql = "SELECT frame_id, aura_state FROM target_aura_pulses WHERE session_id = ? ORDER BY frame_id"
            async with db.execute(sql, (sid,)) as cursor:
                rows = await cursor.fetchall()
                return [{"f": r[0], "aura": r[1]} for r in rows]

    async def fetch_reaction_logs(self, sid: int) -> list[str]:
        """获取所有反应事件的原始负载 JSON"""
        async with aiosqlite.connect(self.db_path) as db:
            sql = """
                SELECT p.payload_json 
                FROM event_payloads p
                JOIN simulation_event_log l ON p.event_id = l.event_id
                WHERE l.session_id = ? AND l.event_type = 'AFTER_ELEMENTAL_REACTION'
            """
            async with db.execute(sql, (sid,)) as cursor:
                rows = await cursor.fetchall()
                return [str(r[0]) for r in rows]

    async def fetch_mechanism_metrics(self, sid: int) -> list[dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            sql = "SELECT frame_id, entity_id, metric_key, value FROM simulation_mechanism_metrics WHERE session_id = ? ORDER BY frame_id"
            async with db.execute(sql, (sid,)) as cursor:
                rows = await cursor.fetchall()
                return [{"f": r[0], "eid": r[1], "key": r[2], "val": r[3]} for r in rows]

    async def fetch_energy_jumps(self, sid: int) -> list[dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            sql = "SELECT frame_id, entity_id, new_value FROM simulation_state_jumps WHERE session_id = ? AND jump_type = 'ENERGY' ORDER BY frame_id"
            async with db.execute(sql, (sid,)) as cursor:
                rows = await cursor.fetchall()
                return [{"f": r[0], "eid": r[1], "val": r[2]} for r in rows]

    async def fetch_damage_audit_trail(self, event_id: int) -> list[dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            sql = "SELECT modifier_id, source_name, stat_type, value, op_type FROM event_audit_trail WHERE event_id = ? ORDER BY id"
            async with db.execute(sql, (event_id,)) as cursor:
                rows = await cursor.fetchall()
                return [{"mid": r[0], "src": r[1], "stat": r[2], "val": r[3], "op": r[4]} for r in rows]

    async def fetch_entity_modifiers(
        self,
        session_id: int,
        entity_id: int,
        frame: int,
        stat_filter: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """查询指定实体在指定帧的活跃修饰符

        Args:
            session_id: 会话ID
            entity_id: 实体ID
            frame: 帧编号
            stat_filter: 可选，筛选特定属性类型

        Returns:
            修饰符列表 [{"source": str, "stat": str, "value": float, "op": str}, ...]
        """
        async with aiosqlite.connect(self.db_path) as db:
            sql = """
                SELECT source_name, stat_type, value, op_type
                FROM modifier_lifecycles
                WHERE session_id = ? AND entity_id = ?
                AND start_frame <= ?
                AND (end_frame IS NULL OR end_frame > ?)
            """
            params: list[Any] = [session_id, entity_id, frame, frame]

            if stat_filter:
                placeholders = ",".join("?" * len(stat_filter))
                sql += f" AND stat_type IN ({placeholders})"
                params.extend(stat_filter)

            cursor = await db.execute(sql, params)
            rows = await cursor.fetchall()

            return [
                {"source": r[0], "stat": r[1], "value": r[2], "op": r[3]}
                for r in rows
            ]

    async def fetch_event_with_damage(self, event_id: int) -> dict[str, Any] | None:
        """[V2.5.5] 获取事件元数据（用于审计详情加载）

        Args:
            event_id: 事件 ID

        Returns:
            事件元数据字典，包含：
            - session_id: 会话 ID
            - event_id: 事件 ID
            - frame_id: 帧编号
            - source_id: 来源实体 ID
            - target_id: 目标 ID
            - event_type: 事件类型
            - is_crit: 是否暴击
            - final_damage: 最终伤害
            - element_type: 元素类型
            - reaction_name: 反应名称（用于判断剧变反应）
        """
        async with aiosqlite.connect(self.db_path) as db:
            sql = """
                SELECT l.session_id, l.event_id, l.frame_id, l.source_id, d.target_id, l.event_type,
                       d.is_crit, d.final_damage, d.element_type, d.reaction_name
                FROM simulation_event_log l
                LEFT JOIN event_damage_data d ON l.event_id = d.event_id
                WHERE l.event_id = ?
            """
            async with db.execute(sql, (event_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        "session_id": row[0],
                        "event_id": row[1],
                        "frame_id": row[2],
                        "source_id": row[3],
                        "target_id": row[4],
                        "event_type": row[5],
                        "is_crit": bool(row[6]) if row[6] is not None else False,
                        "final_damage": row[7],
                        "element_type": row[8],
                        "reaction_name": row[9]
                    }
                return None
