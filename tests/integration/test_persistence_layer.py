import pytest
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
    await db.create_session("IntegrationTest")
    await db.start_session()

    # 模拟写入 100 帧数据
    for i in range(100):
        snapshot = {
            "frame": i,
            "global": {"move_dist": i * 0.1},
            "team": [{"entity_id": 1, "name": "香菱", "metrics": {"hp": 1000 - i}}],
            "entities_meta": [{
                "entity_id": 1,
                "entity_type": "CHARACTER",
                "name": "香菱",
                "spawn_x": 0.0, "spawn_y": 0.0, "spawn_z": 0.0,
                "hitbox_radius": 0.5, "hitbox_height": 2.0,
                "level": 90, "constellation": 0,
                "base_attributes": {"生命值": 1000}, "weapon_data": {}, "artifact_sets": [], "skill_levels": {}
            }]
        }
        db.record_snapshot(snapshot)

    # 等待 Worker 处理完成
    await db.stop_session()

    # 测试随机读取
    frame_50 = await db.get_frame(50)
    assert frame_50 is not None
    assert frame_50["frame"] == 50
    assert frame_50["team"][0]["metrics"]["hp"] == 950

    frame_99 = await db.get_frame(99)
    assert frame_99["frame"] == 99
    assert frame_99["team"][0]["metrics"]["hp"] == 901

    # 测试不存在的帧 (在此模型中，只要 session 存在，get_frame 就会返回包含实体的 Snapshot，只不过是最新状态)
    none_frame = await db.get_frame(999)
    assert none_frame is not None
    assert none_frame["frame"] == 999

    # 清理
    if os.path.exists(db_path):
        os.remove(db_path)
