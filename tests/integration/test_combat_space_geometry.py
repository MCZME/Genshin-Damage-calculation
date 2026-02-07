import pytest
import math
from core.context import create_context
from core.target import Target
from core.action.damage import Damage, DamageType
from core.mechanics.aura import Element
from core.event import GameEvent, EventType
from core.tool import GetCurrentTime

class TestCombatSpaceGeometry:
    """
    几何实验室：验证 CombatSpace 对不同 AOE 形状与 Hitbox 的判定精度。
    """

    @pytest.fixture
    def sim_ctx(self):
        ctx = create_context()
        yield ctx

    @pytest.fixture
    def attacker(self):
        class MockChar:
            def __init__(self):
                self.name = "Attacker"
                self.level = 90
                self.pos = [0.0, 0.0, 0.0]
                self.facing = 0.0 # 默认朝向正 X 轴 (0度)
                self.attributePanel = {'攻击力': 1000.0, '元素精通': 0.0, '暴击率': 0.0, '暴击伤害': 0.0}
                self.active_effects = []
        return MockChar()

    def test_circle_edge_hit(self, sim_ctx, attacker):
        """测试圆形擦边：攻击半径5 + 实体半径0.5 = 5.5有效范围"""
        enemy = Target({'level': 90, 'resists': {k: 0.0 for k in ['火', '水', '雷', '草', '冰', '岩', '风', '物理']}})
        enemy.hitbox_radius = 0.5
        enemy.set_position(5.4, 0.0) # 距离 5.4
        sim_ctx.space.register(enemy)
        
        dmg = Damage(100.0, (Element.PHYSICAL, 0), DamageType.NORMAL, "圆擦边", aoe_shape='CIRCLE', radius=5.0)
        sim_ctx.event_engine.publish(GameEvent(EventType.BEFORE_DAMAGE, GetCurrentTime(), source=attacker, data={'character': attacker, 'damage': dmg}))
        
        assert dmg.target == enemy

    def test_box_hit_rotation(self, sim_ctx, attacker):
        """测试矩形判定：长5宽2，朝向 90度 (正Z轴)"""
        attacker.facing = 90.0
        enemy = Target({'level': 90, 'resists': {k: 0.0 for k in ['火', '水', '雷', '草', '冰', '岩', '风', '物理']}})
        enemy.hitbox_radius = 0.5
        # 目标放在 (0, 4) 处。在攻击者的正前方 4米。
        enemy.set_position(0.0, 4.0)
        sim_ctx.space.register(enemy)
        
        dmg = Damage(100.0, (Element.PHYSICAL, 0), DamageType.NORMAL, "矩形命中", aoe_shape='BOX', length=5.0, width=2.0)
        sim_ctx.event_engine.publish(GameEvent(EventType.BEFORE_DAMAGE, GetCurrentTime(), source=attacker, data={'character': attacker, 'damage': dmg}))
        
        assert dmg.target == enemy

    def test_sector_hit_edge(self, sim_ctx, attacker):
        """测试扇形判定：半径5，角度90 (正负45度)"""
        attacker.facing = 0.0 # 朝向正 X
        enemy = Target({'level': 90, 'resists': {k: 0.0 for k in ['火', '水', '雷', '草', '冰', '岩', '风', '物理']}})
        enemy.hitbox_radius = 1.0
        # 目标放在 (4, 2) 处。
        # 角度为 atan2(2, 4) = 约 26.5 度。在 45 度范围内。
        enemy.set_position(4.0, 2.0)
        sim_ctx.space.register(enemy)
        
        dmg = Damage(100.0, (Element.PHYSICAL, 0), DamageType.NORMAL, "扇形命中", aoe_shape='SECTOR', radius=5.0, fan_angle=90.0)
        sim_ctx.event_engine.publish(GameEvent(EventType.BEFORE_DAMAGE, GetCurrentTime(), source=attacker, data={'character': attacker, 'damage': dmg}))
        
        assert dmg.target == enemy

    def test_offset_hit(self, sim_ctx, attacker):
        """测试位移偏移：攻击点在角色前方 5 米处释放圆形 AOE"""
        attacker.pos = [0.0, 0.0, 0.0]
        attacker.facing = 0.0 # 朝向 X+
        
        # 怪物在 (5, 0)
        enemy = Target({'level': 90, 'resists': {k: 0.0 for k in ['火', '水', '雷', '草', '冰', '岩', '风', '物理']}})
        enemy.set_position(5.0, 0.0)
        sim_ctx.space.register(enemy)
        
        # 攻击半径很小(1.0)，但偏移设为 (5.0, 0.0)
        dmg = Damage(100.0, (Element.PHYSICAL, 0), DamageType.NORMAL, "偏移攻击", 
                     aoe_shape='CIRCLE', radius=1.0, offset=(5.0, 0.0))
        
        sim_ctx.event_engine.publish(GameEvent(EventType.BEFORE_DAMAGE, GetCurrentTime(), source=attacker, data={'character': attacker, 'damage': dmg}))
        
        assert dmg.target == enemy
