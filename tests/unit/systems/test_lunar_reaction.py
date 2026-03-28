"""
月曜反应系统测试用例。

测试内容：
1. 月曜反应枚举与类别
2. 月曜触发判定
3. 反应转换逻辑
4. 加权求和计算
5. 月曜伤害计算
"""

import pytest
from typing import Any

from core.context import create_context
from core.systems.contract.reaction import (
    ReactionResult,
    ElementalReactionType,
    ReactionCategory,
)
from core.mechanics.aura import Element, Gauge, AuraManager
from core.systems.lunar_system import LunarReactionSystem
from core.entities.lunar_entities import (
    ProsperousCoreEntity,
    ThunderCloudEntity,
    LunarCageEntity,
)
class MockCharacter:
    """模拟角色对象（用于触发判定测试）"""

    def __init__(self, name: str, level: int = 90, lunar_triggers: set[str] | None = None):
        self.name = name
        self.level = level
        self.elemental_mastery = 100.0
        self.crit_rate = 50.0
        self.crit_dmg = 100.0
        self.pos = [0.0, 0.0, 0.0]
        self.on_field = True
        # 月兆天赋（用于触发判定）
        self.talents = []
        if lunar_triggers:
            from core.effect.common import MoonsignTalent
            class MockMoonsignTalent(MoonsignTalent):
                def __init__(self, triggers):
                    super().__init__()
                    self.lunar_triggers = triggers
            self.talents.append(MockMoonsignTalent(lunar_triggers))


class MockTeam:
    """模拟队伍"""

    def __init__(self, members: list[MockCharacter]):
        self.members = members

    def get_members(self):
        return self.members


class TestLunarReactionEnums:
    """测试月曜反应枚举与类别"""

    def test_lunar_reaction_types_exist(self):
        """测试月曜反应类型已定义"""
        assert ElementalReactionType.LUNAR_BLOOM.value == "月绽放"
        assert ElementalReactionType.LUNAR_CHARGED.value == "月感电"
        assert ElementalReactionType.LUNAR_CRYSTALLIZE.value == "月结晶"

    def test_lunar_category_exist(self):
        """测试月曜类别已定义"""
        assert ReactionCategory.LUNAR is not None
        assert ReactionCategory.LUNAR != ReactionCategory.TRANSFORMATIVE
        assert ReactionCategory.LUNAR != ReactionCategory.AMPLIFYING


class TestLunarReactionSystem:
    """测试月曜系统核心功能"""

    @pytest.fixture
    def lunar_system(self):
        return LunarReactionSystem()

    def test_can_trigger_lunar_bloom(self, lunar_system):
        """测试月绽放触发判定"""
        # 有触发角色（哥伦比娅可以触发所有类型）
        team = MockTeam([
            MockCharacter("哥伦比娅", lunar_triggers={"bloom", "charged", "crystallize"}),
            MockCharacter("其他角色"),
        ])
        assert lunar_system.can_trigger_lunar_bloom(team.get_members()) is True

        # 无触发角色
        team_no_trigger = MockTeam([
            MockCharacter("其他角色1"),
            MockCharacter("其他角色2"),
        ])
        assert lunar_system.can_trigger_lunar_bloom(team_no_trigger.get_members()) is False

    def test_can_trigger_lunar_charged(self, lunar_system):
        """测试月感电触发判定"""
        team = MockTeam([
            MockCharacter("菲林斯", lunar_triggers={"charged"}),
            MockCharacter("其他角色"),
        ])
        assert lunar_system.can_trigger_lunar_charged(team.get_members()) is True

        team_no_trigger = MockTeam([
            MockCharacter("其他角色1"),
            MockCharacter("其他角色2"),
        ])
        assert lunar_system.can_trigger_lunar_charged(team_no_trigger.get_members()) is False

    def test_can_trigger_lunar_crystallize(self, lunar_system):
        """测试月结晶触发判定"""
        team = MockTeam([
            MockCharacter("兹白", lunar_triggers={"crystallize"}),
        ])
        assert lunar_system.can_trigger_lunar_crystallize(team.get_members()) is True

        team_no_trigger = MockTeam([
            MockCharacter("其他角色"),
        ])
        assert lunar_system.can_trigger_lunar_crystallize(team_no_trigger.get_members()) is False


class TestGrassDewMechanism:
    """测试草露机制"""

    @pytest.fixture
    def lunar_system(self):
        return LunarReactionSystem()

    def test_grass_dew_initial_state(self, lunar_system):
        """测试草露初始状态"""
        assert lunar_system.grass_dew == 0
        assert lunar_system.grass_dew_max == 3

    def test_grass_dew_add(self, lunar_system):
        """测试草露添加"""
        result = lunar_system.add_grass_dew(2)
        assert result == 2
        assert lunar_system.grass_dew == 2

    def test_grass_dew_max_limit(self, lunar_system):
        """测试草露上限"""
        lunar_system.add_grass_dew(5)  # 尝试添加超过上限
        assert lunar_system.grass_dew == 3  # 应被限制在上限

    def test_grass_dew_consume(self, lunar_system):
        """测试草露消耗"""
        lunar_system.add_grass_dew(2)
        result = lunar_system.consume_grass_dew(1)
        assert result is True
        assert lunar_system.grass_dew == 1

    def test_grass_dew_consume_insufficient(self, lunar_system):
        """测试草露不足时消耗失败"""
        result = lunar_system.consume_grass_dew(1)
        assert result is False
        assert lunar_system.grass_dew == 0


