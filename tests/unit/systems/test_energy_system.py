import pytest
from core.systems.energy_system import EnergySystem
from core.event import GameEvent, EventType
from core.tool import get_current_time
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
        source_entity.elemental_energy = ElementalEnergy(element="火", max_energy=80)
        return team

    def test_fixed_energy_charge(self, energy_sys, source_entity, setup_team):
        """测试固定能量恢复 (is_fixed=True)"""
        source_entity.elemental_energy.current_energy = 10.0

        event_data = {
            "character": source_entity,
            "amount": 5.0,
            "is_fixed": True,
            "is_alone": True,
        }
        event = GameEvent(
            EventType.BEFORE_ENERGY_CHANGE, get_current_time(), data=event_data
        )
        energy_sys.handle_event(event)

        assert source_entity.elemental_energy.current_energy == 15.0

    def test_particle_energy_charge_same_element(
        self, energy_sys, source_entity, setup_team
    ):
        """测试同元素微粒恢复 (is_fixed=False)"""
        source_entity.attribute_data["元素充能效率"] = 200.0
        source_entity.elemental_energy.current_energy = 0.0
        source_entity.on_field = True

        event_data = {
            "character": source_entity,
            "amount": ("火", 3.0),
            "is_fixed": False,
            "is_alone": True,
        }
        event = GameEvent(
            EventType.BEFORE_ENERGY_CHANGE, get_current_time(), data=event_data
        )
        energy_sys.handle_event(event)

        # 3.0微粒 * 3.0(同元素站场) * 200%(效率) = 18.0
        assert source_entity.elemental_energy.current_energy == 18.0

    def test_particle_energy_overflow(self, energy_sys, source_entity, setup_team):
        """测试微粒恢复不会超过能量上限"""
        source_entity.attribute_data["元素充能效率"] = 100.0
        source_entity.elemental_energy.current_energy = 75.0
        source_entity.elemental_energy.max_energy = 80.0
        source_entity.on_field = True

        event_data = {
            "character": source_entity,
            "amount": ("火", 10.0),  # 远超剩余空间
            "is_fixed": False,
            "is_alone": True,
        }
        event = GameEvent(
            EventType.BEFORE_ENERGY_CHANGE, get_current_time(), data=event_data
        )
        energy_sys.handle_event(event)

        # 应该精确达到上限，不会溢出
        assert source_entity.elemental_energy.current_energy == 80.0

    def test_fixed_energy_overflow(self, energy_sys, source_entity, setup_team):
        """测试固定值恢复也不会超过上限"""
        source_entity.elemental_energy.current_energy = 70.0
        source_entity.elemental_energy.max_energy = 80.0

        event_data = {
            "character": source_entity,
            "amount": 20.0,  # 超过剩余空间
            "is_fixed": True,
            "is_alone": True,
        }
        event = GameEvent(
            EventType.BEFORE_ENERGY_CHANGE, get_current_time(), data=event_data
        )
        energy_sys.handle_event(event)

        assert source_entity.elemental_energy.current_energy == 80.0

    def test_off_field_energy_rate(self, energy_sys, source_entity, setup_team):
        """测试后台能量获取系数"""
        source_entity.attribute_data["元素充能效率"] = 100.0
        source_entity.elemental_energy.current_energy = 0.0
        source_entity.on_field = False  # 后台

        event_data = {
            "character": source_entity,
            "amount": ("火", 1.0),  # 同元素微粒
            "is_fixed": False,
            "is_alone": True,
        }
        event = GameEvent(
            EventType.BEFORE_ENERGY_CHANGE, get_current_time(), data=event_data
        )
        energy_sys.handle_event(event)

        # 后台同元素: 1.8 * 100% = 1.8
        assert source_entity.elemental_energy.current_energy == 1.8
