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
        assert lunar_system.grass_dew == 0.0
        assert lunar_system.grass_dew_max == 3
        assert isinstance(lunar_system.grass_dew, float)

    def test_grass_dew_is_float(self, lunar_system):
        """测试草露为浮点类型"""
        lunar_system.add_grass_dew(0.5)
        assert lunar_system.grass_dew == 0.5
        assert isinstance(lunar_system.grass_dew, float)

    def test_grass_dew_add(self, lunar_system):
        """测试草露添加"""
        result = lunar_system.add_grass_dew(2.0)
        assert result == 2.0
        assert lunar_system.grass_dew == 2.0

    def test_grass_dew_max_limit(self, lunar_system):
        """测试草露上限"""
        lunar_system.add_grass_dew(5.0)  # 尝试添加超过上限
        assert lunar_system.grass_dew == 3.0  # 应被限制在上限

    def test_grass_dew_consume(self, lunar_system):
        """测试草露消耗"""
        lunar_system.add_grass_dew(2.0)
        result = lunar_system.consume_grass_dew(1)
        assert result is True
        assert lunar_system.grass_dew == 1.0

    def test_grass_dew_consume_insufficient(self, lunar_system):
        """测试草露不足时消耗失败"""
        result = lunar_system.consume_grass_dew(1)
        assert result is False
        assert lunar_system.grass_dew == 0.0

    def test_grass_dew_consume_preserves_remainder(self, lunar_system):
        """测试消耗后保留小数部分"""
        lunar_system.add_grass_dew(1.7)
        result = lunar_system.consume_grass_dew(1)
        assert result is True
        assert abs(lunar_system.grass_dew - 0.7) < 0.001

    def test_grass_dew_continuous_recovery(self, lunar_system):
        """测试持续恢复"""
        lunar_system.start_grass_dew_recovery()
        assert lunar_system.grass_dew_recovery_active is True
        assert lunar_system.grass_dew_recovery_timer == 2.5

        # 模拟1秒
        lunar_system.update_grass_dew(1.0)
        # 应恢复 0.4 枚（1.0 * 0.4）
        assert abs(lunar_system.grass_dew - 0.4) < 0.001
        assert lunar_system.grass_dew_recovery_timer == 1.5

    def test_grass_dew_recovery_timer_expires(self, lunar_system):
        """测试恢复状态2.5秒后自动结束"""
        lunar_system.start_grass_dew_recovery()

        # 模拟2.5秒
        lunar_system.update_grass_dew(2.5)
        assert lunar_system.grass_dew_recovery_active is False
        assert abs(lunar_system.grass_dew - 1.0) < 0.001

    def test_grass_dew_refresh_duration(self, lunar_system):
        """测试再次触发刷新持续时间"""
        lunar_system.start_grass_dew_recovery()

        # 模拟1秒
        lunar_system.update_grass_dew(1.0)
        assert abs(lunar_system.grass_dew - 0.4) < 0.001
        assert lunar_system.grass_dew_recovery_timer == 1.5

        # 再次触发，刷新持续时间
        lunar_system.refresh_grass_dew_recovery()
        assert lunar_system.grass_dew_recovery_timer == 2.5

        # 再模拟1.5秒
        lunar_system.update_grass_dew(1.5)
        assert abs(lunar_system.grass_dew - 1.0) < 0.001  # 0.4 + 1.5 * 0.4 = 1.0
        assert lunar_system.grass_dew_recovery_timer == 1.0

    def test_grass_dew_recovery_stops_at_max(self, lunar_system):
        """测试达到上限后停止恢复"""
        lunar_system.grass_dew = 2.9  # 接近上限
        lunar_system.start_grass_dew_recovery()

        # 模拟1秒，会超过上限
        lunar_system.update_grass_dew(1.0)
        assert lunar_system.grass_dew == 3.0  # 不超过上限
        assert lunar_system.grass_dew_recovery_active is False

    def test_grass_dew_consume_requires_full_unit(self, lunar_system):
        """测试消耗需要满1枚"""
        lunar_system.add_grass_dew(0.9)
        assert lunar_system.can_consume_grass_dew(1) is False

        lunar_system.add_grass_dew(0.2)  # 现在有 1.1
        assert lunar_system.can_consume_grass_dew(1) is True


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
    def converter(self):
        from core.systems.reaction.converter import LunarConverter
        return LunarConverter()

    def test_is_character_source(self, converter):
        """测试角色源判定"""
        # 创建真正的 Character 实例来测试
        # 由于 MockCharacter 不是 Character 子类，测试其不是角色源
        mock_char = MockCharacter("哥伦比娅")
        assert converter._is_character_source(mock_char) is False

        # 非角色对象
        class NonCharacter:
            pass
        assert converter._is_character_source(NonCharacter()) is False

    def test_convert_to_lunar_bloom(self, converter):
        """测试绽放转月绽放"""
        char = MockCharacter("哥伦比娅")
        original = ReactionResult(
            reaction_type=ElementalReactionType.BLOOM,
            category=ReactionCategory.TRANSFORMATIVE,
            source_element=Element.HYDRO,
            target_element=Element.DENDRO,
            gauge_consumed=0.8,
        )

        converted = converter._convert_to_lunar_bloom(original, char)

        assert converted.reaction_type == ElementalReactionType.LUNAR_BLOOM
        assert converted.category == ReactionCategory.LUNAR
        assert converted.data.get("original_reaction") == ElementalReactionType.BLOOM

    def test_convert_to_lunar_charged(self, converter):
        """测试感电转月感电"""
        char = MockCharacter("菲林斯")
        original = ReactionResult(
            reaction_type=ElementalReactionType.ELECTRO_CHARGED,
            category=ReactionCategory.TRANSFORMATIVE,
            source_element=Element.ELECTRO,
            target_element=Element.HYDRO,
            gauge_consumed=0.4,
        )

        converted = converter._convert_to_lunar_charged(original, char)

        assert converted.reaction_type == ElementalReactionType.LUNAR_CHARGED
        assert converted.category == ReactionCategory.LUNAR
        assert char in converted.data.get("source_characters", [])

    def test_convert_to_lunar_crystallize(self, converter):
        """测试结晶转月结晶"""
        char = MockCharacter("兹白")
        original = ReactionResult(
            reaction_type=ElementalReactionType.CRYSTALLIZE,
            category=ReactionCategory.STATUS,
            source_element=Element.GEO,
            target_element=Element.HYDRO,
            gauge_consumed=0.5,
        )

        converted = converter._convert_to_lunar_crystallize(original, char)

        assert converted.reaction_type == ElementalReactionType.LUNAR_CRYSTALLIZE
        assert converted.category == ReactionCategory.LUNAR


