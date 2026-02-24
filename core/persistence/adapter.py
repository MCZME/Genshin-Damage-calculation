import aiosqlite
import json
import os
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

    async def _get_latest_session(self, db) -> Optional[int]:
        """获取最近一次仿真的 ID (如果未指定 session_id)"""
        if self.session_id:
            return self.session_id
        try:
            async with db.execute("SELECT id FROM simulation_sessions ORDER BY id DESC LIMIT 1") as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None
        except Exception as e:
            from core.logger import get_ui_logger
            get_ui_logger().log_error(f"Adapter: Latest session lookup failed: {e}")
            return None

    async def _load_name_map(self, db, sid: int):
        """加载当前会话的实体 ID 到名称的映射"""
        if self._name_map or sid is None:
            return
        async with db.execute(
            "SELECT entity_id, name FROM simulation_entity_registry WHERE session_id = ?", (sid,)
        ) as cursor:
            async for row in cursor:
                self._name_map[row[0]] = row[1]

    async def get_summary_stats(self) -> Dict[str, Any]:
        """获取全局统计摘要 (直接查询汇总表)"""
        from core.logger import get_ui_logger
        if not os.path.exists(self.db_path):
            get_ui_logger().log_warning(f"Adapter: Database file not found at {self.db_path}")
            return {"total_damage": 0, "duration_seconds": 0, "avg_dps": 0, "peak_dps": 0}

        async with aiosqlite.connect(self.db_path) as db:
            sid = await self._get_latest_session(db)
            if sid is None:
                get_ui_logger().log_warning("Adapter: No session ID found.")
                return {"total_damage": 0, "duration_seconds": 0, "avg_dps": 0, "peak_dps": 0}
                
            get_ui_logger().log_info(f"Adapter: Querying summary for SID {sid}")
            async with db.execute(
                "SELECT total_damage, duration_frames, avg_dps, peak_dps FROM simulation_sessions WHERE id = ?", (sid,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    get_ui_logger().log_info(f"Adapter: Summary result: DMG={row[0]}, Frames={row[1]}")
                    return {
                        "total_damage": row[0] or 0,
                        "duration_seconds": (row[1] or 0) / 60.0,
                        "avg_dps": row[2] or 0,
                        "peak_dps": row[3] or 0
                    }
                get_ui_logger().log_warning(f"Adapter: Session {sid} not found in database.")
                return {"total_damage": 0, "duration_seconds": 0, "avg_dps": 0, "peak_dps": 0}

    async def get_dps_data(self) -> List[Dict[str, Any]]:
        """从 event_damage_data 聚合伤害序列，用于绘制曲线"""
        from core.logger import get_ui_logger
        if not os.path.exists(self.db_path): return []
        async with aiosqlite.connect(self.db_path) as db:
            sid = await self._get_latest_session(db)
            if sid is None: return []
            await self._load_name_map(db, sid)
            
            # 增强查询：关联 character_pulses 获取当时的动作指令
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
            try:
                async with db.execute(sql, (sid,)) as cursor:
                    results = []
                    async for row in cursor:
                        results.append({
                            "frame": row[0],
                            "value": row[1],
                            "source": self._name_map.get(row[2], f"ID:{row[2]}"),
                            "element": row[3],
                            "event_id": row[4],
                            "action": row[5] or "伤害触发"
                        })
                    get_ui_logger().log_info(f"Adapter: Loaded {len(results)} damage events.")
                    return results
            except Exception as e:
                get_ui_logger().log_error(f"Adapter: DPS data query failed: {e}")
                return []

    async def get_energy_data(self) -> Dict[str, List[Tuple[int, float]]]:
        """提取全队能量跳变轨迹"""
        if not os.path.exists(self.db_path): return {}
        async with aiosqlite.connect(self.db_path) as db:
            sid = await self._get_latest_session(db)
            if sid is None: return {}
            await self._load_name_map(db, sid)
            trajectories: Dict[str, List[Tuple[int, float]]] = {}
            
            async with db.execute(
                "SELECT frame_id, entity_id, new_value FROM simulation_state_jumps "
                "WHERE session_id = ? AND jump_type = 'ENERGY' ORDER BY frame_id", (sid,)
            ) as cursor:
                async for row in cursor:
                    name = self._name_map.get(row[1], f"Entity_{row[1]}")
                    if name not in trajectories:
                        trajectories[name] = []
                    trajectories[name].append((row[0], row[2]))
                return trajectories

    async def get_mechanism_data(self) -> Dict[str, List[Tuple[int, float]]]:
        """提取通用机制指标 (如气氛值) 的演进轨迹"""
        if not os.path.exists(self.db_path): return {}
        async with aiosqlite.connect(self.db_path) as db:
            sid = await self._get_latest_session(db)
            if sid is None: return {}
            await self._load_name_map(db, sid)
            trajectories: Dict[str, List[Tuple[int, float]]] = {}
            
            async with db.execute(
                "SELECT frame_id, entity_id, metric_key, value FROM simulation_mechanism_metrics "
                "WHERE session_id = ? ORDER BY frame_id", (sid,)
            ) as cursor:
                async for row in cursor:
                    e_name = self._name_map.get(row[1], f"ID:{row[1]}")
                    m_key = f"{e_name}-{row[2]}"
                    if m_key not in trajectories:
                        trajectories[m_key] = []
                    trajectories[m_key].append((row[0], row[3]))
                return trajectories

    async def get_reaction_stats(self) -> Dict[str, int]:
        """统计各类元素反应的触发次数 (从 payload 解析具体类型)"""
        if not os.path.exists(self.db_path): return {}
        async with aiosqlite.connect(self.db_path) as db:
            sid = await self._get_latest_session(db)
            if sid is None: return {}
            
            # 从 event_payloads 中解析具体的反应名称
            sql = """
                SELECT p.payload_json 
                FROM event_payloads p
                JOIN simulation_event_log l ON p.event_id = l.event_id
                WHERE l.session_id = ? AND l.event_type = 'AFTER_ELEMENTAL_REACTION'
            """
            stats = {}
            async with db.execute(sql, (sid,)) as cursor:
                async for row in cursor:
                    try:
                        payload = json.loads(row[0])
                        reaction = payload.get("elemental_reaction", {})
                        rtype = reaction.get("reaction_type")
                        if rtype:
                            stats[rtype] = stats.get(rtype, 0) + 1
                    except:
                        continue
            return stats

    async def get_frame(self, frame_id: int) -> Optional[dict]:
        """[核心逻辑] 重建第 T 帧的全量快照"""
        if not os.path.exists(self.db_path): return None
        async with aiosqlite.connect(self.db_path) as db:
            sid = await self._get_latest_session(db)
            if sid is None: return None
            await self._load_name_map(db, sid)
            
            snapshot = {
                "frame": frame_id,
                "team": [],
                "entities": [],
                "events": []
            }

            # 1. 确定当时存活的实体 (基于注册表)
            active_entities = []
            async with db.execute(
                "SELECT entity_id, name, entity_type FROM simulation_entity_registry WHERE session_id = ?", (sid,)
            ) as cursor:
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

                # --- A. 静态基准加载 ---
                if etype == "CHARACTER":
                    async with db.execute("SELECT base_attributes FROM simulation_characters WHERE session_id=? AND entity_id=?", (sid, eid)) as sc:
                        row = await sc.fetchone()
                        if row:
                            entity_snapshot["stats"] = json.loads(row[0])
                elif etype == "TARGET":
                    async with db.execute("SELECT res_phys, res_fire, res_water, res_wind, res_elec, res_grass, res_ice, res_rock FROM simulation_targets WHERE session_id=? AND entity_id=?", (sid, eid)) as sc:
                        row = await sc.fetchone()
                        if row:
                            entity_snapshot["stats"] = {
                                "物理抗性": row[0], "火抗": row[1], "水抗": row[2], "风抗": row[3],
                                "雷抗": row[4], "草抗": row[5], "冰抗": row[6], "岩抗": row[7]
                            }

                # --- B. 物理轨道 (Pulse) ---
                if etype == "CHARACTER":
                    async with db.execute(
                        "SELECT x, y, z, action_id, is_on_field FROM character_pulses "
                        "WHERE session_id = ? AND entity_id = ? AND frame_id <= ? "
                        "ORDER BY frame_id DESC LIMIT 1", (sid, eid, frame_id)
                    ) as sc:
                        row = await sc.fetchone()
                        if row:
                            entity_snapshot.update({
                                "pos": [row[0], row[1], row[2]],
                                "action_id": row[3],
                                "on_field": bool(row[4])
                            })
                            entity_snapshot["stats"].update({
                                "坐标_X": round(row[0], 2), "坐标_Y": round(row[1], 2), "坐标_Z": round(row[2], 2),
                                "在场": "是" if row[4] else "否"
                            })
                
                # --- C. 资源轨道 (Jumps) ---
                async with db.execute(
                    "SELECT jump_type, new_value FROM simulation_state_jumps "
                    "WHERE session_id = ? AND entity_id = ? AND frame_id <= ? "
                    "GROUP BY jump_type", (sid, eid, frame_id)
                ) as sc:
                    async for row in sc:
                        jtype, val = row[0], row[1]
                        entity_snapshot[jtype.lower()] = val
                        entity_snapshot["stats"][jtype] = round(val, 1)

                # --- D. 机制指标轨道 (Mechanism) ---
                async with db.execute(
                    "SELECT metric_key, value FROM simulation_mechanism_metrics "
                    "WHERE session_id = ? AND entity_id = ? AND frame_id <= ? "
                    "GROUP BY metric_key", (sid, eid, frame_id)
                ) as sc:
                    async for row in sc:
                        entity_snapshot["stats"][row[0]] = round(row[1], 1)

                # --- E. 属性增益轨道 (Lifecycles) ---
                async with db.execute(
                    "SELECT modifier_id, source_name, stat_type, value, op_type FROM modifier_lifecycles "
                    "WHERE session_id = ? AND entity_id = ? AND start_frame <= ? "
                    "AND (end_frame IS NULL OR end_frame > ?)", (sid, eid, frame_id, frame_id)
                ) as sc:
                    async for r in sc:
                        entity_snapshot["active_modifiers"].append({
                            "modifier_id": r[0],
                            "name": r[1],
                            "stat": r[2],
                            "value": r[3],
                            "op": r[4]
                        })

                # E. 效果生命周期轨道 (Effects/Shields)
                async with db.execute(
                    "SELECT instance_id, name, effect_type, start_frame, duration FROM simulation_effect_lifecycles "
                    "WHERE session_id = ? AND entity_id = ? AND start_frame <= ? "
                    "AND (end_frame IS NULL OR end_frame > ?)", (sid, eid, frame_id, frame_id)
                ) as sc:
                    async for r in sc:
                        entity_snapshot["active_modifiers"].append({
                            "name": r[1],
                            "value": r[2], # 类型标识
                            "is_effect": True
                        })

                if etype == "CHARACTER":
                    snapshot["team"].append(entity_snapshot)
                else:
                    snapshot["entities"].append(entity_snapshot)

            # 3. 帧内事件记录
            async with db.execute(
                "SELECT event_id, event_type, source_id FROM simulation_event_log "
                "WHERE session_id = ? AND frame_id = ?", (sid, frame_id)
            ) as cursor:
                async for row in cursor:
                    snapshot["events"].append({
                        "event_id": row[0],
                        "type": row[1],
                        "source_name": self._name_map.get(row[2], "Unknown")
                    })

            return snapshot

    async def get_aura_pulses(self) -> List[Dict[str, Any]]:
        """获取目标元素附着脉搏列表"""
        if not os.path.exists(self.db_path): return []
        async with aiosqlite.connect(self.db_path) as db:
            sid = await self._get_latest_session(db)
            if sid is None: return []
            sql = """
                SELECT frame_id, aura_state FROM target_aura_pulses 
                WHERE session_id = ? ORDER BY frame_id
            """
            async with db.execute(sql, (sid,)) as cursor:
                pulses = []
                async for row in cursor:
                    pulses.append({
                        "frame": row[0],
                        "aura": json.loads(row[1])
                    })
                return pulses

    async def get_full_lifecycles(self) -> List[Dict[str, Any]]:
        """获取全场所有生命周期记录，用于绘制甘特图"""
        if not os.path.exists(self.db_path): return []
        async with aiosqlite.connect(self.db_path) as db:
            sid = await self._get_latest_session(db)
            if sid is None: return []
            results = []
            
            # 1. 获取修饰符
            async with db.execute(
                "SELECT source_name, start_frame, end_frame, stat_type FROM modifier_lifecycles WHERE session_id=?", (sid,)
            ) as cur:
                async for r in cur:
                    results.append({'name': f"{r[0]} ({r[3]})", 'start': r[1], 'end': r[2], 'type': 'MODIFIER'})
            
            # 2. 获取效果/护盾
            async with db.execute(
                "SELECT name, start_frame, end_frame, effect_type FROM simulation_effect_lifecycles WHERE session_id=?", (sid,)
            ) as cur:
                async for r in cur:
                    results.append({'name': r[0], 'start': r[1], 'end': r[2], 'type': r[3]})
                    
            return results

    async def get_action_tracks(self) -> Dict[str, List[Dict[str, Any]]]:
        """提取角色动作指令的时间轴轨道 (聚合为片段)"""
        if not os.path.exists(self.db_path): return {}
        async with aiosqlite.connect(self.db_path) as db:
            sid = await self._get_latest_session(db)
            if sid is None: return {}
            await self._load_name_map(db, sid)
            
            tracks: Dict[str, List[Dict[str, Any]]] = {}
            sql = """
                SELECT frame_id, entity_id, action_id 
                FROM character_pulses 
                WHERE session_id = ? 
                ORDER BY entity_id, frame_id
            """
            async with db.execute(sql, (sid,)) as cursor:
                current_entity = None
                current_action = None
                start_frame = 0
                
                async for row in cursor:
                    fid, eid, aid = row
                    name = self._name_map.get(eid, f"Char_{eid}")
                    
                    if eid != current_entity or aid != current_action:
                        # 结束旧片段
                        if current_entity is not None and current_action:
                            if name not in tracks: tracks[name] = []
                            tracks[name].append({
                                "start": start_frame,
                                "end": fid - 1,
                                "action": current_action
                            })
                        # 开始新片段
                        current_entity = eid
                        current_action = aid
                        start_frame = fid
                
                # 最后一个片段处理
                if current_entity is not None and current_action:
                    name = self._name_map.get(current_entity, f"Char_{current_entity}")
                    if name not in tracks: tracks[name] = []
                    tracks[name].append({
                        "start": start_frame,
                        "end": start_frame + 1,
                        "action": current_action
                    })
            return tracks

    async def get_all_pulses(self) -> Dict[str, List[Dict[str, Any]]]:
        """提取全场所有实体的物理轨迹 (用于重演投影)"""
        if not os.path.exists(self.db_path): return {}
        async with aiosqlite.connect(self.db_path) as db:
            sid = await self._get_latest_session(db)
            if sid is None: return {}
            await self._load_name_map(db, sid)
            
            trajectories = {}
            # 1. 角色轨迹
            async with db.execute(
                "SELECT frame_id, entity_id, x, z, is_on_field FROM character_pulses "
                "WHERE session_id = ? ORDER BY frame_id", (sid,)
            ) as cursor:
                async for row in cursor:
                    name = self._name_map.get(row[1], f"Char_{row[1]}")
                    if name not in trajectories: trajectories[name] = []
                    trajectories[name].append({
                        "f": row[0], 
                        "pos": (row[2], row[3]), 
                        "on": bool(row[4])
                    })
            return trajectories

    async def get_damage_audit(self, event_id: int) -> List[Dict[str, Any]]:
        """获取特定事件的完整计算审计明细"""
        if not os.path.exists(self.db_path) or event_id is None: return []
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
