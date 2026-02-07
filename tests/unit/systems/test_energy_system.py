import pytest
from core.systems.energy_system import EnergySystem
from core.event import EventType, GameEvent
from core.tool import GetCurrentTime

class TestEnergySystemUnit:
    """EnergySystem 逻辑单元测试"""

    @pytest.fixture
    def energy_sys(self, event_engine):
        """提供初始化好的能量系统"""
        sys = EnergySystem()
        class MockContext:
            def __init__(self, engine):
                self.team = None
                self.event_engine = engine
        ctx = MockContext(event_engine)
        sys.initialize(ctx)
        return sys

    @pytest.fixture
    def setup_team(self, energy_sys, source_entity):
        """辅助 fixture: 设置单人队伍"""
        class MockTeam:
            def __init__(self, members):
                self.team = members
        energy_sys.context.team = MockTeam([source_entity])
        return energy_sys.context.team

    def test_fixed_energy_charge(self, energy_sys, source_entity, setup_team):
        """测试固定能量恢复 (is_fixed=True)"""
        source_entity.elemental_energy.current_energy = 10.0
        
        event_data = {
            'character': source_entity,
            'amount': ('无', 5.0),
            'is_fixed': True,
            'is_alone': True
        }
        event = GameEvent(EventType.BEFORE_ENERGY_CHANGE, GetCurrentTime(), data=event_data)
        
        energy_sys.handle_event(event)
        
        assert source_entity.elemental_energy.current_energy == 15.0

    def test_particle_energy_charge_same_element(self, energy_sys, source_entity, setup_team):
        """测试同元素微粒恢复 (is_fixed=False)"""
        source_entity.attributePanel['元素充能效率'] = 200.0
        source_entity.elemental_energy.current_energy = 0.0
        source_entity.on_field = True
        
        event_data = {
            'character': source_entity,
            'amount': ('火', 3.0),
            'is_fixed': False,
            'is_alone': True
        }
        event = GameEvent(EventType.BEFORE_ENERGY_CHANGE, GetCurrentTime(), data=event_data)
        
        energy_sys.handle_event(event)
        
        # 3.0 * 1.0 * 1.5 * 2.0 = 9.0
        assert source_entity.elemental_energy.current_energy == 9.0

    def test_off_field_energy_decay(self, energy_sys, source_entity):
        """测试后台角色能量获取衰减"""
        source_entity.on_field = False
        source_entity.attributePanel['元素充能效率'] = 100.0
        source_entity.elemental_energy.current_energy = 0.0
        
        char2 = MockEntityStub()
        char3 = MockEntityStub()
        char4 = MockEntityStub()
        
        class MockTeam:
            def __init__(self, members):
                self.team = members
        # 设置 4 人队伍
        energy_sys.context.team = MockTeam([source_entity, char2, char3, char4])
        
        event_data = {
            'character': source_entity,
            'amount': ('火', 3.0),
            'is_fixed': False,
            'is_alone': True
        }
        event = GameEvent(EventType.BEFORE_ENERGY_CHANGE, GetCurrentTime(), data=event_data)
        
        energy_sys.handle_event(event)
        
        # 3.0 * 0.6 * 1.5 * 1.0 = 2.7
        assert source_entity.elemental_energy.current_energy == pytest.approx(2.7)

class MockEntityStub:
    def __init__(self):
        self.name = "Stub"