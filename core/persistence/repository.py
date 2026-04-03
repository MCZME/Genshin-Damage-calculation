from __future__ import annotations
import aiosqlite
import json
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
        """获取所有原始伤害记录，包含来源 ID 和伤害名称"""
        async with aiosqlite.connect(self.db_path) as db:
            sql = """
                SELECT l.frame_id, d.final_damage, l.source_id, d.element_type, l.event_id, p.action_id, d.name
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
                return [{"frame": r[0], "dmg": r[1], "source_id": r[2], "element": r[3], "event_id": r[4], "action": r[5], "name": r[6]} for r in rows]

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
        stat_filter: list[str] | None = None,
        before_event_id: int | None = None,
    ) -> list[dict[str, Any]]:
        """查询指定实体在指定帧的活跃修饰符

        Args:
            session_id: 会话ID
            entity_id: 实体ID
            frame: 帧编号
            stat_filter: 可选，筛选特定属性类型
            before_event_id: [V17.0] 可选，仅包含 start_event_id < before_event_id 的修饰符
                            此参数用于排除同帧内晚于伤害事件施加的修饰符。

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

            # [V17.0] 子帧精度过滤：排除同帧内晚于目标伤害事件的修饰符
            if before_event_id is not None:
                sql += " AND (start_event_id IS NULL OR start_event_id < ?)"
                params.append(before_event_id)

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

    # ============================================================
    # [V4.1] 快照数据获取方法 (供 Adapter 调用)
    # ============================================================

    async def fetch_all_characters_base_stats(self, sid: int) -> list[dict[str, Any]]:
        """批量获取所有角色的初始面板快照（含名称映射）

        Args:
            sid: 会话 ID

        Returns:
            [{"entity_id": int, "name": str, "base_attributes": str}, ...]
        """
        async with aiosqlite.connect(self.db_path) as db:
            sql = """
                SELECT sc.entity_id, r.name, sc.base_attributes
                FROM simulation_characters sc
                JOIN simulation_entity_registry r ON sc.session_id = r.session_id AND sc.entity_id = r.entity_id
                WHERE sc.session_id = ?
            """
            async with db.execute(sql, (sid,)) as cursor:
                rows = await cursor.fetchall()
                return [{"entity_id": r[0], "name": r[1], "base_attributes": r[2]} for r in rows]

    async def fetch_entity_base_attributes(self, sid: int, entity_id: int) -> dict | None:
        """获取实体基础属性原始数据

        Args:
            sid: 会话 ID
            entity_id: 实体 ID

        Returns:
            {"base_attributes": str} 或 None
        """
        async with aiosqlite.connect(self.db_path) as db:
            sql = "SELECT base_attributes FROM simulation_characters WHERE session_id = ? AND entity_id = ?"
            async with db.execute(sql, (sid, entity_id)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {"base_attributes": row[0]}
                return None

    async def fetch_entity_state_jumps(self, sid: int, entity_id: int, frame_id: int) -> list[dict]:
        """获取实体在指定帧之前的最新状态跳变

        Args:
            sid: 会话 ID
            entity_id: 实体 ID
            frame_id: 帧编号

        Returns:
            [{"jump_type": str, "new_value": float}, ...]
        """
        async with aiosqlite.connect(self.db_path) as db:
            sql = """
                SELECT jump_type, new_value FROM simulation_state_jumps
                WHERE session_id = ? AND entity_id = ? AND frame_id <= ?
                GROUP BY jump_type HAVING frame_id = MAX(frame_id)
            """
            async with db.execute(sql, (sid, entity_id, frame_id)) as cursor:
                rows = await cursor.fetchall()
                return [{"jump_type": r[0], "new_value": r[1]} for r in rows]

    async def fetch_active_modifiers(
        self, sid: int, entity_id: int, frame_id: int,
        before_event_id: int | None = None
    ) -> list[dict]:
        """获取实体在指定帧的活跃修饰符

        Args:
            sid: 会话 ID
            entity_id: 实体 ID
            frame_id: 帧编号
            before_event_id: [V17.0] 可选，仅包含 start_event_id < before_event_id 的修饰符

        Returns:
            [{"source_name": str, "stat_type": str, "value": float, "op_type": str}, ...]
        """
        async with aiosqlite.connect(self.db_path) as db:
            sql = """
                SELECT source_name, stat_type, value, op_type FROM modifier_lifecycles
                WHERE session_id = ? AND entity_id = ? AND start_frame <= ? AND (end_frame IS NULL OR end_frame > ?)
            """
            params: list[Any] = [sid, entity_id, frame_id, frame_id]
            # [V17.0] 子帧精度过滤
            if before_event_id is not None:
                sql += " AND (start_event_id IS NULL OR start_event_id < ?)"
                params.append(before_event_id)
            async with db.execute(sql, params) as cursor:
                rows = await cursor.fetchall()
                return [{"source_name": r[0], "stat_type": r[1], "value": r[2], "op_type": r[3]} for r in rows]

    async def fetch_entity_mechanism_metrics(self, sid: int, entity_id: int, frame_id: int) -> dict[str, float]:
        """获取实体在指定帧的机制指标

        Args:
            sid: 会话 ID
            entity_id: 实体 ID
            frame_id: 帧编号

        Returns:
            {"metric_key": float, ...}
        """
        async with aiosqlite.connect(self.db_path) as db:
            sql = """
                SELECT metric_key, value FROM simulation_mechanism_metrics
                WHERE session_id = ? AND entity_id = ? AND frame_id <= ?
                GROUP BY metric_key HAVING frame_id = MAX(frame_id)
            """
            async with db.execute(sql, (sid, entity_id, frame_id)) as cursor:
                rows = await cursor.fetchall()
                return {r[0]: r[1] for r in rows}

    async def fetch_target_aura_state(self, sid: int, frame_id: int) -> dict | None:
        """获取目标在指定帧的元素附着状态

        Args:
            sid: 会话 ID
            frame_id: 帧编号

        Returns:
            {"aura_state": str} 或 None
        """
        async with aiosqlite.connect(self.db_path) as db:
            sql = """
                SELECT aura_state FROM target_aura_pulses
                WHERE session_id = ? AND frame_id <= ?
                ORDER BY frame_id DESC LIMIT 1
            """
            async with db.execute(sql, (sid, frame_id)) as cursor:
                row = await cursor.fetchone()
                if row and row[0]:
                    return {"aura_state": row[0]}
                return None

    async def fetch_entity_registry_info(self, sid: int, entity_id: int) -> dict | None:
        """获取实体注册信息

        Args:
            sid: 会话 ID
            entity_id: 实体 ID

        Returns:
            {"name": str, "entity_type": str} 或 None
        """
        async with aiosqlite.connect(self.db_path) as db:
            sql = "SELECT name, entity_type FROM simulation_entity_registry WHERE session_id = ? AND entity_id = ?"
            async with db.execute(sql, (sid, entity_id)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {"name": row[0], "entity_type": row[1]}
                return None

    async def fetch_target_attributes(self, sid: int, entity_id: int) -> dict | None:
        """[V16.0] 获取战斗目标的基础属性

        从 simulation_targets 表获取目标的等级、防御力和各元素抗性。

        Args:
            sid: 会话 ID
            entity_id: 实体 ID

        Returns:
            目标属性字典，包含：
            - level: 等级
            - defense: 防御力
            - resistance: 抗性字典 {"火": 10.0, "水": 10.0, ...}
            或 None
        """
        async with aiosqlite.connect(self.db_path) as db:
            sql = """
                SELECT level, base_defense, res_phys, res_fire, res_water, res_wind, res_elec, res_grass, res_ice, res_rock
                FROM simulation_targets
                WHERE session_id = ? AND entity_id = ?
            """
            async with db.execute(sql, (sid, entity_id)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        "level": row[0] or 90,
                        "defense": row[1] or 500,
                        "resistance": {
                            "物理": row[2] or 0.0,
                            "火": row[3] or 0.0,
                            "水": row[4] or 0.0,
                            "风": row[5] or 0.0,
                            "雷": row[6] or 0.0,
                            "草": row[7] or 0.0,
                            "冰": row[8] or 0.0,
                            "岩": row[9] or 0.0,
                        }
                    }
                return None

    async def fetch_active_effects(self, sid: int, entity_id: int, frame_id: int) -> list[dict]:
        """获取实体在指定帧的活跃效果

        Args:
            sid: 会话 ID
            entity_id: 实体 ID
            frame_id: 帧编号

        Returns:
            [{"instance_id": int, "effect_type": str, "name": str, "start_frame": int, "end_frame": int | None, "duration": int}, ...]
        """
        async with aiosqlite.connect(self.db_path) as db:
            sql = """
                SELECT instance_id, effect_type, name, start_frame, end_frame, duration
                FROM simulation_effect_lifecycles
                WHERE session_id = ? AND entity_id = ? AND start_frame <= ? AND (end_frame IS NULL OR end_frame > ?)
            """
            async with db.execute(sql, (sid, entity_id, frame_id, frame_id)) as cursor:
                rows = await cursor.fetchall()
                return [
                    {"instance_id": r[0], "effect_type": r[1], "name": r[2], "start_frame": r[3], "end_frame": r[4], "duration": r[5]}
                    for r in rows
                ]

    async def fetch_shield_state(self, sid: int, instance_id: int, frame_id: int) -> float:
        """获取护盾在指定帧的剩余量

        Args:
            sid: 会话 ID
            instance_id: 护盾实例 ID
            frame_id: 帧编号

        Returns:
            护盾剩余量，不存在则返回 0
        """
        async with aiosqlite.connect(self.db_path) as db:
            sql = """
                SELECT current_shield_hp FROM simulation_shield_jumps
                WHERE session_id = ? AND instance_id = ? AND frame_id <= ?
                ORDER BY frame_id DESC LIMIT 1
            """
            async with db.execute(sql, (sid, instance_id, frame_id)) as cursor:
                row = await cursor.fetchone()
                return float(row[0]) if row else 0.0

    async def fetch_modifier_lifecycles(self, sid: int) -> list[dict]:
        """获取完整修饰符生命周期列表

        Args:
            sid: 会话 ID

        Returns:
            [{"source_name": str, "start_frame": int, "end_frame": int | None, "stat_type": str}, ...]
        """
        async with aiosqlite.connect(self.db_path) as db:
            sql = "SELECT source_name, start_frame, end_frame, stat_type FROM modifier_lifecycles WHERE session_id = ?"
            async with db.execute(sql, (sid,)) as cursor:
                rows = await cursor.fetchall()
                return [
                    {"source_name": r[0], "start_frame": r[1], "end_frame": r[2], "stat_type": r[3]}
                    for r in rows
                ]

    async def fetch_effect_lifecycles(self, sid: int) -> list[dict]:
        """获取完整效果生命周期列表

        Args:
            sid: 会话 ID

        Returns:
            [{"name": str, "start_frame": int, "end_frame": int | None, "effect_type": str}, ...]
        """
        async with aiosqlite.connect(self.db_path) as db:
            sql = "SELECT name, start_frame, end_frame, effect_type FROM simulation_effect_lifecycles WHERE session_id = ?"
            async with db.execute(sql, (sid,)) as cursor:
                rows = await cursor.fetchall()
                return [
                    {"name": r[0], "start_frame": r[1], "end_frame": r[2], "effect_type": r[3]}
                    for r in rows
                ]

    async def fetch_event_log_by_frame(self, sid: int, frame_id: int) -> list[dict]:
        """获取指定帧的事件日志

        Args:
            sid: 会话 ID
            frame_id: 帧编号

        Returns:
            [{"event_id": int, "event_type": str, "source_id": int}, ...]
        """
        async with aiosqlite.connect(self.db_path) as db:
            sql = "SELECT event_id, event_type, source_id FROM simulation_event_log WHERE session_id = ? AND frame_id = ?"
            async with db.execute(sql, (sid, frame_id)) as cursor:
                rows = await cursor.fetchall()
                return [{"event_id": r[0], "event_type": r[1], "source_id": r[2]} for r in rows]

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
            - attack_tag: 攻击标签（如 "超载伤害"、"感电伤害"）
            - reaction: 反应数据字典 {"type": "VAPORIZE", "multiplier": 2.0, ...}
            - name: 伤害名称（如 "普通攻击·一段"）
            - contributions: 月反应组分 [{"name": "芙宁娜", "damage": 1234.5, "weight": 45.2}, ...]
        """
        async with aiosqlite.connect(self.db_path) as db:
            sql = """
                SELECT l.session_id, l.event_id, l.frame_id, l.source_id, d.target_id, l.event_type,
                       d.is_crit, d.final_damage, d.element_type, d.attack_tag, d.reaction, d.name, d.contributions
                FROM simulation_event_log l
                LEFT JOIN event_damage_data d ON l.event_id = d.event_id
                WHERE l.event_id = ?
            """
            async with db.execute(sql, (event_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    reaction_data = json.loads(row[10]) if row[10] else None
                    contributions_data = json.loads(row[12]) if row[12] else None
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
                        "attack_tag": row[9],
                        "reaction": reaction_data,
                        "name": row[11],
                        "contributions": contributions_data,
                    }
                return None
