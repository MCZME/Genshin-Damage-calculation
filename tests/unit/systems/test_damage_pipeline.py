import pytest
from core.systems.contract.damage import Damage
from core.action.action_data import AttackConfig
from core.action.attack_tag_resolver import AttackCategory
from core.systems.damage_system import DamagePipeline, DamageContext
from core.event import GameEvent, EventType
from core.tool import get_current_time

class TestDamagePipelineUnit:
    def test_snapshot_attributes(self, event_engine, source_entity, target_entity):
        """测试属性快照功能"""
        pipeline = DamagePipeline(event_engine)
        # element, damage_multiplier, scaling_stat, config, name
        dmg = Damage(
            element=("火", 1.0),
            damage_multiplier=100.0,
            scaling_stat="攻击力",
            config=AttackConfig(attack_tag="普通攻击1"),
            name="Snapshot"
        )
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
        dmg = Damage(
            element=("火", 1.0),
            damage_multiplier=100.0,
            scaling_stat="攻击力",
            config=AttackConfig(attack_tag="普通攻击1"),
            name="Def"
        )
        ctx = DamageContext(dmg, source_entity, target_entity)

        target_entity.attribute_panel['防御力'] = defense
        source_entity.level = attacker_lv

        pipeline._calculate_def_res(ctx)
        assert pytest.approx(ctx.stats["防御区系数"], 0.0001) == expected_mult

    def test_damage_audit_trail(self, event_engine, source_entity, target_entity):
        """测试伤害审计链记录"""
        pipeline = DamagePipeline(event_engine)
        dmg = Damage(
            element=("水", 1.0),
            damage_multiplier=200.0,
            scaling_stat="生命值",
            config=AttackConfig(attack_tag="元素战技"),
            name="FurinaSkill"
        )
        ctx = DamageContext(dmg, source_entity, target_entity)
        
        source_entity.attribute_panel['生命值'] = 40000
        source_entity.attribute_panel['伤害加成'] = 20.0 # 基础 20%
        
        # 模拟一个外部增益注入 (使用具备 handle_event 的 Mock 对象)
        class MockBuff:
            def handle_event(self, event):
                event.data["damage_context"].add_modifier(source="测试增益", stat="伤害加成", value=30.0)
        
        event_engine.subscribe(EventType.BEFORE_CALCULATE, MockBuff())
        
        pipeline.run(ctx)
        
        # 验证审计链
        audit = dmg.data["audit_trail"]
        sources = [record.source for record in audit]
        
        assert "角色基础面板" in sources
        assert "测试增益" in sources
        assert "总和伤害加成区" in sources
        
        # 验证数值 (生命值 40000 * 200% * (1 + (20+30)/100) * 防御(0.5) * 抗性(0.9))
        # 40000 * 2.0 * 1.5 * 0.5 * 0.9 = 54000
        # 注意: 这里的防御和抗性取决于 MockEntity 的默认值
        # MockEntity: 防御 800, 等级 90 -> coeff = (5*90+500)/(800+5*90+500) = 950 / 1750 = 0.542857
        # MockEntity: 抗性 10 -> coeff = 1 - 10/100 = 0.9
        # 40000 * 2.0 * 1.5 * 0.542857 * 0.9 = 58628.556
        
        assert pytest.approx(dmg.damage, 0.1) == 58628.6
