import pytest
from core.context import create_context
from core.systems.contract.attack import AttackConfig
from core.target import Target
from core.systems.contract.damage import Damage
from core.mechanics.aura import Element
from core.event import GameEvent, EventType
from core.tool import get_current_time
from core.entities.base_entity import Faction

from core.systems.contract.attack import HitboxConfig, AOEShape


class TestCombatSpaceGeometry:
    @pytest.fixture
    def sim_ctx(self):
        return create_context()

    @pytest.fixture
    def attacker(self):
        class MockChar:
            def __init__(self):
                self.name = "Attacker"
                self.faction = Faction.PLAYER
                self.level = 90
                self.pos = [0.0, 0.0, 0.0]
                self.facing = 0.0
                self.attribute_data = {
                    k: 1000.0 for k in ["攻击力", "元素精通", "暴击率", "暴击伤害"]
                }
                self.active_effects = []

        return MockChar()

    def test_circle_edge_hit(self, sim_ctx, attacker):
        """测试圆形擦边"""
        enemy = Target(
            {
                "level": 90,
                "resists": {
                    k: 0.0 for k in ["火", "水", "雷", "草", "冰", "岩", "风", "物理"]
                },
            }
        )
        enemy.hitbox = (0.5, 2.0)
        enemy.set_position(5.4, 0.0)
        sim_ctx.space.register(enemy)

        hitbox = HitboxConfig(shape=AOEShape.SPHERE, radius=5.0)
        dmg_config = AttackConfig(attack_tag="普通攻击", hitbox=hitbox)
        dmg = Damage((Element.PHYSICAL, 1.0), 100.0, "攻击力", dmg_config, "圆擦边")
        sim_ctx.event_engine.publish(
            GameEvent(
                EventType.BEFORE_DAMAGE,
                get_current_time(),
                source=attacker,
                data={"character": attacker, "damage": dmg},
            )
        )

        assert dmg.target == enemy

    def test_box_hit_rotation(self, sim_ctx, attacker):
        """测试矩形判定"""
        attacker.facing = 90.0
        enemy = Target(
            {
                "level": 90,
                "resists": {
                    k: 0.0 for k in ["火", "水", "雷", "草", "冰", "岩", "风", "物理"]
                },
            }
        )
        enemy.hitbox = (0.5, 2.0)
        enemy.set_position(0.0, 4.0)
        sim_ctx.space.register(enemy)

        hitbox = HitboxConfig(shape=AOEShape.BOX, length=5.0, width=2.0)
        dmg_config = AttackConfig(attack_tag="普通攻击", hitbox=hitbox)
        dmg = Damage((Element.PHYSICAL, 1.0), 100.0, "攻击力", dmg_config, "矩形命中")
        sim_ctx.event_engine.publish(
            GameEvent(
                EventType.BEFORE_DAMAGE,
                get_current_time(),
                source=attacker,
                data={"character": attacker, "damage": dmg},
            )
        )

        assert dmg.target == enemy

    def test_offset_hit(self, sim_ctx, attacker):
        """测试位移偏移"""
        attacker.pos = [0.0, 0.0, 0.0]
        attacker.facing = 0.0

        enemy = Target(
            {
                "level": 90,
                "resists": {
                    k: 0.0 for k in ["火", "水", "雷", "草", "冰", "岩", "风", "物理"]
                },
            }
        )
        enemy.set_position(5.0, 0.0)
        sim_ctx.space.register(enemy)

        hitbox = HitboxConfig(shape=AOEShape.SPHERE, radius=1.0, offset=(5.0, 0.0))
        dmg_config = AttackConfig(attack_tag="普通攻击", hitbox=hitbox)
        dmg = Damage((Element.PHYSICAL, 1.0), 100.0, "攻击力", dmg_config, "偏移攻击")

        sim_ctx.event_engine.publish(
            GameEvent(
                EventType.BEFORE_DAMAGE,
                get_current_time(),
                source=attacker,
                data={"character": attacker, "damage": dmg},
            )
        )

        assert dmg.target == enemy
