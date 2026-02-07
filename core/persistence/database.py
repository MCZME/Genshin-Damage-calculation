import aiosqlite
import json
import asyncio
from typing import Dict, Any, Optional

class ResultDatabase:
    """
    仿真结果持久化驱动 (基于 SQLite)。
    采用异步队列模式，实现非阻塞的帧快照存储。
    """
    def __init__(self, db_path: str = "simulation_results.db"):
        self.db_path = db_path
        self._queue = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None
        self._running = False

    async def initialize(self):
        """初始化数据库表结构"""
        async with aiosqlite.connect(self.db_path) as db:
            # 帧数据表 (使用 frame_id 作为索引实现 O(1) 随机访问)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS frames (
                    frame_id INTEGER PRIMARY KEY,
                    data TEXT NOT NULL
                )
            """)
            # 事件数据表 (用于 DPS 分析和计算溯源)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    frame_id INTEGER,
                    event_type TEXT,
                    payload TEXT,
                    FOREIGN KEY(frame_id) REFERENCES frames(frame_id)
                )
            """)
            await db.commit()

    async def start_session(self):
        """启动后台持久化 Worker"""
        self._running = True
        self._worker_task = asyncio.create_task(self._worker())

    async def stop_session(self):
        """停止 Worker 并等待队列清空"""
        self._running = False
        if self._worker_task:
            await self._queue.put(None) # 结束信号
            await self._worker_task

    def record_snapshot(self, snapshot: dict):
        """同步接口：将快照压入写入队列"""
        self._queue.put_nowait(snapshot)

    async def _worker(self):
        """后台写入进程"""
        async with aiosqlite.connect(self.db_path) as db:
            # 开启 WAL 模式提高并发读写性能
            await db.execute("PRAGMA journal_mode=WAL")
            
            while True:
                item = await self._queue.get()
                if item is None:
                    break
                
                frame_id = item["frame"]
                # 序列化为 JSON 存储 (后续若追求性能可换 MsgPack)
                await db.execute(
                    "INSERT OR REPLACE INTO frames (frame_id, data) VALUES (?, ?)",
                    (frame_id, json.dumps(item))
                )
                
                # 批量处理该帧发生的事件 (如果有)
                # 注：此处假设 snapshot 中已包含当前帧事件，或后续通过独立接口 record_event 传入
                
                if self._queue.empty():
                    await db.commit()
                
                self._queue.task_done()
            
            await db.commit()

    async def get_frame(self, frame_id: int) -> Optional[dict]:
        """[核心功能] 瞬间读取任意帧状态"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT data FROM frames WHERE frame_id = ?", (frame_id,)) as cursor:
                row = await cursor.fetchone()
                return json.loads(row[0]) if row else None
