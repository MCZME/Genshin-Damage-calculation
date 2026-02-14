import pytest
from core.entities.base_entity import CombatEntity, Faction
from core.mechanics.aura import Element


class TestStateExport:
    def test_combat_entity_export_basic(self):
        """验证基础战斗实体的状态导出结构"""
        from core.context import create_context

        ctx = create_context()
        with ctx:
            entity = CombatEntity(
                name="测试目标",
                faction=Faction.ENEMY,
                pos=(1.0, 2.0, 3.0),
                hitbox=(0.5, 2.0),
            )

            # 注入一些模拟数据
            entity.attribute_data = {"攻击力": 1000.0, "生命值": 5000.0}
            entity.aura.apply_element(Element.PYRO, 1.0)

            # 执行导出
            state = entity.export_state()

            # 断言结构
            assert isinstance(state, dict)
            assert state["name"] == "测试目标"
            assert state["pos"] == [1.0, 2.0, 3.0]
            assert "attributes" in state
            assert state["attributes"]["攻击力"] == 1000.0
            assert "auras" in state
            assert isinstance(state["auras"]["regular"], list)

            # 确保没有对象引用（验证可序列化）
            import json

            try:
                json.dumps(state)
            except TypeError as e:
                pytest.fail(f"导出数据包含不可序列化对象: {e}")

    def test_character_export_logic(self):
        """验证角色子类的状态导出逻辑"""
        from core.context import create_context

        ctx = create_context()
        with ctx:
            from tests.conftest import MockAttributeEntity

            char = MockAttributeEntity()
            char.name = "香菱"

            state = char.export_state()
            assert state["name"] == "香菱"
            assert "level" in state
            assert state["level"] == 90

    def test_context_snapshot(self):
        """验证全局快照功能"""
        from core.context import create_context

        ctx = create_context()
        with ctx:
            entity = CombatEntity(name="靶子", faction=Faction.ENEMY)
            ctx.space.register(entity)

            snapshot = ctx.take_snapshot()
            assert snapshot["frame"] == 0
            assert len(snapshot["entities"]) >= 1
            assert any(e["name"] == "靶子" for e in snapshot["entities"])
