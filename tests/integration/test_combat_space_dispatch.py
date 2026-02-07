import pytest
from core.context import create_context, get_context
from core.target import Target
from core.action.damage import Damage, DamageType
from core.mechanics.aura import Element
from core.event import GameEvent, EventType
from core.tool import GetCurrentTime

class TestCombatSpaceDispatch:
    """
    集成测试：验证 CombatSpace 的广播与派发链路。
    """

    @pytest.fixture
    def sim_ctx(self):
        """创建完整的仿真上下文"""
        ctx = create_context()
        yield ctx

    def test_basic_broadcast_hit(self, sim_ctx):
        """验证基础广播：圆形伤害命中目标"""
        # 1. 准备目标
        target_data = {
            'level': 90,
            'resists': {k: 10.0 for k in ['火', '水', '雷', '草', '冰', '岩', '风', '物理']}
        }
        enemy = Target(target_data)
        enemy.set_position(0.0, 0.0) # 放在原点
        sim_ctx.space.register(enemy)
        
        # 2. 构造攻击者 (Mock)
        class MockChar:
            def __init__(self):
                self.name = "Attacker"
                self.level = 90
                self.pos = [0.0, 0.0, 0.0]
                self.facing = 0.0
                self.attributePanel = {
                    '攻击力': 1000.0,
                    '元素精通': 0.0,
                    '暴击率': 5.0,
                    '暴击伤害': 50.0,
                    '火元素伤害加成': 0.0
                }
                self.active_effects = []
        attacker = MockChar()

        # 3. 发起伤害广播
        dmg = Damage(
            damage_multiplier=100.0, 
            element=(Element.PYRO, 1.0), 
            damage_type=DamageType.NORMAL, 
            name="测试火球",
            aoe_shape='CIRCLE',
            radius=5.0
        )
        
        event = GameEvent(
            EventType.BEFORE_DAMAGE, 
            GetCurrentTime(), 
            source=attacker,
            data={'character': attacker, 'damage': dmg}
        )
        
        sim_ctx.event_engine.publish(event)
        
        # 4. 断言验证
        assert dmg.target == enemy
        # 检查 enemy 是否产生了附着 (检查 auras 列表中是否存在对应元素)
        assert any(a.element == Element.PYRO for a in enemy.aura.auras)
        # 1000 * 0.5 * 0.9 = 450
        assert dmg.damage == pytest.approx(450.0)

    def test_broadcast_miss(self, sim_ctx):
        """验证广播未命中：超出范围"""
        target_data = {'level': 90, 'resists': {k: 10.0 for k in ['火', '水', '雷', '草', '冰', '岩', '风', '物理']}}
        enemy = Target(target_data)
        enemy.set_position(10.0, 10.0) # 放在远处
        sim_ctx.space.register(enemy)
        
        class MockChar:
            def __init__(self):
                self.name = "Attacker"
                self.level = 90
                self.pos = [0.0, 0.0, 0.0]
                self.facing = 0.0
                self.attributePanel = {k: 0.0 for k in ['攻击力', '元素精通', '暴击率', '暴击伤害']}
                self.active_effects = []
        attacker = MockChar()

        dmg = Damage(100.0, (Element.PYRO, 1.0), DamageType.NORMAL, "打不到", radius=5.0)
        event = GameEvent(EventType.BEFORE_DAMAGE, GetCurrentTime(), source=attacker, 
                          data={'character': attacker, 'damage': dmg})
        
        sim_ctx.event_engine.publish(event)
        
        assert dmg.target is None
        assert dmg.damage == 0.0
