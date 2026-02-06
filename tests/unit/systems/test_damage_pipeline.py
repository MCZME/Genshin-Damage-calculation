import pytest
from core.systems.damage_system import DamagePipeline
from core.config import Config

class TestDamagePipelineUnit:
    """DamagePipeline 核心计算逻辑单元测试"""

    def test_snapshot_attributes(self, event_engine, source_entity, target_entity, create_damage_context):
        """测试属性快照功能"""
        pipeline = DamagePipeline(event_engine)
        ctx = create_damage_context(source_entity, target_entity)
        
        # 修改源属性
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

    @pytest.mark.parametrize("res, expected_mult", [
        (10.0, 0.9),       # 标准 10% -> 0.9
        (0.0, 1.0),        # 0% -> 1.0
        (-20.0, 1.1),      # -20% -> 1.1
        (80.0, 0.23809),   # 1/(1+4*0.8) = 1/4.2 ≈ 0.23809
    ])
    def test_resistance_calculation(self, event_engine, source_entity, target_entity, create_damage_context, res, expected_mult):
        """参数化测试抗性区计算"""
        pipeline = DamagePipeline(event_engine)
        ctx = create_damage_context(source_entity, target_entity)
        
        target_entity.current_resistance['火'] = res
        
        pipeline._calculate_def_res(ctx)
        
        assert ctx.stats['抗性区系数'] == pytest.approx(expected_mult, 0.0001)

    def test_full_calculation_flow(self, event_engine, source_entity, target_entity, create_damage_context):
        """测试完整计算流程 (Base * Bonus * Def * Res)"""
        pipeline = DamagePipeline(event_engine)
        ctx = create_damage_context(source_entity, target_entity, value=100.0)
        
        source_entity.attributePanel['攻击力'] = 1000
        source_entity.attributePanel['伤害加成'] = 50.0
        target_entity.defense = 950
        target_entity.current_resistance['火'] = 0.0
        
        # 使用 Config.set
        Config.set('emulation.open_critical', False)
        
        pipeline.run(ctx)
        
        # Expect: 1000 * 1.5 * 0.5 * 1.0 = 750
        assert ctx.final_result == pytest.approx(750.0, 0.001)