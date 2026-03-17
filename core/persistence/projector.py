from __future__ import annotations

import json
from typing import Any
from core.persistence.database import GenshinJSONEncoder


class DataProjector:
    """
    [V3.0 投影层] 核心业务分流器。
    负责将 SimulationContext 产生的全量快照映射为数据库各轨道的原子操作。
    """

    def __init__(self, session_id: int):
        self.session_id = session_id

        # 1. 静态登记缓存
        self.registered_entities: set[int] = set()

        # 2. 连续流增量缓存: {entity_id: (x, y, z, action_id, is_on_field)}
        self.last_pulse_cache: dict[int, tuple[float, float, float, str, int]] = {}

        # 3. 跳变流增量缓存: {(entity_id, jump_type): value}
        self.last_jump_cache: dict[tuple[int, str], float] = {}

        # 3.5 机制指标增量缓存: {(entity_id, metric_key): value}
        self.last_metrics_cache: dict[tuple[int, str], float] = {}

        # 4. 生命周期追踪: {(entity_id, modifier_id): start_frame}
        self.active_modifiers: set[tuple[int, int]] = set()

        # 5. 全局汇总指标 (用于 Session 结算)
        self.total_damage: float = 0.0
        self.max_frame: int = 0
        self.peak_dps: float = 0.0
        self._damage_in_last_window: float = 0.0
        self._last_dps_calc_frame: int = 0

    def project_static_meta(self, snapshot: dict) -> list[tuple[str, tuple]]:
        """处理实体登记元数据。"""
        commands: list[tuple[str, tuple]] = []
        meta_list = snapshot.get("entities_meta", [])

        for meta in meta_list:
            eid = meta["entity_id"]
            if eid in self.registered_entities:
                continue

            etype = meta["entity_type"]
            commands.append((
                "INSERT OR IGNORE INTO simulation_entity_registry (session_id, entity_id, entity_type, name, spawn_x, spawn_y, spawn_z, hitbox_radius, hitbox_height) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (self.session_id, eid, etype, meta["name"], meta["spawn_x"], meta["spawn_y"], meta["spawn_z"], meta["hitbox_radius"], meta["hitbox_height"])
            ))

            if etype == "CHARACTER":
                commands.append((
                    "INSERT OR IGNORE INTO simulation_characters (session_id, entity_id, level, constellation, base_attributes, weapon_data, artifact_sets, skill_levels) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (self.session_id, eid, meta["level"], meta["constellation"],
                     json.dumps(meta["base_attributes"], cls=GenshinJSONEncoder),
                     json.dumps(meta["weapon_data"], cls=GenshinJSONEncoder),
                     json.dumps(meta["artifact_sets"], cls=GenshinJSONEncoder),
                     json.dumps(meta["skill_levels"], cls=GenshinJSONEncoder))
                ))
            elif etype == "TARGET":
                commands.append((
                    "INSERT OR IGNORE INTO simulation_targets (session_id, entity_id, level, base_defense, res_phys, res_fire, res_water, res_wind, res_elec, res_grass, res_ice, res_rock) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (self.session_id, eid, meta["level"], meta["base_defense"], meta["res_phys"], meta["res_fire"], meta["res_water"], meta["res_wind"], meta["res_elec"], meta["res_grass"], meta["res_ice"], meta["res_rock"])
                ))
            elif etype == "CONSTRUCT":
                commands.append((
                    "INSERT OR IGNORE INTO simulation_entities (session_id, entity_id, owner_id, created_frame, duration) VALUES (?, ?, ?, ?, ?)",
                    (self.session_id, eid, meta.get("owner_id"), snapshot.get("frame", 0), meta.get("duration"))
                ))

            self.registered_entities.add(eid)

        return commands

    def project_pulse(self, snapshot: dict) -> list[tuple[str, tuple]]:
        """处理角色位移与动作轨道 (增量存储逻辑) 以及目标附着快照。"""
        commands: list[tuple[str, tuple]] = []
        frame_id = snapshot.get("frame", 0)
        self.max_frame = max(self.max_frame, frame_id)

        for char in snapshot.get("team", []):
            eid = char["entity_id"]
            pos = char.get("pos", [0, 0, 0])
            action_id = char.get("action_id", "IDLE")
            on_field = 1 if char.get("on_field") else 0

            last = self.last_pulse_cache.get(eid)
            changed = True
            if last:
                dist_sq = (pos[0]-last[0])**2 + (pos[1]-last[1])**2 + (pos[2]-last[2])**2
                if dist_sq < 0.0001 and action_id == last[3] and on_field == last[4]:
                    changed = False

            if changed:
                commands.append((
                    "INSERT OR REPLACE INTO character_pulses (session_id, frame_id, entity_id, x, y, z, action_id, is_on_field) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (self.session_id, frame_id, eid, pos[0], pos[1], pos[2], action_id, on_field)
                ))
                self.last_pulse_cache[eid] = (pos[0], pos[1], pos[2], action_id, on_field)

        # 目标元素附着脉搏
        for ent in snapshot.get("entities", []):
            eid = ent.get("entity_id")
            auras = ent.get("auras", {})
            is_empty = (not auras.get("regular") and auras.get("frozen") is None and auras.get("quicken") is None and not auras.get("states"))

            if auras and not is_empty:
                commands.append((
                    "INSERT OR REPLACE INTO target_aura_pulses (session_id, frame_id, entity_id, aura_state) VALUES (?, ?, ?, ?)",
                    (self.session_id, frame_id, eid, json.dumps(auras, cls=GenshinJSONEncoder))
                ))

        return commands

    def project_metrics(self, snapshot: dict) -> list[tuple[str, tuple]]:
        """处理所有实体的通用机制指标 (Mechanism Metrics)。"""
        commands: list[tuple[str, tuple]] = []
        frame_id = snapshot.get("frame", 0)

        all_entities = snapshot.get("team", []) + snapshot.get("entities", [])
        for ent in all_entities:
            eid = ent.get("entity_id")
            metrics = ent.get("metrics", {})
            for m_key, val in metrics.items():
                cache_key = (eid, m_key)
                if self.last_metrics_cache.get(cache_key) != val:
                    commands.append((
                        "INSERT INTO simulation_mechanism_metrics (session_id, frame_id, entity_id, metric_key, value) VALUES (?, ?, ?, ?, ?)",
                        (self.session_id, frame_id, eid, m_key, val)
                    ))
                    self.last_metrics_cache[cache_key] = val
        return commands

    def _serialize_element(self, element: Any) -> str:
        """[V3.2] 元素量保留序列化工具：生成 '元素:量' 格式字符串。"""
        if element is None:
            return "Neutral:0.0"

        target_elem = element
        amount = 0.0

        # 处理元组形式 (Element.HYDRO, 1.0)
        if isinstance(element, tuple):
            if len(element) > 0:
                target_elem = element[0]
            if len(element) > 1:
                amount = float(element[1])

        # 获取元素名称 (优先取 .value)
        elem_name = getattr(target_elem, "value", str(target_elem))
        # 如果是 Enum 实例但没取到 value，取 .name
        if not isinstance(elem_name, str) and hasattr(target_elem, "name"):
            elem_name = target_elem.name

        return f"{elem_name}:{amount}"

    def project_events(self, snapshot: dict) -> list[tuple[str, tuple]]:
        """处理离散事件及其相关的 Jump、Lifecycle 和 审计明细。"""
        commands: list[tuple[str, tuple]] = []
        frame_id = snapshot.get("frame", 0)
        self.max_frame = max(self.max_frame, frame_id)
        events = snapshot.get("events", [])

        for evt in events:
            etype = evt.get("type")
            payload = evt.get("payload", {})
            eid = evt.get("source_id")

            if etype in ("AFTER_ENERGY_CHANGE", "AFTER_HEALTH_CHANGE"):
                vtype = "ENERGY" if "ENERGY" in etype else "HP"
                new_val = payload.get("new_energy") if vtype == "ENERGY" else payload.get("new_hp")
                delta = payload.get("delta", 0.0)
                if new_val is not None:
                    cache_key = (eid, vtype)
                    if self.last_jump_cache.get(cache_key) != new_val:
                        commands.append((
                            "INSERT OR REPLACE INTO simulation_state_jumps (session_id, frame_id, entity_id, jump_type, new_value, delta_value) VALUES (?, ?, ?, ?, ?, ?)",
                            (self.session_id, frame_id, eid, vtype, new_val, delta)
                        ))
                        self.last_jump_cache[cache_key] = new_val

            elif etype == "ON_SHIELD_CHANGE":
                shield = payload.get("shield")
                inst_id = getattr(shield, "instance_id", 0)
                if inst_id > 0:
                    commands.append((
                        "INSERT OR REPLACE INTO simulation_shield_jumps (session_id, instance_id, frame_id, current_shield_hp) VALUES (?, ?, ?, ?)",
                        (self.session_id, inst_id, frame_id, payload.get("new_hp", 0.0))
                    ))

            elif etype == "ON_MODIFIER_ADDED":
                mod = payload.get("modifier")
                mid = getattr(mod, "modifier_id", 0)
                commands.append((
                    "INSERT INTO modifier_lifecycles (session_id, modifier_id, entity_id, start_frame, source_name, stat_type, value, op_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (self.session_id, mid, eid, frame_id, getattr(mod, "source", ""), getattr(mod, "stat", ""), getattr(mod, "value", 0.0), getattr(mod, "op", "ADD"))
                ))

            elif etype == "ON_MODIFIER_REMOVED":
                mod = payload.get("modifier")
                mid = getattr(mod, "modifier_id", 0)
                commands.append((
                    "UPDATE modifier_lifecycles SET end_frame = ? WHERE session_id = ? AND modifier_id = ?",
                    (frame_id, self.session_id, mid)
                ))

            elif etype == "ON_EFFECT_ADDED":
                eff = payload.get("effect")
                inst_id = getattr(eff, "instance_id", 0)
                etype_str = "SHIELD" if "Shield" in type(eff).__name__ else "STATUS"
                commands.append((
                    "INSERT INTO simulation_effect_lifecycles (session_id, instance_id, entity_id, effect_type, name, start_frame, duration) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (self.session_id, inst_id, eid, etype_str, getattr(eff, "name", "Effect"), frame_id, getattr(eff, "duration", 0))
                ))

            elif etype == "ON_EFFECT_REMOVED":
                eff = payload.get("effect")
                inst_id = getattr(eff, "instance_id", 0)
                commands.append((
                    "UPDATE simulation_effect_lifecycles SET end_frame = ? WHERE session_id = ? AND instance_id = ?",
                    (frame_id, self.session_id, inst_id)
                ))

            if etype in ("AFTER_DAMAGE", "AFTER_ELEMENTAL_REACTION", "AFTER_HEAL"):
                commands.append((
                    "INSERT INTO simulation_event_log (session_id, frame_id, event_type, source_id) VALUES (?, ?, ?, ?)",
                    (self.session_id, frame_id, etype, eid)
                ))
                commands.append((
                    "INSERT INTO event_payloads (event_id, payload_json) VALUES ((SELECT MAX(event_id) FROM simulation_event_log), ?)",
                    (json.dumps(payload, cls=GenshinJSONEncoder),)
                ))

                if etype == "AFTER_DAMAGE":
                    dmg_obj = payload.get("damage")
                    target = payload.get("target")
                    tid = getattr(target, "entity_id", 0)
                    dmg_val = getattr(dmg_obj, "damage", 0.0)
                    self.total_damage += dmg_val
                    self._damage_in_last_window += dmg_val

                    attack_tag = "None"
                    if hasattr(dmg_obj, "config") and dmg_obj.config:
                        attack_tag = getattr(dmg_obj.config.attack_tag, "name", str(dmg_obj.config.attack_tag))

                    # 存储完整的反应数据为 JSON
                    reaction_json = None
                    if hasattr(dmg_obj, "reaction_results") and dmg_obj.reaction_results:
                        rr = dmg_obj.reaction_results[0]
                        reaction_json = json.dumps({
                            "type": rr.reaction_type.name,
                            "multiplier": getattr(rr, "multiplier", 1.0),
                            "source_element": getattr(rr.source_element, "name", str(rr.source_element)) if rr.source_element else None,
                            "target_element": getattr(rr.target_element, "name", str(rr.target_element)) if rr.target_element else None,
                        })

                    # 使用专门的序列化工具处理元素类型
                    elem_str = self._serialize_element(getattr(dmg_obj, "element", "Neutral"))

                    # 提取伤害名称
                    dmg_name = getattr(dmg_obj, "name", "Unknown Damage")

                    commands.append((
                        "INSERT INTO event_damage_data (event_id, target_id, final_damage, element_type, attack_tag, is_crit, reaction, name) VALUES ((SELECT MAX(event_id) FROM simulation_event_log), ?, ?, ?, ?, ?, ?, ?)",
                        (tid, dmg_val, elem_str, attack_tag, 1 if getattr(dmg_obj, "is_crit", False) else 0, reaction_json, dmg_name)
                    ))

                    audit_trail = getattr(dmg_obj, "data", {}).get("audit_trail", [])
                    for step in audit_trail:
                        commands.append((
                            "INSERT INTO event_audit_trail (event_id, modifier_id, source_name, stat_type, value, op_type) VALUES ((SELECT MAX(event_id) FROM simulation_event_log), ?, ?, ?, ?, ?)",
                            (getattr(step, "modifier_id", None), getattr(step, "source", ""), getattr(step, "stat", ""), getattr(step, "value", 0.0), getattr(step, "op", "ADD"))
                        ))

        if frame_id - self._last_dps_calc_frame >= 60:
            self.peak_dps = max(self.peak_dps, self._damage_in_last_window)
            self._damage_in_last_window = 0.0
            self._last_dps_calc_frame = frame_id

        return commands

    def record_static_modifiers(
        self, entity_id: int, modifiers: list[Any], frame: int = 0
    ) -> list[tuple[str, tuple]]:
        """
        登记静态修饰符（武器/圣遗物）。

        静态装备属性是永久性修饰符，不需要帧级生命周期管理。
        此方法直接生成 INSERT 命令，不依赖事件捕获时机。

        注意：使用修饰符原本的 modifier_id（由 ctx.get_next_modifier_id() 分配），
        以确保后续 ON_MODIFIER_REMOVED 事件能正确匹配并更新 end_frame。

        Args:
            entity_id: 所属实体 ID
            modifiers: 修饰符列表 (ModifierRecord 对象)
            frame: 起始帧，默认为 0

        Returns:
            SQL 命令列表
        """
        commands: list[tuple[str, tuple]] = []
        for mod in modifiers:
            # 使用修饰符原本的 ID，确保与 ON_MODIFIER_REMOVED 事件匹配
            mid = getattr(mod, "modifier_id", 0)

            commands.append((
                "INSERT INTO modifier_lifecycles (session_id, modifier_id, entity_id, start_frame, source_name, stat_type, value, op_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (self.session_id, mid, entity_id, frame, getattr(mod, "source", ""), getattr(mod, "stat", ""), getattr(mod, "value", 0.0), getattr(mod, "op", "ADD"))
            ))

            # 将静态修饰符添加到活跃集合，以便后续生命周期追踪
            self.active_modifiers.add((entity_id, mid))

        return commands