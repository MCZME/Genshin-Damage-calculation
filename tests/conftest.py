import pytest
from typing import Any
from unittest.mock import MagicMock
from core.context import EventEngine
from core.mechanics.aura import AuraManager
from core.mechanics.icd import ICDManager
from core.entities.base_entity import Faction


# ---------------------------------------------------------
# Mock UI Logger for tests (CI 环境无配置文件)
# ---------------------------------------------------------
class MockUILogger:
    """Mock UILogger，用于测试环境"""

    def log_info(self, msg: str) -> None:
        pass

    def log_warning(self, msg: str) -> None:
        pass

    def log_error(self, msg: str) -> None:
        pass

    def log_debug(self, msg: str) -> None:
        pass

    def log_window_open(self, name: str) -> None:
        pass

    def log_button_click(self, name: str) -> None:
        pass


@pytest.fixture(autouse=True)
def mock_ui_logger():
    """自动 mock get_ui_logger 以避免 CI 环境配置缺失问题"""
    import core.logger as logger_module

    original_logger = logger_module._default_ui_logger
    logger_module._default_ui_logger = MockUILogger()

    yield

    logger_module._default_ui_logger = original_logger


class MockAttributeEntity:
    """标准属性 Mock 对象，对齐 V2 架构变量名"""

    def __init__(self):
        self.name = "MockEntity"
        self.faction = Faction.PLAYER
        self.level = 90
        self.facing = 0.0
        self.attribute_data = {
            "攻击力": 1000.0,
            "固定攻击力": 0.0,
            "攻击力%": 0.0,
            "生命值": 10000.0,
            "固定生命值": 0.0,
            "生命值%": 0.0,
            "防御力": 800.0,
            "固定防御力": 0.0,
            "防御力%": 0.0,
            "元素精通": 100.0,
            "暴击率": 50.0,
            "暴击伤害": 100.0,
            "火元素伤害加成": 0.0,
            "水元素伤害加成": 0.0,
            "草元素伤害加成": 0.0,
            "雷元素伤害加成": 0.0,
            "冰元素伤害加成": 0.0,
            "伤害加成": 0.0,
            "元素充能效率": 100.0,
        }
        self.attribute_data = self.attribute_data.copy()
        self.current_resistance = {
            k: 10.0 for k in ["火", "水", "雷", "草", "冰", "岩", "风", "物理"]
        }
        self.aura = AuraManager()
        self.icd_manager = ICDManager(self)
        self.active_effects = []
        self.on_field = True
        self.pos = [0.0, 0.0, 0.0]
        self.hitbox = (0.5, 2.0)

    @property
    def defense(self):
        return self.attribute_data["防御力"]

    def handle_damage(self, damage: Any) -> None:
        """Mock 伤害处理，建立引用并触发附着逻辑"""
        damage.set_target(self)
        self.apply_elemental_aura(damage)

    def apply_elemental_aura(self, damage: Any) -> list:
        # 1. 检查 ICD
        tag = getattr(damage.config, "icd_tag", "Default")
        group = getattr(damage.config, "icd_group", "Default")
        multiplier = self.icd_manager.check_attachment(damage.source, tag, group)
        if multiplier <= 0:
            return []

        # 2. 调用 AuraManager
        results = self.aura.apply_element(
            damage.element[0], damage.element[1] * multiplier
        )

        # 3. 同步结果 (重要：确保结果回到 damage 对象)
        if hasattr(damage, "reaction_results"):
            damage.reaction_results.extend(results)
        return results

    def export_state(self) -> dict:
        """Mock 协议导出"""
        return {
            "name": self.name,
            "level": self.level,
            "faction": self.faction.name,
            "pos": self.pos,
            "attributes": self.attribute_data.copy(),
            "auras": self.aura.export_state(),
        }


@pytest.fixture
def source_entity():
    return MockAttributeEntity()


@pytest.fixture
def target_entity():
    return MockAttributeEntity()


@pytest.fixture
def event_engine():
    return EventEngine()