class TestCrystallizeCooldown:
    """测试结晶反应冷却机制"""

    @pytest.fixture
    def sim_ctx(self):
        """创建测试上下文并设置帧数。"""
        ctx = create_context()
        # 设置上下文变量
        import core.context as ctx_module
        ctx_module._current_context.set(ctx)
        yield ctx
        ctx_module._current_context.set(None)

    def test_crystallize_cooldown_initial_state(self):
        """测试结晶冷却初始状态"""
        aura = AuraManager()
        assert hasattr(aura, '_crystallize_cooldowns')
        assert aura._crystallize_cooldowns == {}

    def test_first_crystallize_not_on_cooldown(self, sim_ctx):
        """测试首次结晶不在冷却中"""
        sim_ctx.current_frame = 0

        aura = AuraManager()
        # 先挂水
        aura.apply_element(Element.HYDRO, 1.0)

        # 首次结晶
        results = aura.apply_element(Element.GEO, 1.0)

        # 应生成结晶结果，且不在冷却中
        assert len(results) == 1
        assert results[0].reaction_type == ElementalReactionType.CRYSTALLIZE
        assert results[0].is_cooldown_skipped is False

    def test_crystallize_cooldown_blocks_second(self, sim_ctx):
        """测试冷却中的结晶被跳过"""
        aura = AuraManager()
        # 先挂水
        aura.apply_element(Element.HYDRO, 2.0)  # 挂足量水

        # 首次结晶
        sim_ctx.current_frame = 0
        results1 = aura.apply_element(Element.GEO, 1.0)
        assert results1[0].is_cooldown_skipped is False

        # 0.5秒后再次尝试结晶（在1秒冷却内）
        sim_ctx.current_frame = 30  # 0.5秒 = 30帧
        # 重新挂水
        aura.apply_element(Element.HYDRO, 1.0)
        results2 = aura.apply_element(Element.GEO, 1.0)

        # 应被冷却跳过
        assert len(results2) == 1
        assert results2[0].is_cooldown_skipped is True

    def test_crystallize_cooldown_expires_after_1_second(self, sim_ctx):
        """测试1秒后冷却结束"""
        aura = AuraManager()
        # 先挂水
        aura.apply_element(Element.HYDRO, 2.0)

        # 首次结晶
        sim_ctx.current_frame = 0
        results1 = aura.apply_element(Element.GEO, 1.0)
        assert results1[0].is_cooldown_skipped is False

        # 1秒后再次结晶（冷却结束）
        sim_ctx.current_frame = 61  # 超过60帧
        # 重新挂水
        aura.apply_element(Element.HYDRO, 1.0)
        results2 = aura.apply_element(Element.GEO, 1.0)

        # 应正常触发
        assert results2[0].is_cooldown_skipped is False

    def test_different_elements_have_separate_cooldowns(self, sim_ctx):
        """测试不同元素结晶独立冷却"""
        aura = AuraManager()
        # 挂水和火
        aura.apply_element(Element.HYDRO, 1.0)
        aura.apply_element(Element.PYRO, 1.0)

        # 水结晶
        sim_ctx.current_frame = 0
        results1 = aura.apply_element(Element.GEO, 1.0)
        assert results1[0].target_element == Element.HYDRO
        assert results1[0].is_cooldown_skipped is False

        # 0.5秒后再次尝试水结晶
        sim_ctx.current_frame = 30  # 0.5秒后
        # 重新挂水
        aura.apply_element(Element.HYDRO, 1.0)
        results2 = aura.apply_element(Element.GEO, 1.0)

        # 水结晶应在冷却中
        assert results2[0].is_cooldown_skipped is True

    def test_lunar_crystallize_ignores_cooldown(self, sim_ctx):
        """测试月结晶无视冷却"""
        # 创建带月结晶触发能力的模拟角色
        class MockCharWithLunar:
            def __init__(self):
                self.name = "哥伦比娅"
                self.pos = [0.0, 0.0, 0.0]
                self.talents = []
                from core.effect.common import MoonsignTalent
                class MockMoonsign(MoonsignTalent):
                    def __init__(self):
                        super().__init__()
                        self.lunar_triggers = {"crystallize"}
                self.talents.append(MockMoonsign())

        # 测试 LunarConverter 的转换逻辑
        # 模拟冷却中的水结晶结果
        cooled_result = ReactionResult(
            reaction_type=ElementalReactionType.CRYSTALLIZE,
            category=ReactionCategory.STATUS,
            source_element=Element.GEO,
            target_element=Element.HYDRO,
            gauge_consumed=0.5,
            is_cooldown_skipped=True,  # 在冷却中
        )

        # 验证转换后冷却标记被清除
        from core.systems.reaction.converter import LunarConverter
        converter = LunarConverter()
        char = MockCharWithLunar()

        # 直接测试转换方法
        converted = converter._convert_to_lunar_crystallize(cooled_result, char)
        assert converted.reaction_type == ElementalReactionType.LUNAR_CRYSTALLIZE
        assert converted.is_cooldown_skipped is False  # 月结晶无视冷却


