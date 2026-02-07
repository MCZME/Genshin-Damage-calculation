import pytest
from core.context import create_context
from core.team import Team
from character.character import Character
from core.entities.base_entity import Faction
from core.action.damage import Damage, DamageType
from core.mechanics.aura import Element
from core.event import GameEvent, EventType
from core.tool import GetCurrentTime

class TestCharacterEntityization:
    """
    集成测试：验证角色作为 CombatEntity 的注册、驱动与交互。
    """

    @pytest.fixture
    def setup_team(self):
        """构造一个包含 Mock 角色的队伍"""
        ctx = create_context()
        
        class MockChar(Character):
            def _init_character(self):
                self.name = "TestChar"
            def apply_talents(self): pass
            
        char = MockChar(base_data={"name": "TestChar", "element": "火", "base_hp": 10000.0})
        team = Team([char])
        return ctx, char, team

    def test_auto_registration(self, setup_team):
        """1. 验证角色在 Team 初始化后自动进入 CombatSpace"""
        ctx, char, _ = setup_team
        
        # 检查 Faction.PLAYER 阵营中是否有该角色
        player_entities = ctx.space._entities[Faction.PLAYER]
        assert char in player_entities
        assert char.faction == Faction.PLAYER

    def test_synchronized_update(self, setup_team):
        """2. 验证角色的 update 由 CombatSpace 统一驱动"""
        ctx, char, _ = setup_team
        
        # 初始帧
        assert char.current_frame == 0
        
        # 推进 10 帧
        for _ in range(10):
            ctx.advance_frame()
            
        # 验证角色帧数同步增长
        assert char.current_frame == 10

    def test_character_self_damage_interaction(self, setup_team):
        """3. 验证角色能接收并处理伤害广播 (自伤模拟)"""
        ctx, char, _ = setup_team
        
        # 让角色站在原点 (0,0)
        char.set_position(0.0, 0.0)
        
        # 发起一次针对玩家阵营的 10.0 半径圆形广播 (模拟草原核爆炸)
        dmg = Damage(
            damage_multiplier=100.0,
            element=(Element.PYRO, 1.0),
            damage_type=DamageType.REACTION,
            name="环境火伤",
            target_faction=Faction.PLAYER, # 必须指定目标阵营为 PLAYER
            radius=10.0
        )
        
        # 此时广播逻辑在 DamagePipeline 内部
        # 我们模拟 DamageSystem 的行为，直接调用 space.broadcast_damage
        ctx.space.broadcast_damage(char, dmg)
        
        # 验证角色是否被标记为目标
        assert dmg.target == char
        # 验证角色身上产生了火附着 (证明 handle_damage 被调用)
        assert any(a.element == Element.PYRO for a in char.aura.auras)
