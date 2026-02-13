import pytest
from core.context import create_context
from core.target import Target
from core.systems.contract.damage import Damage, DamageType
from core.mechanics.aura import Element
from core.event import GameEvent, EventType
from core.tool import get_current_time
from core.entities.base_entity import Faction

class TestCombatSpaceDispatch:
    @pytest.fixture
    def sim_ctx(self):
        return create_context()

    def test_basic_broadcast_hit(self, sim_ctx):
        """验证基础广播：圆形伤害命中目标"""
        target_data = {'level': 90, 'resists': {k: 10.0 for k in ['火', '水', '雷', '草', '冰', '岩', '风', '物理']}}
        enemy = Target(target_data)
        enemy.set_position(0.0, 0.0)
        sim_ctx.space.register(enemy)

        class MockChar:
            def __init__(self):
                self.name = "Attacker"
                self.faction = Faction.PLAYER
                self.level = 90
                self.pos = [0.0, 0.0, 0.0]
                self.facing = 0.0
                self.attribute_data = {
                    '攻击力': 1000.0,
                    '元素精通': 0.0,
                    '暴击率': 5.0,
                    '暴击伤害': 50.0,
                    '火元素伤害加成': 0.0
                }
                self.active_effects = []
        attacker = MockChar()

        dmg = Damage(100.0, (Element.PYRO, 1.0), DamageType.NORMAL, "测试火球")
        dmg.data.update({'aoe_shape': 'CIRCLE', 'radius': 5.0})

        event = GameEvent(EventType.BEFORE_DAMAGE, get_current_time(), source=attacker,
                          data={'character': attacker, 'damage': dmg})
        sim_ctx.event_engine.publish(event)

        assert dmg.target == enemy

    def test_broadcast_miss(self, sim_ctx):
        """验证广播未命中：超出范围"""
        target_data = {'level': 90, 'resists': {k: 10.0 for k in ['火', '水', '雷', '草', '冰', '岩', '风', '物理']}}
        enemy = Target(target_data)
        enemy.set_position(10.0, 10.0)
        sim_ctx.space.register(enemy)

        class MockChar:
            def __init__(self):
                self.name = "Attacker"
                self.faction = Faction.PLAYER
                self.level = 90
                self.pos = [0.0, 0.0, 0.0]
                self.facing = 0.0
                self.attribute_data = {k: 0.0 for k in ['攻击力', '元素精通', '暴击率', '暴击伤害']}
                self.active_effects = []
        attacker = MockChar()

        dmg = Damage(100.0, (Element.PYRO, 1.0), DamageType.NORMAL, "打不到")
        dmg.data.update({'aoe_shape': 'CIRCLE', 'radius': 5.0})
        
        event = GameEvent(EventType.BEFORE_DAMAGE, get_current_time(), source=attacker,
                          data={'character': attacker, 'damage': dmg})
        sim_ctx.event_engine.publish(event)

        assert dmg.target is None
