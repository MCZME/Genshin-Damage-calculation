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
        return await self.repo.fetch_all_sessions()

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
            "action": r['action'] or "伤害触发"
        } for r in raw]

    async def get_raw_damage_events(self) -> list[dict[str, Any]]:
        """[V6.6] 获取用于加工的原始伤害事件"""
        sid = await self.repo.get_latest_session_id()
        if not sid:
            return []
        await self._ensure_name_map(sid)
        return await self.get_dps_data()

    async def get_stacked_dps_data_raw(self) -> list[dict[str, Any]]:
        """获取用于堆叠 DPS 加工的原始事件"""
        sid = await self.repo.get_latest_session_id()
        if not sid:
            return []
        return await self.repo.fetch_raw_damage_events(sid)

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
        """[V8.3] 批量获取所有角色的初始面板快照（包含名称映射）"""
        sid = await self.repo.get_latest_session_id()
        if not sid:
            return {}
        
        import aiosqlite
        results = {}
        async with aiosqlite.connect(self.repo.db_path) as db:
            # 使用 JOIN 关联注册表获取实体的真实名称
            sql = """
                SELECT sc.entity_id, r.name, sc.base_attributes 
                FROM simulation_characters sc
                JOIN simulation_entity_registry r ON sc.session_id = r.session_id AND sc.entity_id = r.entity_id
                WHERE sc.session_id = ?
            """
            async with db.execute(sql, (sid,)) as cursor:
                async for row in cursor:
                    eid, name, base_json = row
                    stats = json.loads(base_json)
                    # 显式注入名称字段供 UI 直接读取
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

    async def get_frame(self, frame_id: int) -> dict | None:
        """重建第 T 帧的全量快照 (包含 HP/能量/效果/护盾的离散还原)"""
        sid = await self.repo.get_latest_session_id()
        if not sid:
            return None
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
                entity_snapshot = {
                    "entity_id": eid, 
                    "name": name, 
                    "stats": {}, 
                    "active_modifiers": [],
                    "active_effects": [], # [V9.2] 活跃效果列表
                    "shields": []         # [V9.2] 活跃护盾列表
                }

                # 1. 加载基础面板 (仅角色)
                if etype == "CHARACTER":
                    async with db.execute("SELECT base_attributes FROM simulation_characters WHERE session_id=? AND entity_id=?", (sid, eid)) as sc:
                        row = await sc.fetchone()
                        if row:
                            entity_snapshot["stats"] = json.loads(row[0])
                    
                    # 2. 轨迹同步 (坐标、动作)
                    async with db.execute(
                        "SELECT x, y, z, action_id, is_on_field FROM character_pulses "
                        "WHERE session_id = ? AND entity_id = ? AND frame_id <= ? "
                        "ORDER BY frame_id DESC LIMIT 1", (sid, eid, frame_id)
                    ) as sc:
                        row = await sc.fetchone()
                        if row:
                            entity_snapshot.update({"pos": [row[0], row[1], row[2]], "action_id": row[3], "on_field": bool(row[4])})
                            entity_snapshot["stats"].update({"坐标_X": round(row[0], 2), "坐标_Y": round(row[1], 2), "在场": "是" if row[4] else "否"})

                # 3. 资源跳变还原 (HP, ENERGY)
                # 针对每种跳变类型取最近的一条记录
                async with db.execute(
                    "SELECT jump_type, new_value FROM simulation_state_jumps "
                    "WHERE session_id = ? AND entity_id = ? AND frame_id <= ? "
                    "GROUP BY jump_type HAVING frame_id = MAX(frame_id)", (sid, eid, frame_id)
                ) as sc:
                    async for row in sc: 
                        jtype, jval = row[0], row[1]
                        entity_snapshot["stats"][jtype] = round(jval, 1)
                        # 同时提升到顶层方便 UI 访问
                        if jtype == "HP":
                            entity_snapshot["current_hp"] = jval
                        if jtype == "ENERGY":
                            entity_snapshot["current_energy"] = jval

                # 4. 属性修饰符还原 (Lifecycles)
                async with db.execute(
                    "SELECT source_name, stat_type, value, op_type FROM modifier_lifecycles "
                    "WHERE session_id = ? AND entity_id = ? AND start_frame <= ? AND (end_frame IS NULL OR end_frame > ?)", (sid, eid, frame_id, frame_id)
                ) as sc:
                    async for r in sc:
                        entity_snapshot["active_modifiers"].append({"name": r[0], "stat": r[1], "value": r[2], "op": r[3]})

                # 5. 效果与护盾还原 (Effect Lifecycles)
                async with db.execute(
                    "SELECT instance_id, effect_type, name, start_frame FROM simulation_effect_lifecycles "
                    "WHERE session_id = ? AND entity_id = ? AND start_frame <= ? AND (end_frame IS NULL OR end_frame > ?)", (sid, eid, frame_id, frame_id)
                ) as sc:
                    async for r in sc:
                        inst_id, eff_type, eff_name, start_f = r
                        eff_data = {"instance_id": inst_id, "name": eff_name, "start_frame": start_f}
                        
                        if eff_type == "SHIELD":
                            # 进一步查询护盾剩余量
                            async with db.execute(
                                "SELECT current_shield_hp FROM simulation_shield_jumps "
                                "WHERE session_id = ? AND instance_id = ? AND frame_id <= ? "
                                "ORDER BY frame_id DESC LIMIT 1", (sid, inst_id, frame_id)
                            ) as sj:
                                s_row = await sj.fetchone()
                                eff_data["current_hp"] = s_row[0] if s_row else 0
                            entity_snapshot["shields"].append(eff_data)
                        else:
                            entity_snapshot["active_effects"].append(eff_data)

                if etype == "CHARACTER":
                    snapshot["team"].append(entity_snapshot)
                else:
                    snapshot["entities"].append(entity_snapshot)

            # 6. 事件日志同步
            async with db.execute(
                "SELECT event_id, event_type, source_id FROM simulation_event_log WHERE session_id = ? AND frame_id = ?", (sid, frame_id)
            ) as cursor:
                async for row in cursor:
                    snapshot["events"].append({"event_id": row[0], "type": row[1], "source_name": self._name_map.get(row[2], "Unknown")})

            return snapshot

    async def get_full_lifecycles(self) -> list[dict[str, Any]]:
        sid = await self.repo.get_latest_session_id()
        if not sid:
            return []
        import aiosqlite
        async with aiosqlite.connect(self.repo.db_path) as db:
            results = []
            async with db.execute("SELECT source_name, start_frame, end_frame, stat_type FROM modifier_lifecycles WHERE session_id=?", (sid,)) as cur:
                async for r in cur:
                    results.append({'name': f"{r[0]} ({r[3]})", 'start': r[1], 'end': r[2], 'type': 'MODIFIER'})
            async with db.execute("SELECT name, start_frame, end_frame, effect_type FROM simulation_effect_lifecycles WHERE session_id=?", (sid,)) as cur:
                async for r in cur:
                    results.append({'name': r[0], 'start': r[1], 'end': r[2], 'type': r[3]})
            return results
