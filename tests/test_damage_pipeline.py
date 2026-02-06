import unittest
from core.action.damage import Damage, DamageType
from core.systems.damage_system import DamageContext, DamagePipeline
from core.context import EventEngine
from core.entities.base_entity import BaseEntity

class MockCharacter:
    def __init__(self):
        self.level = 90
        self.attributePanel = {
            '攻击力': 1000,
            '固定攻击力': 0,
            '攻击力%': 0,
            '生命值': 10000,
            '固定生命值': 0,
            '生命值%': 0,
            '防御力': 500,
            '固定防御力': 0,
            '防御力%': 0,
            '元素精通': 0,
            '暴击率': 50.0,
            '暴击伤害': 100.0,
            '火元素伤害加成': 0.0,
            '伤害加成': 0.0
        }
        self.active_effects = []

class MockTarget:
    def __init__(self):
        self.defense = 500
        self.current_resistance = {'火': 10.0}
    
    def apply_elemental_aura(self, damage):
        return None

class TestDamagePipeline(unittest.TestCase):
    def setUp(self):
        self.engine = EventEngine()
        self.pipeline = DamagePipeline(self.engine)
        self.source = MockCharacter()
        self.target = MockTarget()
        self.damage = Damage(100.0, ('火', 1), DamageType.NORMAL, "Test Attack")
        # Initialize context
        self.ctx = DamageContext(self.damage, self.source, self.target)

    def test_snapshot_attributes(self):
        self.pipeline._snapshot(self.ctx)
        self.assertEqual(self.ctx.stats['攻击力'], 1000)
        self.assertEqual(self.ctx.stats['暴击率'], 50.0)
        self.assertEqual(self.ctx.stats['伤害加成'], 0.0)

    def test_calculate_math_simple(self):
        # 模拟快照
        self.ctx.stats['攻击力'] = 1000
        self.ctx.stats['防御区系数'] = 0.5
        self.ctx.stats['抗性区系数'] = 0.9 # 10% res -> 0.9 multiplier
        
        # 运行计算
        self.pipeline._calculate(self.ctx)
        
        # 预期: 1000(Base) * 1.0(Multiplier) * 0.5(Def) * 0.9(Res) = 450
        expected_non_crit = 1000 * 1.0 * 0.5 * 0.9
        expected_crit = expected_non_crit * 2.0 # 100% crit dmg
        
        self.assertTrue(abs(self.ctx.final_result - expected_non_crit) < 0.1 or 
                        abs(self.ctx.final_result - expected_crit) < 0.1)

    def test_add_bonus(self):
        self.ctx.add_modifier("伤害加成", 50.0)
        self.assertEqual(self.ctx.stats['伤害加成'], 50.0)

if __name__ == '__main__':
    unittest.main()