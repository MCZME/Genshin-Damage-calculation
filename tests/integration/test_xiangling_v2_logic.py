import pytest
from core.context import create_context
from core.team import Team
from character.LIYUE.xiangling import XIANG_LING
from core.entities.base_entity import Faction
from core.action.damage import Damage, DamageType
from core.event import GameEvent, EventType
from core.tool import GetCurrentTime

class TestXianglingV2Logic:
    """
    验收测试：验证模块化重构后的香菱在场景引擎中的行为。
    """

    @pytest.fixture
    def setup_xiangling(self):
        """初始化一个 90 级 3 命香菱"""
        ctx = create_context()
        # 初始化基础数据
        base_data = {
            "name": "香菱",
            "element": "火",
            "base_hp": 10875.0,
            "base_atk": 225.0,
            "base_def": 669.0
        }
        # 创建角色 (ID=11, 90级, 技能1/1/1, 3命)
        char = XIANG_LING(level=90, skill_params=[1, 1, 1], constellation=3, base_data=base_data)
        team = Team([char]) # 这一步会自动将香菱 register 到 CombatSpace
        return ctx, char, team

    def test_constellation_skill_boost(self, setup_xiangling):
        """1. 验证 3 命效果：大招等级自动提升 3 级"""
        _, char, _ = setup_xiangling
        
        # 初始 skill_params 是 1，3命提升后应该是 4
        burst_skill = char.skills.get("burst")
        assert burst_skill is not None
        assert burst_skill.lv == 4

    def test_elemental_skill_guoba_spawn(self, setup_xiangling):
        """2. 验证 E 技能：在场景中生成锅巴实体"""
        ctx, char, _ = setup_xiangling
        
        # 发起 E 技能请求 (ASM 驱动)
        char.elemental_skill()
        
        # 模拟推进时间到召唤帧 (40帧)
        for _ in range(40):
            ctx.advance_frame()
            
        # 验证 CombatSpace 中是否出现了名为“锅巴”的实体
        entities = ctx.space._entities[Faction.PLAYER]
        guoba = next((e for e in entities if e.name == "锅巴"), None)
        
        assert guoba is not None
        assert guoba.is_active is True
        # 验证初始位置继承自施法者
        assert guoba.pos[0] == char.pos[0]

    def test_guoba_autonomous_update(self, setup_xiangling):
        """3. 验证实体自治：锅巴由场景自动驱动更新"""
        ctx, char, _ = setup_xiangling
        
        char.elemental_skill()
        for _ in range(40): ctx.advance_frame()
        
        guoba = next(e for e in ctx.space._entities[Faction.PLAYER] if e.name == "锅巴")
        initial_frame = guoba.current_frame
        
        # 再次推进 10 帧
        for _ in range(10):
            ctx.advance_frame()
            
        # 验证锅巴的帧数随场景步进，无需外部显式调用
        assert guoba.current_frame == initial_frame + 10

    def test_pyronado_rotation_follow(self, setup_xiangling):
        """4. 验证 Q 技能：旋火轮跟随角色位移"""
        ctx, char, _ = setup_xiangling
        
        # 发起 Q 技能
        char.elemental_burst()
        
        # 推进到召唤帧 (56帧)
        for _ in range(56): ctx.advance_frame()
        
        pyronado = next(e for e in ctx.space._entities[Faction.PLAYER] if e.name == "旋火轮")
        
        # 修改角色位置
        char.set_position(10.0, 5.0)
        
        # 推进 1 帧让场景驱动更新
        ctx.advance_frame()
        
        # 验证旋火轮位置同步更新
        assert pyronado.pos[0] == 10.0
        assert pyronado.pos[1] == 5.0
