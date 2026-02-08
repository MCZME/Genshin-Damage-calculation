import pytest
from core.context import create_context
from core.team import Team
from character.LIYUE.xiangling import XIANG_LING
from core.entities.base_entity import Faction, CombatEntity
from core.action.damage import Damage, DamageType
from core.mechanics.aura import Element

class MockTarget(CombatEntity):
    """用于测试附着的靶子"""
    def __init__(self):
        super().__init__("靶子", Faction.ENEMY)
        self.attribute_panel = {
            '防御力': 500,
            '火元素抗性': 10.0
        }
    
    def handle_damage(self, damage):
        """处理受击，触发附着逻辑"""
        damage.set_target(self)
        self.apply_elemental_aura(damage)

class TestXianglingV2Logic:
    """
    验收测试：验证模块化重构后的香菱在场景引擎中的行为。
    """

    @pytest.fixture
    def setup_xiangling(self):
        ctx = create_context()
        base_data = {"name": "香菱", "element": "火", "base_hp": 10000, "base_atk": 200, "base_def": 500}
        char = XIANG_LING(level=90, skill_params=[1, 1, 1], constellation=3, base_data=base_data)
        team = Team([char])
        
        # 添加一个靶子到场景
        target = MockTarget()
        target.set_position(0.5, 0) # 放在攻击范围内
        ctx.space.register(target)
        
        return ctx, char, target

    def test_constellation_skill_boost(self, setup_xiangling):
        """1. 验证 3 命效果"""
        _, char, _ = setup_xiangling
        burst_skill = char.skills.get("burst")
        assert burst_skill.lv == 4

    def test_elemental_skill_guoba_spawn(self, setup_xiangling):
        """2. 验证 E 技能：在场景中生成锅巴实体"""
        ctx, char, _ = setup_xiangling
        char.elemental_skill()
        for _ in range(40): ctx.advance_frame()
        entities = ctx.space._entities[Faction.PLAYER]
        guoba = next((e for e in entities if e.name == "锅巴"), None)
        assert guoba is not None

    def test_guoba_autonomous_update(self, setup_xiangling):
        """3. 验证实体自治"""
        ctx, char, _ = setup_xiangling
        char.elemental_skill()
        for _ in range(40): ctx.advance_frame()
        guoba = next(e for e in ctx.space._entities[Faction.PLAYER] if e.name == "锅巴")
        initial_frame = guoba.current_frame
        for _ in range(10): ctx.advance_frame()
        assert guoba.current_frame == initial_frame + 10

    def test_pyronado_rotation_follow(self, setup_xiangling):
        """4. 验证 Q 技能：旋火轮跟随角色位移"""
        ctx, char, _ = setup_xiangling
        char.elemental_burst()
        for _ in range(56): ctx.advance_frame()
        pyronado = next(e for e in ctx.space._entities[Faction.PLAYER] if e.name == "旋火轮")
        char.set_position(10.0, 5.0)
        ctx.advance_frame()
        assert pyronado.pos[0] == 10.0
        assert pyronado.pos[1] == 5.0

    def test_icd_sequence_logic(self, setup_xiangling):
        """5. 验证 ICD 序列逻辑 (1,0,0 循环)"""
        ctx, char, target = setup_xiangling
        
        # 模拟 4 次普攻命中 (使用相同的 icd_tag="NormalAttack")
        # 我们直接构造 Damage 对象调用 apply_elemental_aura，跳过动作系统以简化测试
        from core.action.action_data import AttackConfig
        
        # 确保使用 Default 组别
        config = AttackConfig(icd_tag="Default", element_u=1.0)
        dmg = Damage(100, (Element.PYRO, 1.0), DamageType.NORMAL, "TestHit", config=config)
        dmg.set_source(char)
        
        # 第1击：应附着 (Index 0 -> 1)
        res1 = target.apply_elemental_aura(dmg)
        assert len(target.aura.auras) == 1 
        
        # 第2击：不应附着 (Index 1 -> 0)
        res2 = target.apply_elemental_aura(dmg)
        assert len(target.aura.auras) == 1 # 数量不变
        
        # 第3击：不应附着 (Index 2 -> 0)
        res3 = target.apply_elemental_aura(dmg)
        assert len(target.aura.auras) == 1 
        
        # 第4击：应附着 (Index 3%3=0 -> 1)
        # 注意：这里会刷新附着量，或叠加
        res4 = target.apply_elemental_aura(dmg)
        # 由于同元素叠加是取最大值刷新，数量还是 1，但 decay_rate 可能更新
        assert len(target.aura.auras) == 1
        
        # 验证 ICD 状态
        state = target.icd_manager.records.get((id(char), "Default"))
        assert state.hit_count == 4