import pytest
from core.context import create_context
from core.systems.damage_system import DamageContext
from core.systems.contract.damage import Damage
from core.systems.contract.reaction import ElementalReactionType
from core.systems.contract.attack import AttackConfig
from core.mechanics.aura import Element


class TestElementalReactionsFullFlow:
    @pytest.fixture
    def sim_ctx(self):
        ctx = create_context()
        return ctx

    def test_vaporize_forward_full_flow(self, sim_ctx, source_entity, target_entity):
        """1. 增幅反应测试：强水触发蒸发 (2.0x)"""
        # 挂火
        target_entity.aura.apply_element(Element.PYRO, 1.0)

        dmg = Damage(
            element=(Element.HYDRO, 1.0),
            damage_multiplier=100.0,
            scaling_stat="攻击力",
            name="水箭",
        )
        dmg.set_source(source_entity)

        pipeline = sim_ctx.get_system("DamageSystem").pipeline
        pipeline.run(DamageContext(dmg, source_entity, target_entity))

        assert dmg.damage > 0
        assert any(
            res.reaction_type == ElementalReactionType.VAPORIZE
            for res in dmg.reaction_results
        )

    def test_bloom_reaction_chain(self, sim_ctx, source_entity, target_entity):
        """测试绽放反应"""
        # 挂草
        target_entity.aura.apply_element(Element.DENDRO, 1.0)

        config = AttackConfig(is_deployable=True)
        dmg = Damage(
            element=(Element.HYDRO, 1.0),
            damage_multiplier=100.0,
            scaling_stat="攻击力",
            config=config,
            name="水波",
        )
        dmg.set_source(source_entity)

        pipeline = sim_ctx.get_system("DamageSystem").pipeline
        pipeline.run(DamageContext(dmg, source_entity, target_entity))

        assert any(
            res.reaction_type == ElementalReactionType.BLOOM
            for res in dmg.reaction_results
        )
