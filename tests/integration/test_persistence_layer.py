import pytest
import asyncio
import os
from core.persistence.database import ResultDatabase

@pytest.mark.asyncio
async def test_persistence_random_access():
    """验证 SQLite 持久化层的随机存取性能与正确性"""
    db_path = "test_sim.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        
    db = ResultDatabase(db_path)
    await db.initialize()
    await db.start_session()
    
    # 模拟写入 100 帧数据
    for i in range(100):
        snapshot = {
            "frame": i,
            "global": {"move_dist": i * 0.1},
            "entities": [{"name": "香菱", "hp": 1000 - i}]
        }
        db.record_snapshot(snapshot)
        
    # 等待 Worker 处理完成
    await db.stop_session()
    
    # 测试随机读取
    frame_50 = await db.get_frame(50)
    assert frame_50 is not None
    assert frame_50["frame"] == 50
    assert frame_50["entities"][0]["hp"] == 950
    
    frame_99 = await db.get_frame(99)
    assert frame_99["frame"] == 99
    
    # 测试不存在的帧
    none_frame = await db.get_frame(999)
    assert none_frame is None
    
    # 清理
    if os.path.exists(db_path):
        os.remove(db_path)