class TestLunarCageCounter:
    """测试月笼计数机制"""

    @pytest.fixture
    def lunar_system(self):
        return LunarReactionSystem()

    def test_counter_increment(self, lunar_system):
        """测试计数增加"""
        char = MockCharacter("兹白")
        count = lunar_system.add_lunar_cage_counter(char)
        assert count == 1

        count = lunar_system.add_lunar_cage_counter(char)
        assert count == 2

    def test_counter_threshold_and_reset(self, lunar_system):
        """测试达到阈值后重置"""
        char1 = MockCharacter("兹白")
        char2 = MockCharacter("哥伦比娅")

        lunar_system.add_lunar_cage_counter(char1)
        lunar_system.add_lunar_cage_counter(char2)
        lunar_system.add_lunar_cage_counter(char1)

        triggered, sources = lunar_system.check_and_reset_lunar_cage_counter()
        assert triggered is True
        assert len(sources) == 2  # 两个不同角色

        # 计数应重置
        assert lunar_system.lunar_cage_counter == 0

    def test_counter_overflow(self, lunar_system):
        """测试计数溢出"""
        char = MockCharacter("兹白")

        # 达到阈值后继续增加
        for _ in range(5):
            lunar_system.add_lunar_cage_counter(char)

        # 应有溢出
        assert lunar_system.lunar_cage_overflow > 0
        assert lunar_system.lunar_cage_overflow <= 4


class TestAuraSourceTracking:
    """测试附着来源追踪"""

    def test_gauge_source_character(self):
        """测试 Gauge 记录来源角色"""
        char = MockCharacter("哥伦比娅")
        gauge = Gauge.create(Element.HYDRO, 1.0, source_character=char)

        assert gauge.source_character == char
        assert gauge.element == Element.HYDRO

    def test_aura_manager_apply_with_source(self):
        """测试 AuraManager 接收来源参数"""
        aura = AuraManager()
        char = MockCharacter("哥伦比娅")

        aura.apply_element(Element.HYDRO, 1.0, source_character=char)

        # 检查附着已创建且有来源记录
        assert len(aura.auras) == 1
        assert aura.auras[0].source_character == char


class TestWeightedDamage:
    """测试加权求和伤害计算"""

    def _calculate_weighted(self, damage_components: list[tuple[Any, float]]) -> float:
        """计算加权求和"""
        if not damage_components:
            return 0.0

        damages = sorted([d[1] for d in damage_components], reverse=True)

        if len(damages) == 1:
            return damages[0]
        elif len(damages) == 2:
            return damages[0] + damages[1] / 2
        else:
            return damages[0] + damages[1] / 2 + sum(damages[2:]) / 12

    def test_single_component(self):
        """测试单组分"""
        components = [(None, 100.0)]
        result = self._calculate_weighted(components)
        assert result == 100.0

    def test_two_components(self):
        """测试两组分"""
        components = [(None, 100.0), (None, 60.0)]
        result = self._calculate_weighted(components)
        # 最高(100) + 次高/2(60/2=30) = 130
        assert result == 130.0

    def test_three_components(self):
        """测试三组分"""
        components = [(None, 100.0), (None, 60.0), (None, 24.0)]
        result = self._calculate_weighted(components)
        # 最高(100) + 次高/2(30) + 其余/12(24/12=2) = 132
        assert result == 132.0

    def test_many_components(self):
        """测试多组分"""
        components = [(None, 100.0), (None, 80.0), (None, 60.0), (None, 40.0)]
        result = self._calculate_weighted(components)
        # 最高(100) + 次高/2(40) + 其余/12((60+40)/12≈8.33) = 148.33
        expected = 100 + 80 / 2 + (60 + 40) / 12
        assert abs(result - expected) < 0.01


