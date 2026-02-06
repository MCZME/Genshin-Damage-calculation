import pytest
from core.systems.utils import AttributeCalculator
from core.base_entity import BaseEntity
from core.context import SimulationContext

class MockEntity:
    def __init__(self):
        self.attributePanel = {
            '攻击力': 1000,
            '攻击力%': 20,
            '固定攻击力': 100,
            '生命值': 10000,
            '生命值%': 10,
            '固定生命值': 500,
            '防御力': 800,
            '防御力%': 15,
            '固定防御力': 50,
            '元素精通': 200,
            '护盾强效': 35,
            '伤害加成': 15,
            '火元素伤害加成': 46.6,
            '暴击率': 60,
            '暴击伤害': 120,
            '反应系数提高': {'蒸发': 15}
        }

def test_attribute_calculator():
    entity = MockEntity()
    
    # 攻击力: 1000 * (1 + 20/100) + 100 = 1200 + 100 = 1300
    atk = AttributeCalculator.get_attack(entity)
    print(f"ATK: {atk}")
    assert atk == pytest.approx(1300)
    
    # 生命值: 10000 * (1 + 10/100) + 500 = 11000 + 500 = 11500
    hp = AttributeCalculator.get_hp(entity)
    print(f"HP: {hp}")
    assert hp == pytest.approx(11500)
    
    # 防御力: 800 * (1 + 15/100) + 50 = 920 + 50 = 970
    dfe = AttributeCalculator.get_defense(entity)
    print(f"DEF: {dfe}")
    assert dfe == pytest.approx(970)
    
    # 元素精通
    assert AttributeCalculator.get_mastery(entity) == 200

    # 护盾强效
    # 35% -> 0.35
    shield_bonus = AttributeCalculator.get_shield_strength_bonus(entity)
    print(f"Shield Bonus: {shield_bonus}")
    assert shield_bonus == pytest.approx(0.35)

    # 伤害加成
    # 通用 15% + 火 46.6% = 61.6% -> 0.616
    dmg_bonus = AttributeCalculator.get_damage_bonus(entity, '火')
    print(f"Fire Damage Bonus: {dmg_bonus}")
    assert dmg_bonus == pytest.approx(0.616)
    
    # 暴击
    assert AttributeCalculator.get_crit_rate(entity) == pytest.approx(0.6)
    assert AttributeCalculator.get_crit_damage(entity) == pytest.approx(1.2)

    # 反应加成
    assert AttributeCalculator.get_reaction_bonus_dict(entity).get('蒸发') == 15

    print("AttributeCalculator Test Passed!")

def test_base_entity_context():
    # 1. 测试显式传递 context
    ctx = SimulationContext()
    entity = BaseEntity("TestEntity", context=ctx)
    assert entity.ctx == ctx
    assert entity.event_engine == ctx.event_engine
    
    # 2. 测试自动获取 context (使用 with 语句确保 set_context 被调用)
    with SimulationContext() as ctx2:
        entity2 = BaseEntity("TestEntityAuto")
        assert entity2.ctx == ctx2
        assert entity2.event_engine == ctx2.event_engine
    
    print("BaseEntity Context Test Passed!")

if __name__ == "__main__":
    test_attribute_calculator()
    test_base_entity_context()