class TestLunarDamagePipeline:
    """测试 LunarDamagePipeline 月曜伤害计算流水线"""

    @pytest.fixture
    def sim_ctx(self):
        ctx = create_context()
        import core.context as ctx_module
        ctx_module._current_context.set(ctx)
        yield ctx
        ctx_module._current_context.set(None)

    def test_lunar_pipeline_basic_calculation(self, sim_ctx):
        """测试月曜伤害基本计算"""
        from core.systems.damage import LunarDamagePipeline, DamageContext
        from core.systems.contract.damage import Damage
        from core.systems.contract.attack import AttackConfig
        from core.context import EventEngine

        # 创建模拟目标
        class MockTarget:
            def __init__(self):
                self.pos = [0.0, 0.0, 0.0]
                self.雷元素抗性 = 10  # 10% 雷抗
                self.attribute_data = {"雷元素抗性": 10.0}

            def handle_damage(self, damage):
                """处理伤害（空实现）"""
                pass

        # 创建模拟源
        class MockSource:
            def __init__(self):
                self.level = 90
                self.elemental_mastery = 100
                self.pos = [0.0, 0.0, 0.0]
                self.attribute_data = {"元素精通": 100.0}

        # 创建 Damage 对象
        dmg = Damage(
            element=(Element.ELECTRO, 0.0),
            config=AttackConfig(attack_tag="月感电伤害"),
            name="月感电",
        )
        # 通过 data 传递参数
        dmg.add_data("等级系数", 1446.9)  # 90级基数
        dmg.add_data("反应倍率", 1.8)

        source = MockSource()
        target = MockTarget()
        dmg.set_source(source)
        dmg.set_target(target)

        # 创建 context
        ctx = DamageContext(dmg, source, target)

        # 创建 pipeline 并运行
        engine = EventEngine()
        pipeline = LunarDamagePipeline(engine)
        pipeline.run(ctx)

        # 验证伤害计算结果
        # 基础伤害 = 等级系数 × 反应倍率 × (1 + 精通系数)
        # 精通系数 = 6 × 100 / (100 + 2000) ≈ 0.286
        # 反应提升 = 1 + 0.286 = 1.286
        # 核心基础伤害 = 1446.9 × 1.8 × 1.286 ≈ 3348.7
        assert ctx.final_result > 0
        assert dmg.damage == ctx.final_result

    def test_lunar_pipeline_respects_weighted_damage_formula(self, sim_ctx):
        """测试加权求和公式正确性"""
        from core.systems.damage.lunar_pipeline import LunarDamagePipeline

        # 创建模拟数据
        class MockChar:
            def __init__(self, name):
                self.name = name

        pipeline = LunarDamagePipeline(engine=None)

        # 测试三组分加权求和
        components = [
            (MockChar("A"), 1000.0),  # 最高
            (MockChar("B"), 600.0),   # 次高
            (MockChar("C"), 240.0),   # 其余
        ]

        result = pipeline._calculate_weighted_damage(components)
        # 公式：最高(1000) + 次高/2(300) + 其余/12(20) = 1320
        expected = 1000 + 600 / 2 + 240 / 12
        assert abs(result - expected) < 0.01

    def test_lunar_pipeline_no_defense_zone(self, sim_ctx):
        """测试月曜伤害无视防御"""
        from core.systems.damage import LunarDamagePipeline, DamageContext
        from core.systems.contract.damage import Damage
        from core.systems.contract.attack import AttackConfig
        from core.context import EventEngine

        class MockTarget:
            def __init__(self):
                self.pos = [0.0, 0.0, 0.0]
                self.雷元素抗性 = 0
                self.防御力 = 10000  # 高防御
                self.attribute_data = {"雷元素抗性": 0.0}

            def handle_damage(self, damage):
                """处理伤害（空实现）"""
                pass

        class MockSource:
            def __init__(self):
                self.level = 90
                self.elemental_mastery = 0
                self.pos = [0.0, 0.0, 0.0]
                self.attribute_data = {"元素精通": 0.0}

        dmg = Damage(
            element=(Element.ELECTRO, 0.0),
            config=AttackConfig(attack_tag="月感电伤害"),
            name="月感电",
        )
        dmg.add_data("等级系数", 1446.9)
        dmg.add_data("反应倍率", 1.8)

        source = MockSource()
        target = MockTarget()
        dmg.set_source(source)
        dmg.set_target(target)

        ctx = DamageContext(dmg, source, target)

        engine = EventEngine()
        pipeline = LunarDamagePipeline(engine)
        pipeline.run(ctx)

        # 验证：月曜伤害无视防御，防御区系数应该趋近于 1
        # 由于公式中没有防御区，最终结果不应受目标防御力影响
        # 基础伤害 = 1446.9 × 1.8 × 1 = 2604.42
        expected_base = 1446.9 * 1.8  # 无精通加成
        assert abs(ctx.final_result - expected_base) < 10  # 允许抗性等影响

    def test_lunar_pipeline_with_em_bonus(self, sim_ctx):
        """测试元素精通加成"""
        from core.systems.damage import LunarDamagePipeline, DamageContext
        from core.systems.contract.damage import Damage
        from core.systems.contract.attack import AttackConfig
        from core.context import EventEngine
        from unittest.mock import patch

        class MockTarget:
            def __init__(self):
                self.pos = [0.0, 0.0, 0.0]
                self.雷元素抗性 = 0
                self.attribute_data = {"雷元素抗性": 0.0}

            def handle_damage(self, damage):
                """处理伤害（空实现）"""
                pass

        class MockSourceWithEM:
            def __init__(self):
                self.level = 90
                self.elemental_mastery = 200  # 200 精通
                self.pos = [0.0, 0.0, 0.0]
                self.attribute_data = {"元素精通": 200.0}

        dmg = Damage(
            element=(Element.ELECTRO, 0.0),
            config=AttackConfig(attack_tag="月感电伤害"),
            name="月感电",
        )
        dmg.add_data("等级系数", 1446.9)
        dmg.add_data("反应倍率", 1.8)

        source = MockSourceWithEM()
        target = MockTarget()
        dmg.set_source(source)
        dmg.set_target(target)

        ctx = DamageContext(dmg, source, target)

        engine = EventEngine()
        pipeline = LunarDamagePipeline(engine)

        # Mock 掉暴击随机数，确保不暴击
        with patch('random.uniform', return_value=100):  # 100 > 50% 暴击率，不会暴击
            pipeline.run(ctx)

        # 精通系数 = 6 × 200 / (200 + 2000) ≈ 0.545
        # 反应提升 = 1 + 0.545 = 1.545
        # 基础伤害 = 1446.9 × 1.8 × 1.545 ≈ 4023.5
        expected = 1446.9 * 1.8 * (1 + 6 * 200 / (200 + 2000))
        assert abs(ctx.final_result - expected) < 10


