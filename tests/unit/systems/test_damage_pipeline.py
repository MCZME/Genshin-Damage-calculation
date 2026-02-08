import pytest
from core.action.damage import Damage, DamageType
from core.systems.damage_system import DamagePipeline, DamageContext
from core.effect.elemental import ElementalInfusionEffect
from core.mechanics.aura import Element

class TestDamagePipelineUnit:
    def test_snapshot_attributes(self, event_engine, source_entity, target_entity):
        """测试属性快照功能"""
        pipeline = DamagePipeline(event_engine)
        dmg = Damage(100.0, (Element.PYRO, 1.0), DamageType.NORMAL, "Snapshot")
        ctx = DamageContext(dmg, source_entity, target_entity)

        source_entity.attribute_panel['攻击力'] = 2500
        source_entity.attribute_panel['暴击率'] = 88.8

        pipeline._snapshot(ctx)

        assert ctx.stats["攻击力"] == 2500
        assert ctx.stats["暴击率"] == 88.8

    @pytest.mark.parametrize("defense, attacker_lv, expected_mult", [
        (500, 90, 0.65517),
        (950, 90, 0.5),
        (0, 90, 1.0),
    ])
    def test_defense_calculation(self, event_engine, source_entity, target_entity, defense, attacker_lv, expected_mult):
        """参数化测试防御区计算"""
        pipeline = DamagePipeline(event_engine)
        dmg = Damage(100.0, (Element.PYRO, 1.0), DamageType.NORMAL, "Def")
        ctx = DamageContext(dmg, source_entity, target_entity)

        target_entity.attribute_panel['防御力'] = defense
        source_entity.level = attacker_lv

        pipeline._calculate_def_res(ctx)
        assert pytest.approx(ctx.stats["防御区系数"], 0.0001) == expected_mult

    def test_infusion_priority(self, event_engine, source_entity, target_entity):
        """测试元素附魔优先级: 水 > 火 > 冰"""
        pipeline = DamagePipeline(event_engine)
        dmg = Damage(100.0, (Element.PHYSICAL, 0), DamageType.NORMAL, "Infusion")
        ctx = DamageContext(dmg, source_entity, target_entity)

        # 优先级: HYDRO > PYRO > CRYO
        pyro_infusion = ElementalInfusionEffect(source_entity, "火附魔", Element.PYRO, 10*60)
        hydro_infusion = ElementalInfusionEffect(source_entity, "水附魔", Element.HYDRO, 10*60)
        source_entity.active_effects = [pyro_infusion, hydro_infusion]

        pipeline._handle_infusion(ctx)

        assert ctx.damage.element[0] == Element.HYDRO

    def test_transformative_reaction_logic(self, event_engine, source_entity, target_entity):
        """测试剧变反应逻辑"""
        pipeline = DamagePipeline(event_engine)
        dmg = Damage(0, (Element.ELECTRO, 0), DamageType.REACTION, "Overload")
        # 直接通过 data 字典注入参数
        dmg.data["等级系数"] = 1200
        dmg.data["反应系数"] = 2.75
        
        ctx = DamageContext(dmg, source_entity, target_entity)
        source_entity.attribute_panel['元素精通'] = 0
        
        pipeline._calculate(ctx)
        
        # Base(1200) * React(2.75) * Res(0.9) = 3300 * 0.9 = 2970
        assert pytest.approx(ctx.final_result, 0.1) == 2970
