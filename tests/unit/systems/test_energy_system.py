import pytest
from core.systems.energy_system import EnergySystem
from core.event import GameEvent, EventType
from core.tool import GetCurrentTime
from core.mechanics.energy import ElementalEnergy

class TestEnergySystemUnit:
    @pytest.fixture
    def energy_sys(self, event_engine):
        sys = EnergySystem()
        class MockContext:
            def __init__(self, engine):
                self.event_engine = engine
                self.team = None
        sys.initialize(MockContext(event_engine))
        return sys

    @pytest.fixture
    def setup_team(self, energy_sys, source_entity):
        class MockTeam:
            def __init__(self, members):
                self.team = members
        team = MockTeam([source_entity])
        energy_sys.context.team = team
        # 补全 Mock 实体的组件
        source_entity.elemental_energy = ElementalEnergy(source_entity, ('火', 80))
        return team

    def test_fixed_energy_charge(self, energy_sys, source_entity, setup_team):
        """测试固定能量恢复 (is_fixed=True)"""
        source_entity.elemental_energy.current_energy = 10.0
        
        event_data = {
            'character': source_entity,
            'amount': 5.0,
            'is_fixed': True,
            'is_alone': True
        }
        event = GameEvent(EventType.BEFORE_ENERGY_CHANGE, GetCurrentTime(), data=event_data)
        energy_sys.handle_event(event)

        assert source_entity.elemental_energy.current_energy == 15.0

    def test_particle_energy_charge_same_element(self, energy_sys, source_entity, setup_team):
        """测试同元素微粒恢复 (is_fixed=False)"""
        source_entity.attribute_panel['元素充能效率'] = 200.0
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

        # 3.0微粒 * 3.0(同元素站场) * 200%(效率) = 18.0
        assert source_entity.elemental_energy.current_energy == 18.0