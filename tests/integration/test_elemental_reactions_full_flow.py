import pytest
from core.context import EventEngine
from core.systems.damage_system import DamageSystem
from core.systems.reaction_system import ReactionSystem
from core.event import EventType, GameEvent, DamageEvent, EventHandler
from core.action.damage import Damage, DamageType
from core.mechanics.aura import Element
from core.tool import GetCurrentTime, get_reaction_multiplier

class DamageCaptureHandler(EventHandler):
    def __init__(self, target_list):
        self.target_list = target_list
    def handle_event(self, event):
        if isinstance(event, DamageEvent):
            self.target_list.append(event.damage)

class TestElementalReactionsFullFlow:
    """
    原神伤害引擎：全量反应集成实验室 (高阶扩展版)
    """

    @pytest.fixture
    def setup_engine(self, event_engine, target_entity, source_entity):
        damage_sys = DamageSystem()
        reaction_sys = ReactionSystem()
        
        class MockContext:
            def __init__(self, engine):
                self.event_engine = engine
                self.team = None
        
        ctx = MockContext(event_engine)
        damage_sys.initialize(ctx)
        reaction_sys.initialize(ctx)
        damage_sys.register_events(event_engine)
        reaction_sys.register_events(event_engine)
        
        target_entity.add_effect = lambda eff: target_entity.active_effects.append(eff)
        source_entity.level = 90
        source_entity.attributePanel['攻击力'] = 1000.0
        # 确保精通为 0，防止精通加成干扰基础倍率测试
        source_entity.attributePanel['元素精通'] = 0.0
        
        self.captured_damages = []
        handler = DamageCaptureHandler(self.captured_damages)
        event_engine.subscribe(EventType.AFTER_DAMAGE, handler)
        return event_engine

    def test_vaporize_forward_full_flow(self, setup_engine, source_entity, target_entity):
        """1. 增幅反应测试：强水触发蒸发 (2.0x)"""
        target_entity.aura.apply_element(Element.PYRO, 1.0)
        
        dmg = Damage(100.0, (Element.HYDRO, 1.0), DamageType.NORMAL, "水箭")
        setup_engine.publish(GameEvent(EventType.BEFORE_DAMAGE, GetCurrentTime(), source=source_entity,
                                     data={'character': source_entity, 'target': target_entity, 'damage': dmg}))
        
        # 预期 = 1000 * 0.65517 * 0.9 * 2.0 = 1179.310
        assert dmg.damage == pytest.approx(1179.310, abs=0.001)

    def test_bloom_reaction_chain(self, setup_engine, source_entity, target_entity):
        """测试绽放反应：产生独立伤害"""
        target_entity.aura.apply_element(Element.DENDRO, 1.0)
        
        dmg = Damage(100.0, (Element.HYDRO, 1.0), DamageType.NORMAL, "水波")
        setup_engine.publish(GameEvent(EventType.BEFORE_DAMAGE, GetCurrentTime(), source=source_entity,
                                     data={'character': source_entity, 'target': target_entity, 'damage': dmg}))
        
        bloom_dmg = next((d for d in self.captured_damages if d.name == "绽放"), None)
        assert bloom_dmg is not None
        assert bloom_dmg.damage == pytest.approx(2604.33, abs=0.01)

    def test_quicken_bloom_coexistence(self, setup_engine, source_entity, target_entity):
        """测试高级物理：激化态产生绽放"""
        target_entity.aura.apply_element(Element.DENDRO, 1.0)
        target_entity.aura.apply_element(Element.ELECTRO, 1.0)
        
        dmg = Damage(100.0, (Element.HYDRO, 0.5), DamageType.NORMAL, "弱水")
        setup_engine.publish(GameEvent(EventType.BEFORE_DAMAGE, GetCurrentTime(), source=source_entity,
                                     data={'character': source_entity, 'target': target_entity, 'damage': dmg}))
        
        assert any(d.name == "绽放" for d in self.captured_damages)
        assert target_entity.aura.quicken_gauge is not None
        assert target_entity.aura.quicken_gauge.current_gauge == pytest.approx(0.3)

    def test_burning_consumption_flow(self, setup_engine, source_entity, target_entity):
        """测试燃烧：时间线消耗 (含自然衰减)"""
        target_entity.aura.apply_element(Element.DENDRO, 1.0) # 0.8GU
        
        dmg = Damage(100.0, (Element.PYRO, 1.0), DamageType.NORMAL, "点火")
        setup_engine.publish(GameEvent(EventType.BEFORE_DAMAGE, GetCurrentTime(), source=source_entity,
                                     data={'character': source_entity, 'target': target_entity, 'damage': dmg}))
        
        assert target_entity.aura.is_burning is True
        
        # 1秒流逝 -> 消耗 0.4GU (燃烧) + 约 0.0842GU (自然衰减)
        for _ in range(60):
            target_entity.update()
            
        dendro_aura = next(a for a in target_entity.aura.auras if a.element == Element.DENDRO)
        # 0.8 - (0.4 + 0.0842) = 0.3158
        assert dendro_aura.current_gauge == pytest.approx(0.3158, abs=0.001)

    def test_electro_charged_coexistence_and_trigger(self, setup_engine, source_entity, target_entity):
        """测试感电共存反应"""
        target_entity.aura.apply_element(Element.HYDRO, 1.0)
        target_entity.aura.apply_element(Element.ELECTRO, 1.0)
        target_entity.aura.is_electro_charged = True
        
        dmg = Damage(100.0, (Element.PYRO, 1.0), DamageType.NORMAL, "烈焰")
        setup_engine.publish(GameEvent(EventType.BEFORE_DAMAGE, GetCurrentTime(), source=source_entity,
                                     data={'character': source_entity, 'target': target_entity, 'damage': dmg}))
        
        results = dmg.data.get('reaction_results', [])
        assert len(results) >= 1

    def test_frozen_melt_priority(self, setup_engine, source_entity, target_entity):
        """测试火打冻结：优先级与加成"""
        target_entity.aura.apply_element(Element.HYDRO, 1.0)
        target_entity.aura.apply_element(Element.CRYO, 1.0)
        
        dmg = Damage(100.0, (Element.PYRO, 1.0), DamageType.NORMAL, "融化火")
        setup_engine.publish(GameEvent(EventType.BEFORE_DAMAGE, GetCurrentTime(), source=source_entity,
                                     data={'character': source_entity, 'target': target_entity, 'damage': dmg}))
        
        assert target_entity.aura.frozen_gauge is None
        # 1000 * 0.655 * 0.9 * 2.0 = 1179.31
        assert dmg.damage == pytest.approx(1179.310, abs=0.001)
