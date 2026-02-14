import pytest
from core.context import create_context
from core.systems.contract.attack import AttackConfig
from core.team import Team
from character.character import Character
from core.entities.base_entity import Faction
from core.systems.contract.damage import Damage
from core.mechanics.aura import Element

class MockChar(Character):
    """适配 V2 架构的 Mock 角色"""
    def _setup_character_components(self) -> None:
        # 实现抽象方法
        self.skills = {}
        self.elemental_energy = None

    def _setup_effects(self) -> None:
        # 实现抽象方法
        self.talents = []
        self.constellations = [None] * 6

class TestCharacterEntityization:
    @pytest.fixture
    def setup_team(self):
        ctx = create_context()
        # 使用适配后的 MockChar
        char = MockChar(base_data={"name": "TestChar", "element": "火", "base_hp": 10000.0})
        team = Team([char], context=ctx)
        ctx.space.set_team(team)
        return ctx, char, team

    def test_auto_registration(self, setup_team):
        """验证：角色入队后可通过 CombatSpace 检索到"""
        ctx, char, _ = setup_team
        # 现在角色不在私有的 _entities 列表中，而是通过 Team 管理
        assert char in ctx.space.get_all_entities()
        assert char.name == "TestChar"

    def test_synchronized_update(self, setup_team):
        """验证：场景 advance_frame 能够驱动角色的 current_frame"""
        ctx, char, _ = setup_team
        initial_frame = char.current_frame
        
        ctx.advance_frame()
        assert char.current_frame == initial_frame + 1
        
    def test_character_self_damage_interaction(self, setup_team):
        """验证：角色能够通过 handle_damage 接收并处理伤害逻辑"""
        ctx, char, _ = setup_team
        
        # 修正 Damage 构造函数参数顺序：(element, damage_multiplier, scaling_stat, config, name)
        dmg_config = AttackConfig(attack_tag="元素战技")
        dmg = Damage((Element.PYRO, 1.0), 100, "攻击力", dmg_config, "自伤测试")
        char.handle_damage(dmg)
        
        # 验证是否挂上了火元素
        assert any(a.element == Element.PYRO for a in char.aura.auras)
