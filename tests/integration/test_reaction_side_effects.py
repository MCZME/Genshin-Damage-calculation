import pytest
from core.context import create_context
from core.systems.contract.damage import Damage
from core.mechanics.aura import Element
from core.entities.base_entity import Faction, CombatEntity
from core.tool import get_current_time
from core.event import GameEvent, EventType

class MockEnemy(CombatEntity):
    def __init__(self, name, pos=(0,0,0)):
        super().__init__(name, Faction.ENEMY, pos=pos)
        self.attribute_data = {
            "防御力": 500,
            "物理元素抗性": 10.0,
            "火元素抗性": 10.0,
            "冰元素抗性": 10.0,
            "雷元素抗性": 10.0
        }
    
    def handle_damage(self, damage):
        damage.set_target(self)
        self.apply_elemental_aura(damage)

class TestReactionSideEffects:
    @pytest.fixture
    def sim_ctx(self):
        return create_context()

    def test_superconduct_resistance_reduction(self, sim_ctx):
        """测试超导反应：验证物理减抗副作用"""
        enemy = MockEnemy("受试者")
        sim_ctx.space.register(enemy)
        
        # 1. 挂冰 (1.0U)
        enemy.aura.apply_element(Element.CRYO, 1.0)
        
        # 2. 雷攻击触发超导
        # 注意: 需要 source 具有 level 属性以计算等级系数
        from tests.conftest import MockAttributeEntity
        attacker = MockAttributeEntity()
        attacker.level = 90
        
        dmg = Damage(
            element=(Element.ELECTRO, 1.0),
            damage_multiplier=0,
            name="触发超导"
        )
        dmg.set_source(attacker)
        
        # 触发流程
        sim_ctx.event_engine.publish(GameEvent(
            EventType.BEFORE_DAMAGE, get_current_time(), 
            source=attacker, data={'character': attacker, 'target': enemy, 'damage': dmg}
        ))
        
        # 3. 验证抗性
        # 初始 10.0, 降低 40.0 -> 应为 -30.0
        res = enemy.attribute_data.get("物理元素抗性")
        assert res == -30.0
        
        # 4. 验证效果是否存在
        assert any(eff.name == "超导减抗" for eff in enemy.active_effects)

    def test_swirl_element_spread(self, sim_ctx):
        """测试扩散反应：验证元素空间传播副作用"""
        # 创建两个敌人，一个在中心，一个在 2m 外
        center_enemy = MockEnemy("中心目标", pos=(0, 0, 0))
        nearby_enemy = MockEnemy("邻近目标", pos=(2, 0, 0))
        
        sim_ctx.space.register(center_enemy)
        sim_ctx.space.register(nearby_enemy)
        
        # 1. 中心目标挂火
        center_enemy.aura.apply_element(Element.PYRO, 1.0)
        assert len(nearby_enemy.aura.auras) == 0 # 邻近目标此时无附着
        
        # 2. 风攻击中心目标触发扩散
        attacker = MockEnemy("风角色", pos=(-1, 0, 0)) # 假装是玩家
        attacker.faction = Faction.PLAYER
        attacker.level = 90
        
        dmg = Damage(
            element=(Element.ANEMO, 1.0),
            damage_multiplier=100.0,
            name="风压"
        )
        dmg.set_source(attacker)
        
        # 触发流程
        sim_ctx.event_engine.publish(GameEvent(
            EventType.BEFORE_DAMAGE, get_current_time(), 
            source=attacker, data={'character': attacker, 'target': center_enemy, 'damage': dmg}
        ))
        
        # 3. 验证邻近目标是否被染上火
        assert any(a.element == Element.PYRO for a in nearby_enemy.aura.auras)
