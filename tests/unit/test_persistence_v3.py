import pytest
import os
import aiosqlite
from core.persistence.database import ResultDatabase
from core.persistence.adapter import ReviewDataAdapter
from core.systems.contract.modifier import ModifierRecord

@pytest.mark.asyncio
async def test_persistence_full_flow():
    """
    全链路持久化测试：从 Schema 初始化到数据投影，再到快照重建。
    """
    db_path = "test_audit.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        
    db = ResultDatabase(db_path)
    await db.initialize()
    
    # 1. 创建 Session
    session_id = await db.create_session("Unit_Test_Session", {"config": "test"})
    assert session_id > 0
    assert db.projector is not None
    
    # 启动 Worker
    await db.start_session()
    
    try:
        # 2. 构造模拟快照 - 帧 1 (实体登记 & 初始状态)
        snapshot_f1 = {
            "frame": 1,
            "entities_meta": [
                {
                    "entity_id": 101, "entity_type": "CHARACTER", "name": "测试角色",
                    "level": 90, "constellation": 0, "spawn_x": 0, "spawn_y": 0, "spawn_z": 0,
                    "hitbox_radius": 0.3, "hitbox_height": 1.8,
                    "base_attributes": {"攻击力": 1000}, "weapon_data": {"name": "试作斩岩"},
                    "artifact_sets": ["角斗士2"], "skill_levels": {"normal": 9}
                },
                {
                    "entity_id": 201, "entity_type": "TARGET", "name": "测试木桩",
                    "spawn_x": 10, "spawn_y": 0, "spawn_z": 0, "hitbox_radius": 0.5, "hitbox_height": 2.0,
                    "level": 90, "base_defense": 500, "res_phys": 10, "res_fire": 10, "res_water": 10,
                    "res_wind": 10, "res_elec": 10, "res_grass": 10, "res_ice": 10, "res_rock": 10
                }
            ],
            "team": [
                {"entity_id": 101, "pos": [0, 0, 0], "action_id": "IDLE", "on_field": True}
            ],
            "entities": [
                {"entity_id": 201, "pos": [10, 0, 0], "auras": {"regular": []}}
            ],
            "events": [
                {
                    "type": "ON_MODIFIER_ADDED", "source_id": 101,
                    "payload": {"modifier": ModifierRecord(modifier_id=501, source="测试增益", stat="攻击力%", value=20.0, op="ADD")}
                }
            ]
        }
        
        db.record_snapshot(snapshot_f1)
        
        # 3. 构造模拟快照 - 帧 60 (状态跳变 & 伤害事件)
        # 模拟角色移动，能量增加，产生伤害
        snapshot_f60 = {
            "frame": 60,
            "team": [
                {"entity_id": 101, "pos": [1, 0, 1], "action_id": "SKILL", "on_field": True}
            ],
            "entities": [
                {"entity_id": 201, "pos": [10, 0, 0], "auras": {"regular": [{"element": "Fire", "value": 1.0}]}}
            ],
            "events": [
                # A. 资源跳变
                {
                    "type": "AFTER_ENERGY_CHANGE", "source_id": 101,
                    "payload": {"new_energy": 40.0, "delta": 10.0}
                },
                # B. 伤害与审计链
                {
                    "type": "AFTER_DAMAGE", "source_id": 101,
                    "payload": {
                        "damage": type('obj', (object,), {
                            "damage": 5000.0, "element": "Fire", "attack_tag": "SKILL", "is_crit": True, "reaction_name": "VAPORIZE",
                            "data": {"audit_trail": [
                                ModifierRecord(modifier_id=0, source="面板", stat="攻击力", value=1000.0, op="SET"),
                                ModifierRecord(modifier_id=501, source="测试增益", stat="攻击力%", value=20.0, op="ADD")
                            ]}
                        }),
                        "target": type('obj', (object,), {"entity_id": 201}),
                        "source_name": "测试角色"
                    }
                }
            ]
        }
        
        db.record_snapshot(snapshot_f60)
        
        # 4. 构造模拟快照 - 帧 120 (Buff 结束)
        snapshot_f120 = {
            "frame": 120,
            "team": [
                {"entity_id": 101, "pos": [1, 0, 1], "action_id": "SKILL", "on_field": True} # 位置未变，不应产生 Pulse 记录
            ],
            "events": [
                {
                    "type": "ON_MODIFIER_REMOVED", "source_id": 101,
                    "payload": {"modifier": ModifierRecord(modifier_id=501, source="测试增益", stat="攻击力%", value=20.0, op="ADD")}
                }
            ]
        }
        
        db.record_snapshot(snapshot_f120)
        
        # 停止 Session 以确保数据刷盘
        await db.stop_session()
        
        # --- 验证环节 (ReviewDataAdapter) ---
        adapter = ReviewDataAdapter(db_path, session_id)
        
        # V1: 验证静态登记
        async with aiosqlite.connect(db_path) as conn:
            async with conn.execute("SELECT name, entity_type FROM simulation_entity_registry WHERE session_id=?", (session_id,)) as cur:
                rows = await cur.fetchall()
                assert len(rows) == 2
                assert rows[0][1] == "CHARACTER"
        
        # V2: 验证增量还原 (第 60 帧)
        frame_60 = await adapter.get_frame(60)
        # [V9.3] 坐标已移除，验证能量值
        assert frame_60["team"][0]["current_energy"] == 40.0
        # 验证审计明细中 Buff 关联 (Mid 501 在 60 帧应该 Active)
        mods = frame_60["team"][0]["active_modifiers"]
        # modifier_id 现在以 name 字段表示 source_name
        assert any(m["name"] == "测试增益" for m in mods)

        # V3: 验证伤害特化与明细
        dps_data = await adapter.get_dps_data()
        assert len(dps_data) == 1
        assert dps_data[0]["value"] == 5000.0

        # 验证审计瀑布图数据
        audit_steps = await adapter.get_damage_audit(1) # event_id 应该为 1
        assert len(audit_steps) == 2
        assert audit_steps[1]["modifier_id"] == 501

        # V4: 验证增量 Pulse (120 帧 Buff 应该已失效)
        frame_120 = await adapter.get_frame(120)
        # Buff 应该已失效
        assert len(frame_120["team"][0]["active_modifiers"]) == 0

    finally:
        if os.path.exists(db_path):
            pass # 暂时保留用于手动检查

if __name__ == "__main__":
    pytest.main([__file__])
