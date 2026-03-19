import pytest
from core.systems.contract.damage import Damage
from core.systems.contract.attack import AttackConfig
from core.systems.damage_system import DamagePipeline, DamageContext
from core.event import EventType
from core.mechanics.aura import Element


class TestDamagePipelineUnit:
    def test_snapshot_attributes(self, event_engine, source_entity, target_entity):
        """测试属性快照功能 (V2.5 阶段二)"""
        pipeline = DamagePipeline(event_engine)
        # elemental, damage_multiplier, scaling_stat, config, name
        dmg = Damage(
            element=(Element.PYRO, 1.0),
            damage_multiplier=(100.0,),
            scaling_stat=("攻击力",),
            config=AttackConfig(attack_tag="普通攻击1"),
            name="Snapshot",
        )
        ctx = DamageContext(dmg, source_entity, target_entity)

        source_entity.attribute_data["攻击力"] = 2500
        source_entity.attribute_data["暴击率"] = 88.8

        pipeline._stage_2_foundation(ctx)

        # 验证 stats 中的面板快照
        assert ctx.stats["攻击力"] == 2500
        # 暴击率在阶段四处理，阶段二不快照
        assert "攻击力技能倍率%" in ctx.stats
        assert ctx.stats["攻击力技能倍率%"] == 100.0

    @pytest.mark.parametrize(
        "defense, attacker_lv, expected_mult",
        [
            (500, 90, 0.65517),
            (950, 90, 0.5),
            (0, 90, 1.0),
        ],
    )
    def test_defense_calculation(
        self,
        event_engine,
        source_entity,
        target_entity,
        defense,
        attacker_lv,
        expected_mult,
    ):
        """参数化测试防御区计算 (V2.5 阶段四)"""
        pipeline = DamagePipeline(event_engine)
        dmg = Damage(
            element=(Element.PYRO, 1.0),
            damage_multiplier=(100.0,),
            scaling_stat=("攻击力",),
            config=AttackConfig(attack_tag="普通攻击1"),
            name="Def",
        )
        ctx = DamageContext(dmg, source_entity, target_entity)

        target_entity.attribute_data["防御力"] = defense
        source_entity.level = attacker_lv

        pipeline._resolve_def_res_coeffs(ctx)
        assert pytest.approx(ctx.stats["防御区系数"], 0.0001) == expected_mult

    def test_damage_audit_trail(self, event_engine, source_entity, target_entity):
        """测试伤害审计链记录"""
        from core.config import Config

        Config.set("emulation.open_critical", False)

        pipeline = DamagePipeline(event_engine)
        dmg = Damage(
            element=(Element.HYDRO, 1.0),
            damage_multiplier=(200.0,),
            scaling_stat=("生命值",),
            config=AttackConfig(attack_tag="元素战技"),
            name="FurinaSkill",
        )
        ctx = DamageContext(dmg, source_entity, target_entity)

        source_entity.attribute_data["生命值"] = 40000
        source_entity.attribute_data["伤害加成"] = 20.0
        source_entity.level = 90
        target_entity.attribute_data["防御力"] = 950
        target_entity.attribute_data["HYDRO元素抗性"] = 10.0

        # 模拟一个外部增益注入
        class MockBuff:
            def handle_event(self, event):
                event.data["damage_context"].add_modifier(
                    source="测试增益", stat="伤害加成", value=30.0
                )

        event_engine.subscribe(EventType.BEFORE_CALCULATE, MockBuff())

        pipeline.run(ctx)

        # 验证审计链
        audit = dmg.data["audit_trail"]
        sources = [record.source for record in audit]

        assert "[技能契约]" in sources
        assert "测试增益" in sources
        assert "[面板快照]" not in sources

        # 验证数值
        # 1. 基础伤害 = 40000 * (200 / 100) = 80000
        # 2. 伤害加成区 = 1 + (20 + 30) / 100 = 1.5
        # 3. 防御区 = 0.5 (Lv90 vs 950 Def)
        # 4. 抗性区 = 1 - 0.1 = 0.9
        # 预期 = 80000 * 1.5 * 0.5 * 0.9 = 54000
        assert dmg.damage == pytest.approx(54000.0, abs=1.0)