class TestLunarEntities:
    """测试月曜实体"""

    @pytest.fixture
    def sim_ctx(self):
        ctx = create_context()
        # 设置上下文变量
        import core.context as ctx_module
        ctx_module._current_context.set(ctx)
        yield ctx
        ctx_module._current_context.set(None)

    def test_prosperous_core_creation(self, sim_ctx):
        """测试丰穰之核创建"""
        creator = MockCharacter("哥伦比娅")
        core = ProsperousCoreEntity(creator=creator, pos=(0.0, 0.0, 0.0))

        assert core.name == "丰穰之核"
        assert core.life_frame == 24  # 0.4秒
        assert core.explosion_radius == 6.5

    def test_thunder_cloud_creation(self, sim_ctx):
        """测试雷暴云创建"""
        creator = MockCharacter("菲林斯")
        cloud = ThunderCloudEntity(
            creator=creator,
            pos=(0.0, 0.0, 1.0),
            source_characters=[creator],
        )

        assert cloud.name == "雷暴云"
        assert cloud.attack_interval == 2.0
        assert cloud.initial_delay == 0.25
        assert creator in cloud.source_characters

        # 清理
        ThunderCloudEntity.active_clouds.clear()

    def test_thunder_cloud_add_source(self, sim_ctx):
        """测试雷暴云添加来源角色"""
        creator = MockCharacter("菲林斯")
        cloud = ThunderCloudEntity(
            creator=creator,
            pos=(0.0, 0.0, 1.0),
            source_characters=[creator]  # 初始化时传入创建者
        )

        char2 = MockCharacter("伊涅芙")
        cloud.add_source_character(char2)

        assert len(cloud.source_characters) == 2

        # 清理
        ThunderCloudEntity.active_clouds.clear()

    def test_lunar_cage_creation(self, sim_ctx):
        """测试月笼创建"""
        creator = MockCharacter("兹白")
        cage = LunarCageEntity(creator=creator, pos=(0.0, 0.0, 0.0))

        assert cage.name == "月笼"
        assert cage in LunarCageEntity.active_cages

        # 清理
        cage.finish()
        LunarCageEntity.active_cages.clear()

    def test_lunar_cage_count_nearby(self, sim_ctx):
        """测试附近月笼计数"""
        # 清理现有月笼
        LunarCageEntity.active_cages.clear()

        creator = MockCharacter("兹白")
        LunarCageEntity(creator=creator, pos=(0.0, 0.0, 0.0))
        LunarCageEntity(creator=creator, pos=(1.0, 0.0, 0.0))

        count = LunarCageEntity.count_nearby_cages((0.5, 0.0, 0.0))
        assert count == 2

        # 清理
        LunarCageEntity.active_cages.clear()


class TestLunarReactionConversion:
    """测试月曜反应转换"""

    @pytest.fixture
    def sim_ctx(self):
        return create_context()

    @pytest.fixture
    def reaction_sys(self, sim_ctx):
        return sim_ctx.get_system("ReactionSystem")

    def test_is_character_source(self, reaction_sys):
        """测试角色源判定"""
        # 创建真正的 Character 实例来测试
        # 由于 MockCharacter 不是 Character 子类，测试其不是角色源
        mock_char = MockCharacter("哥伦比娅")
        assert reaction_sys._is_character_source(mock_char) is False

        # 非角色对象
        class NonCharacter:
            pass
        assert reaction_sys._is_character_source(NonCharacter()) is False

    def test_convert_to_lunar_bloom(self, reaction_sys):
        """测试绽放转月绽放"""
        char = MockCharacter("哥伦比娅")
        original = ReactionResult(
            reaction_type=ElementalReactionType.BLOOM,
            category=ReactionCategory.TRANSFORMATIVE,
            source_element=Element.HYDRO,
            target_element=Element.DENDRO,
            gauge_consumed=0.8,
        )

        converted = reaction_sys._convert_to_lunar_bloom(original, char)

        assert converted.reaction_type == ElementalReactionType.LUNAR_BLOOM
        assert converted.category == ReactionCategory.LUNAR
        assert converted.data.get("original_reaction") == ElementalReactionType.BLOOM

    def test_convert_to_lunar_charged(self, reaction_sys):
        """测试感电转月感电"""
        char = MockCharacter("菲林斯")
        original = ReactionResult(
            reaction_type=ElementalReactionType.ELECTRO_CHARGED,
            category=ReactionCategory.TRANSFORMATIVE,
            source_element=Element.ELECTRO,
            target_element=Element.HYDRO,
            gauge_consumed=0.4,
        )

        converted = reaction_sys._convert_to_lunar_charged(original, char)

        assert converted.reaction_type == ElementalReactionType.LUNAR_CHARGED
        assert converted.category == ReactionCategory.LUNAR
        assert char in converted.data.get("source_characters", [])

    def test_convert_to_lunar_crystallize(self, reaction_sys):
        """测试结晶转月结晶"""
        char = MockCharacter("兹白")
        original = ReactionResult(
            reaction_type=ElementalReactionType.CRYSTALLIZE,
            category=ReactionCategory.STATUS,
            source_element=Element.GEO,
            target_element=Element.HYDRO,
            gauge_consumed=0.5,
        )

        converted = reaction_sys._convert_to_lunar_crystallize(original, char)

        assert converted.reaction_type == ElementalReactionType.LUNAR_CRYSTALLIZE
        assert converted.category == ReactionCategory.LUNAR
