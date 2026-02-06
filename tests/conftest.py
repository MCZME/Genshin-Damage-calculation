import pytest
from core.context import EventEngine
from core.config import Config
from core.action.damage import Damage, DamageType
from core.systems.damage_system import DamageSystem, DamageContext, DamagePipeline

# -----------------------------------------------------------------------------
# 基础 Mock 对象
# -----------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def init_config():
    """初始化全局配置单例 (自动运行)"""
    # 尝试加载真实配置，如果不存在则注入 Mock 基础结构
    try:
        Config()
    except Exception:
        Config.config = {
            'emulation': {
                'open_critical': True
            }
        }

class MockAttributeEntity:
    """模拟拥有属性面板的实体 (角色/怪物)"""
    def __init__(self, name="TestEntity", level=90):
        self.name = name
        self.level = level
        self.attributePanel = {
            '攻击力': 1000.0,
            '固定攻击力': 0.0,
            '攻击力%': 0.0,
            '生命值': 10000.0,
            '固定生命值': 0.0,
            '生命值%': 0.0,
            '防御力': 500.0,
            '固定防御力': 0.0,
            '防御力%': 0.0,
            '元素精通': 0.0,
            '暴击率': 5.0,
            '暴击伤害': 50.0,
            '伤害加成': 0.0,
            # 常见元素伤害加成
            '火元素伤害加成': 0.0,
            '水元素伤害加成': 0.0,
            '物理伤害加成': 0.0
        }
        self.active_effects = []
        self.defense = 500.0
        self.current_resistance = {}

    def apply_elemental_aura(self, damage):
        # Mock 反应接口
        return None

# -----------------------------------------------------------------------------
# Pytest Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def event_engine():
    """提供一个干净的事件引擎"""
    return EventEngine()

@pytest.fixture
def damage_system(event_engine):
    """提供已初始化的伤害系统"""
    sys = DamageSystem()
    # 模拟 Context 初始化
    class MockContext:
        pass
    ctx = MockContext()
    ctx.event_engine = event_engine
    ctx.team = None
    
    sys.initialize(ctx)
    return sys

@pytest.fixture
def source_entity():
    """标准测试攻击者 (Lv90, 1000 ATK)"""
    return MockAttributeEntity("Attacker", level=90)

@pytest.fixture
def target_entity():
    """标准测试受击者 (Lv90, 500 DEF, 10% Res)"""
    t = MockAttributeEntity("Target", level=90)
    t.current_resistance = {'通用': 10.0, '火': 10.0, '物理': 10.0}
    return t

@pytest.fixture
def create_damage_context(event_engine):
    """工厂 fixture: 快速创建 DamageContext"""
    def _create(source, target, element='火', value=100.0, damage_type=DamageType.NORMAL):
        dmg = Damage(value, (element, 1), damage_type, "TestDamage")
        return DamageContext(dmg, source, target)
    return _create
