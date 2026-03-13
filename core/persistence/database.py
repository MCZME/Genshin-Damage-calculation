from __future__ import annotations
import aiosqlite
import json
import asyncio
from typing import Any, cast
from enum import Enum
from dataclasses import is_dataclass, asdict

class GenshinJSONEncoder(json.JSONEncoder):
    """
    通用 JSON 编码器：处理枚举、数据类及特殊对象。
    """
    def default(self, o: Any) -> Any:
        # [FIX] 参数名从 obj 改为 o，以匹配基类 JSONEncoder.default
        if isinstance(o, Enum):
            return o.name
        if is_dataclass(o):
            # [FIX] 使用 cast(Any, o) 修复 Pylance 对 asdict 参数类型的严格检查
            return asdict(cast(Any, o))
        if hasattr(o, "to_dict"):
            return o.to_dict()
        if hasattr(o, "name"):
            return o.name
        try:
            return super().default(o)
        except TypeError:
            return str(o)

class ResultDatabase:
    """
    [V3.0 重新设计] 仿真结果持久化引擎。
    作为存储执行层，仅负责 SQL 事务管理与基础 I/O。
    核心投影逻辑已剥离至 DataProjector。
    """

    def __init__(self, db_path: str = "simulation_audit.db"):
        self.db_path = db_path
        self._queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()
        self._worker_task: asyncio.Task[None] | None = None
        self._running = False
        self.session_id: int | None = None
        self.projector: Any | None = None # 延迟初始化

    async def initialize(self):
        """
        初始化数据库表结构 (V3.0 静态登记四表架构)。
        """
        async with aiosqlite.connect(self.db_path) as db:
            # 开启 WAL 模式提高并发性能
            await db.execute("PRAGMA journal_mode=WAL")
            await db.execute("PRAGMA foreign_keys=ON")

            # 1. 仿真会话与详情 (垂直拆分)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS simulation_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_name TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    total_damage REAL DEFAULT 0,
                    duration_frames INTEGER DEFAULT 0,
                    avg_dps REAL DEFAULT 0,
                    peak_dps REAL DEFAULT 0
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS simulation_configs (
                    session_id INTEGER PRIMARY KEY,
                    config_snapshot TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES simulation_sessions(id) ON DELETE CASCADE
                )
            """)

            # 2. 通用实体注册表 (身份与物理体积)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS simulation_entity_registry (
                    session_id INTEGER,
                    entity_id INTEGER,
                    entity_type TEXT NOT NULL, -- CHARACTER, TARGET, CONSTRUCT
                    name TEXT NOT NULL,
                    spawn_x REAL,
                    spawn_y REAL,
                    spawn_z REAL,
                    hitbox_radius REAL, -- 碰撞圆柱底部半径
                    hitbox_height REAL, -- 碰撞圆柱高度
                    PRIMARY KEY (session_id, entity_id),
                    FOREIGN KEY (session_id) REFERENCES simulation_sessions(id) ON DELETE CASCADE
                )
            """)

            # 3. 基础/召唤实体表 (时效与归属)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS simulation_entities (
                    session_id INTEGER,
                    entity_id INTEGER,
                    owner_id INTEGER, -- 所属者 ID (用于追溯)
                    created_frame INTEGER,
                    duration INTEGER,
                    PRIMARY KEY (session_id, entity_id),
                    FOREIGN KEY (session_id, entity_id) REFERENCES simulation_entity_registry(session_id, entity_id) ON DELETE CASCADE
                )
            """)

            # 4. 战斗目标表 (防御与 8 大平铺抗性)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS simulation_targets (
                    session_id INTEGER,
                    entity_id INTEGER,
                    level INTEGER,
                    base_defense REAL,
                    res_phys REAL, -- 物理抗性
                    res_fire REAL, -- 火元素抗性
                    res_water REAL, -- 水元素抗性
                    res_wind REAL, -- 风元素抗性
                    res_elec REAL, -- 雷元素抗性
                    res_grass REAL, -- 草元素抗性
                    res_ice REAL, -- 冰元素抗性
                    res_rock REAL, -- 岩元素抗性
                    PRIMARY KEY (session_id, entity_id),
                    FOREIGN KEY (session_id, entity_id) REFERENCES simulation_entity_registry(session_id, entity_id) ON DELETE CASCADE
                )
            """)

            # 5. 角色详细面板表 (核心计算种子)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS simulation_characters (
                    session_id INTEGER,
                    entity_id INTEGER,
                    level INTEGER,
                    constellation INTEGER,
                    base_attributes TEXT, -- JSON: 初始 attribute_data 快照
                    weapon_data TEXT,     -- JSON: 名称、精炼等
                    artifact_sets TEXT,   -- JSON: 激活的套装名称列表
                    skill_levels TEXT,    -- JSON: A/E/Q 等级
                    PRIMARY KEY (session_id, entity_id),
                    FOREIGN KEY (session_id, entity_id) REFERENCES simulation_entity_registry(session_id, entity_id) ON DELETE CASCADE
                )
            """)

            # 6. 角色动态轨迹表 (Pulse)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS character_pulses (
                    session_id INTEGER,
                    frame_id INTEGER,
                    entity_id INTEGER,
                    x REAL,
                    y REAL,
                    z REAL,
                    action_id TEXT, -- 当前执行的指令名
                    is_on_field INTEGER, -- 0 or 1
                    PRIMARY KEY (session_id, frame_id, entity_id),
                    FOREIGN KEY (session_id, entity_id) REFERENCES simulation_characters(session_id, entity_id) ON DELETE CASCADE
                )
            """)

            # 7. 修饰符生命周期记录表 (Lifecycle)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS modifier_lifecycles (
                    session_id INTEGER,
                    modifier_id INTEGER,
                    entity_id INTEGER,
                    start_frame INTEGER NOT NULL,
                    end_frame INTEGER, -- 可为 NULL
                    source_name TEXT,
                    stat_type TEXT,
                    value REAL,
                    op_type TEXT,
                    PRIMARY KEY (session_id, modifier_id),
                    FOREIGN KEY (session_id) REFERENCES simulation_sessions(id) ON DELETE CASCADE
                )
            """)

            # 8. 骨干事件表 (瞬时事件索引)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS simulation_event_log (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    frame_id INTEGER,
                    event_type TEXT NOT NULL,
                    source_id INTEGER,
                    FOREIGN KEY (session_id) REFERENCES simulation_sessions(id) ON DELETE CASCADE
                )
            """)

            # 9. 事件负载表 (冷数据隔离存储)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS event_payloads (
                    event_id INTEGER PRIMARY KEY,
                    payload_json TEXT NOT NULL,
                    FOREIGN KEY (event_id) REFERENCES simulation_event_log(event_id) ON DELETE CASCADE
                )
            """)

            # 10. 事件审计明细表 (计算步骤溯源)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS event_audit_trail (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER,
                    modifier_id INTEGER, -- 可为 NULL (系统计算)
                    source_name TEXT,
                    stat_type TEXT,
                    value REAL,
                    op_type TEXT, -- SET, ADD, MULT
                    FOREIGN KEY (event_id) REFERENCES simulation_event_log(event_id) ON DELETE CASCADE
                )
            """)

            # 11. 伤害特化数据表 (高性能统计)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS event_damage_data (
                    event_id INTEGER PRIMARY KEY,
                    target_id INTEGER NOT NULL,
                    final_damage REAL NOT NULL,
                    element_type TEXT,
                    attack_tag TEXT, -- NORMAL, SKILL, BURST, etc.
                    is_crit INTEGER, -- 0/1
                    reaction_name TEXT, -- 可为 NULL
                    FOREIGN KEY (event_id) REFERENCES simulation_event_log(event_id) ON DELETE CASCADE
                )
            """)

            # 12. 资源状态跳变表 (能量与血量)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS simulation_state_jumps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    frame_id INTEGER NOT NULL,
                    entity_id INTEGER NOT NULL,
                    jump_type TEXT NOT NULL, -- ENERGY, HP
                    new_value REAL NOT NULL,
                    delta_value REAL,
                    FOREIGN KEY (session_id) REFERENCES simulation_sessions(id) ON DELETE CASCADE
                )
            """)

            # 13. 效果与护盾生命周期表
            await db.execute("""
                CREATE TABLE IF NOT EXISTS simulation_effect_lifecycles (
                    session_id INTEGER,
                    instance_id INTEGER, -- 由引擎分配的唯一实例 ID
                    entity_id INTEGER NOT NULL,
                    effect_type TEXT NOT NULL, -- SHIELD, STATUS
                    name TEXT NOT NULL,
                    start_frame INTEGER NOT NULL,
                    end_frame INTEGER,
                    duration INTEGER, -- 预期持续时间
                    PRIMARY KEY (session_id, instance_id),
                    FOREIGN KEY (session_id) REFERENCES simulation_sessions(id) ON DELETE CASCADE
                )
            """)

            # 14. 护盾数值跳变记录表
            await db.execute("""
                CREATE TABLE IF NOT EXISTS simulation_shield_jumps (
                    session_id INTEGER,
                    instance_id INTEGER,
                    frame_id INTEGER NOT NULL,
                    current_shield_hp REAL NOT NULL,
                    PRIMARY KEY (session_id, instance_id, frame_id),
                    FOREIGN KEY (session_id, instance_id) REFERENCES simulation_effect_lifecycles(session_id, instance_id) ON DELETE CASCADE
                )
            """)

            # 15. 目标元素附着脉搏表 (仅针对 Target)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS target_aura_pulses (
                    session_id INTEGER,
                    frame_id INTEGER NOT NULL,
                    entity_id INTEGER NOT NULL,
                    aura_state TEXT NOT NULL, -- JSON 序列化后的附着状态
                    PRIMARY KEY (session_id, frame_id, entity_id),
                    FOREIGN KEY (session_id) REFERENCES simulation_sessions(id) ON DELETE CASCADE
                )
            """)

            # 16. 通用机制指标跳变表 (如：气氛值、层数、特殊能量)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS simulation_mechanism_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    frame_id INTEGER NOT NULL,
                    entity_id INTEGER NOT NULL,
                    metric_key TEXT NOT NULL,
                    value REAL NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES simulation_sessions(id) ON DELETE CASCADE
                )
            """)

            # 索引优化
            await db.execute("CREATE INDEX IF NOT EXISTS idx_char_pulse_lookup ON character_pulses(session_id, frame_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_modifier_lookup ON modifier_lifecycles(session_id, entity_id, start_frame)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_event_log_lookup ON simulation_event_log(session_id, frame_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_state_jump_lookup ON simulation_state_jumps(session_id, entity_id, frame_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_effect_lookup ON simulation_effect_lifecycles(session_id, entity_id, start_frame)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_metric_jump_lookup ON simulation_mechanism_metrics(session_id, entity_id, metric_key)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_audit_trail_lookup ON event_audit_trail(event_id)")

            await db.commit()

    async def create_session(self, config_name: str, config_snapshot: dict[str, Any] | None = None) -> int:
        """
        创建一个新的仿真会话，并将重型配置数据存储在详情表中。
        同时初始化业务投影器。
        """
        # [FIX] 将 config_snapshot 的类型标注改为 dict[str, Any] | None = None 修复 Pylance 报错
        async with aiosqlite.connect(self.db_path) as db:
            # 1. 插入会话元数据
            cursor = await db.execute(
                "INSERT INTO simulation_sessions (config_name) VALUES (?)",
                (config_name,)
            )
            session_id = cast(int, cursor.lastrowid)

            # 2. 插入重型配置快照
            if config_snapshot:
                await db.execute(
                    "INSERT INTO simulation_configs (session_id, config_snapshot) VALUES (?, ?)",
                    (session_id, json.dumps(config_snapshot, cls=GenshinJSONEncoder))
                )
            
            await db.commit()
            self.session_id = session_id
            
            # 3. 初始化投影器
            from core.persistence.projector import DataProjector
            self.projector = DataProjector(session_id)
            
            return session_id

    async def start_session(self):
        """启动后台写入 Worker"""
        self._running = True
        self._worker_task = asyncio.create_task(self._worker())

    async def stop_session(self):
        """停止 Worker 并等待队列清空"""
        self._running = False
        if self._worker_task:
            await self._queue.put(None)
            await self._worker_task

    def record_snapshot(self, snapshot: dict[str, Any]):
        """压入待处理数据"""
        self._queue.put_nowait(snapshot)

    async def _worker(self):
        """后台分发逻辑 (V3.0 投影分流版 - 增强调试)"""
        if not self.projector:
            return

        from core.logger import get_emulation_logger

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA foreign_keys=ON")
            await db.execute("PRAGMA journal_mode=WAL")
            
            while True:
                item = await self._queue.get()
                if item is None:
                    break
                
                # 1. 获取所有轨道的 SQL 指令
                commands: list[tuple[str, Any]] = []
                commands.extend(self.projector.project_static_meta(item))
                commands.extend(self.projector.project_pulse(item))
                commands.extend(self.projector.project_metrics(item))
                commands.extend(self.projector.project_events(item))
                
                # 2. 批量执行指令集 (在同一个原子操作中)
                sql = "None"
                params = "None"
                try:
                    for sql, params in commands:
                        await db.execute(sql, params)
                except Exception as e:
                    get_emulation_logger().log_error(
                        f"持久化执行失败: {e}\n最近一条SQL: {sql}\n参数: {params}",
                        sender="Persistence"
                    )
                    # 如果发生外键冲突，跳过当前快照以保护后续数据
                    pass

                # 3. 定期提交
                if self._queue.empty() or item.get("frame", 0) % 60 == 0:
                    await db.commit()
                
                self._queue.task_done()

            # --- 4. 仿真结束，执行 Session 汇总回写 ---
            if self.projector:
                proj = self.projector
                avg_dps = proj.total_damage / (proj.max_frame / 60.0) if proj.max_frame > 0 else 0
                await db.execute(
                    "UPDATE simulation_sessions SET total_damage=?, duration_frames=?, avg_dps=?, peak_dps=? WHERE id=?",
                    (proj.total_damage, proj.max_frame, avg_dps, proj.peak_dps, self.session_id)
                )
                await db.commit()

    async def get_frame(self, frame_id: int) -> dict[str, Any] | None:
        """按帧 ID 获取快照数据 (重定向到外部适配器)"""
        from core.persistence.adapter import ReviewDataAdapter
        if self.session_id is None:
            return None
        adapter = ReviewDataAdapter(self.db_path, self.session_id)
        return await adapter.get_frame(frame_id)

    async def record_static_modifiers(self, entity_id: int, modifiers: list[Any]) -> None:
        """
        记录实体的静态修饰符（武器/圣遗物）。

        静态属性修饰符是永久性的，不需要帧级生命周期管理。
        此方法直接写入数据库，不依赖事件捕获时机。

        Args:
            entity_id: 所属实体 ID
            modifiers: 修饰符列表 (ModifierRecord 对象)
        """
        if not self.projector or not modifiers:
            return

        commands = self.projector.record_static_modifiers(entity_id, modifiers)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA foreign_keys=ON")
            for sql, params in commands:
                await db.execute(sql, params)
            await db.commit()
