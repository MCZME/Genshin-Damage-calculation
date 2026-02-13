import pytest
from core.context import create_context
from core.systems.damage_system import DamageContext
from core.systems.contract.damage import Damage, DamageType
from core.systems.contract.reaction import ElementalReactionType
from core.mechanics.aura import Element

class TestElementalReactionsFullFlow:
    @pytest.fixture
    def setup_scene(self, target_entity, source_entity):
        ctx = create_context()
        
        # 补全 Mock 实体的必需属性
        source_entity.ctx = ctx
        target_entity.ctx = ctx
        
        target_entity.add_effect = lambda eff: target_entity.active_effects.append(eff)
        source_entity.level = 90
        source_entity.attribute_panel['攻击力'] = 1000.0
        
        return ctx

    def test_vaporize_forward_full_flow(self, setup_scene, source_entity, target_entity):
        """1. 增幅反应测试：强水触发蒸发 (2.0x)"""
        ctx = setup_scene
        # 修正：使用 Element 枚举
        target_entity.aura.apply_element(Element.PYRO, 1.0)

        dmg = Damage(100.0, (Element.HYDRO, 1.0), DamageType.NORMAL, "水箭")
        dmg.set_source(source_entity)

        pipeline = ctx.get_system("DamageSystem").pipeline
        pipeline.run(DamageContext(dmg, source_entity, target_entity))

        assert dmg.damage > 0
        assert any(res.reaction_type == ElementalReactionType.VAPORIZE for res in dmg.reaction_results)

    def test_bloom_reaction_chain(self, setup_scene, source_entity, target_entity):
        """测试绽放反应"""
        ctx = setup_scene
        target_entity.aura.apply_element(Element.DENDRO, 1.0)

        dmg = Damage(100.0, (Element.HYDRO, 1.0), DamageType.NORMAL, "水波")
        dmg.set_source(source_entity)
        # 必须设为可部署
        dmg.config.is_deployable = True
        
        pipeline = ctx.get_system("DamageSystem").pipeline
        pipeline.run(DamageContext(dmg, source_entity, target_entity))

        assert any(res.reaction_type == ElementalReactionType.BLOOM for res in dmg.reaction_results)
