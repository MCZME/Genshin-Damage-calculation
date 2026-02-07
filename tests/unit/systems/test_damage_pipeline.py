import pytest
from core.systems.damage_system import DamagePipeline
from core.action.damage import DamageType
from core.config import Config
from core.event import EventType, GameEvent, EventHandler
from core.effect.elemental import ElementalInfusionEffect

class TestDamagePipelineUnit:
    """DamagePipeline 核心计算逻辑单元测试"""

    def test_snapshot_attributes(self, event_engine, source_entity, target_entity, create_damage_context):
        """测试属性快照功能"""
        pipeline = DamagePipeline(event_engine)
        ctx = create_damage_context(source_entity, target_entity)
        
        source_entity.attributePanel['攻击力'] = 2500
        source_entity.attributePanel['暴击率'] = 88.8
        
        pipeline._snapshot(ctx)
        
        assert ctx.stats['攻击力'] == 2500
        assert ctx.stats['暴击率'] == 88.8
        assert ctx.stats['伤害加成'] == 0.0

    @pytest.mark.parametrize("defense, attacker_lv, expected_mult", [
        (500, 90, 0.65517),  # 950/1450 ≈ 0.65517
        (950, 90, 0.5),      # 950/1900 = 0.5
        (0, 90, 1.0),        # 950/950 = 1.0
    ])
    def test_defense_calculation(self, event_engine, source_entity, target_entity, create_damage_context, defense, attacker_lv, expected_mult):
        """参数化测试防御区计算"""
        pipeline = DamagePipeline(event_engine)
        ctx = create_damage_context(source_entity, target_entity)
        
        target_entity.defense = defense
        source_entity.level = attacker_lv
        
        pipeline._calculate_def_res(ctx)
        
        assert ctx.stats['防御区系数'] == pytest.approx(expected_mult, 0.0001)

    def test_infusion_priority(self, event_engine, source_entity, target_entity, create_damage_context):
        """测试元素附魔优先级: 水 > 火 > 冰"""
        pipeline = DamagePipeline(event_engine)
        ctx = create_damage_context(source_entity, target_entity, element='物理')
        
        # 实例化参数: (owner, name, element_type, duration)
        pyro_infusion = ElementalInfusionEffect(source_entity, "火附魔", '火', 10*60)
        hydro_infusion = ElementalInfusionEffect(source_entity, "水附魔", '水', 10*60)
        source_entity.active_effects = [pyro_infusion, hydro_infusion]
        
        pipeline._handle_infusion(ctx)
        
        # 优先级 水 > 火，结果应为 水
        assert ctx.damage.element[0] == '水'

    def test_event_driven_modifier(self, event_engine, source_entity, target_entity, create_damage_context):
        """测试通过事件修改计算上下文 (模拟圣遗物/Buff)"""
        pipeline = DamagePipeline(event_engine)
        ctx = create_damage_context(source_entity, target_entity)
        
        # 创建实现了 handle_event 接口的适配器
        class MockModifierHandler(EventHandler):
            def handle_event(self, event: GameEvent):
                damage_ctx = event.data['damage_context']
                damage_ctx.add_modifier("伤害加成", 35.0)
                damage_ctx.add_modifier("攻击力", 200.0)

        handler = MockModifierHandler()
        event_engine.subscribe(EventType.BEFORE_CALCULATE, handler)
        
        # 运行流水线
        pipeline._snapshot(ctx) # 基础 1000 ATK
        pipeline._notify_modifiers(ctx) # 触发事件 +200 ATK, +35% Bonus
        
        assert ctx.stats['伤害加成'] == 35.0
        assert ctx.stats['攻击力'] == 1200.0

    def test_transformative_reaction_logic(self, event_engine, source_entity, target_entity, create_damage_context):
        """测试剧变反应逻辑 (不受倍率和攻击力影响)"""
        pipeline = DamagePipeline(event_engine)
        
        # 创建剧变伤害对象 (如超载)
        ctx = create_damage_context(source_entity, target_entity, damage_type=DamageType.REACTION)
        ctx.damage.set_damage_data("等级系数", 1200)
        ctx.damage.set_damage_data("反应系数", 2.0)
        
        source_entity.attributePanel['元素精通'] = 1400
        target_entity.current_resistance['火'] = 10.0
        
        pipeline.run(ctx)
        
        # 剧变公式: 等级系数 * 反应系数 * (1 + 精通提升 + 反应加成) * 抗性系数
        expected_em_bonus = (16 * 1400) / (1400 + 2000)
        assert ctx.final_result == pytest.approx(1200 * 2.0 * (1 + expected_em_bonus) * 0.9, 0.01)

    def test_full_calculation_flow(self, event_engine, source_entity, target_entity, create_damage_context):
        """测试完整计算流程 (Base * Bonus * Def * Res)"""
        pipeline = DamagePipeline(event_engine)
        ctx = create_damage_context(source_entity, target_entity, value=100.0)
        
        source_entity.attributePanel['攻击力'] = 1000
        source_entity.attributePanel['伤害加成'] = 50.0
        target_entity.defense = 950
        target_entity.current_resistance['火'] = 0.0
        
        Config.set('emulation.open_critical', False)
        
        pipeline.run(ctx)
        
        # Expect: 1000 * 1.5 * 0.5 * 1.0 = 750
        assert ctx.final_result == pytest.approx(750.0, 0.001)