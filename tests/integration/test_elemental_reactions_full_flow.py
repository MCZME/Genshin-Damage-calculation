import pytest
from core.context import EventEngine
from core.systems.damage_system import DamageSystem
from core.systems.reaction_system import ReactionSystem
from core.event import EventType, GameEvent, DamageEvent, EventHandler
from core.action.damage import Damage, DamageType
from core.mechanics.aura import Element
from core.tool import GetCurrentTime, get_reaction_multiplier

class DamageCaptureHandler(EventHandler):
    """事件捕获器：将函数适配为 EventHandler 接口"""
    def __init__(self, target_list):
        self.target_list = target_list
    def handle_event(self, event):
        if isinstance(event, DamageEvent):
            self.target_list.append(event.damage)

class TestElementalReactionsFullFlow:
    """
    原神伤害引擎：全链路反应集成测试 (枚举对齐版)
    验证：角色 -> 技能触发 -> 物理碰撞 -> 数值计算 -> 反应分发 -> 二次伤害/状态变更
    """

    @pytest.fixture
    def setup_engine(self, event_engine, target_entity):
        """初始化完整的计算环境"""
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
        
        self.captured_damages = []
        handler = DamageCaptureHandler(self.captured_damages)
        event_engine.subscribe(EventType.AFTER_DAMAGE, handler)
        
        return event_engine

    def test_vaporize_forward_full_flow(self, setup_engine, source_entity, target_entity):
        """1. 增幅反应测试：强水触发蒸发 (2.0x)"""
        target_entity.aura.apply_element(Element.PYRO, 1.0)
        source_entity.attributePanel['攻击力'] = 1000.0 
        source_entity.level = 90
        
        # 统一使用 Element 枚举
        dmg = Damage(100.0, (Element.HYDRO, 1.0), DamageType.NORMAL, "水箭")
        event = GameEvent(EventType.BEFORE_DAMAGE, GetCurrentTime(), source=source_entity,
                          data={'character': source_entity, 'target': target_entity, 'damage': dmg})
        setup_engine.publish(event)
        
        assert dmg.damage == pytest.approx(1179.310, abs=0.001)

    def test_overload_transformative_full_flow(self, setup_engine, source_entity, target_entity):
        """2. 剧变反应测试：超载"""
        target_entity.aura.apply_element(Element.PYRO, 1.0)
        source_entity.level = 90
        
        dmg = Damage(100.0, (Element.ELECTRO, 1.0), DamageType.NORMAL, "雷击")
        event = GameEvent(EventType.BEFORE_DAMAGE, GetCurrentTime(), source=source_entity,
                          data={'character': source_entity, 'target': target_entity, 'damage': dmg})
        setup_engine.publish(event)
        
        overload_dmg = next(d for d in self.captured_damages if d.name == "超载")
        assert overload_dmg.damage == pytest.approx(3580.95375)

    def test_superconduct_and_debuff_flow(self, setup_engine, source_entity, target_entity):
        """3. 组合测试：超导"""
        target_entity.aura.apply_element(Element.ELECTRO, 1.0)
        target_entity.current_resistance = {'物理': 10.0, '冰': 10.0}
        
        dmg = Damage(100.0, (Element.CRYO, 1.0), DamageType.NORMAL, "冰箭")
        event = GameEvent(EventType.BEFORE_DAMAGE, GetCurrentTime(), source=source_entity,
                          data={'character': source_entity, 'target': target_entity, 'damage': dmg})
        setup_engine.publish(event)
        
        assert any(d.name == "超导" for d in self.captured_damages)
        assert target_entity.current_resistance['物理'] == -30.0

    def test_quicken_and_aggravate_flow(self, setup_engine, source_entity, target_entity):
        """4. 草系反应测试：超激化"""
        target_entity.aura.apply_element(Element.DENDRO, 1.0)
        source_entity.level = 90
        source_entity.attributePanel['攻击力'] = 1000.0
        
        dmg1 = Damage(100.0, (Element.ELECTRO, 1.0), DamageType.NORMAL, "雷1")
        setup_engine.publish(GameEvent(EventType.BEFORE_DAMAGE, GetCurrentTime(), source=source_entity,
                                     data={'character': source_entity, 'target': target_entity, 'damage': dmg1}))
        
        dmg2 = Damage(100.0, (Element.ELECTRO, 1.0), DamageType.NORMAL, "雷2")
        setup_engine.publish(GameEvent(EventType.BEFORE_DAMAGE, GetCurrentTime(), source=source_entity,
                                     data={'character': source_entity, 'target': target_entity, 'damage': dmg2}))
        
        assert dmg2.damage == pytest.approx(1570.769, abs=0.001)

    def test_swirl_multi_element_flow(self, setup_engine, source_entity, target_entity):
        """5. 复杂反应测试：多重扩散"""
        target_entity.aura.apply_element(Element.HYDRO, 1.0)
        target_entity.aura.apply_element(Element.ELECTRO, 1.0)
        target_entity.aura.is_electro_charged = True
        
        dmg = Damage(100.0, (Element.ANEMO, 1.0), DamageType.NORMAL, "扩散风")
        setup_engine.publish(GameEvent(EventType.BEFORE_DAMAGE, GetCurrentTime(), source=source_entity,
                                     data={'character': source_entity, 'target': target_entity, 'damage': dmg}))
        
        swirls = [d for d in self.captured_damages if d.name == "扩散"]
        assert len(swirls) == 2

    def test_freeze_and_shatter_flow(self, setup_engine, source_entity, target_entity):
        """6. 机制测试：碎冰"""
        target_entity.aura.apply_element(Element.HYDRO, 1.0)
        dmg_ice = Damage(100.0, (Element.CRYO, 1.0), DamageType.NORMAL, "冰")
        setup_engine.publish(GameEvent(EventType.BEFORE_DAMAGE, GetCurrentTime(), source=source_entity,
                                     data={'character': source_entity, 'target': target_entity, 'damage': dmg_ice}))
        
        dmg_geo = Damage(100.0, (Element.GEO, 1.0), DamageType.NORMAL, "岩击")
        setup_engine.publish(GameEvent(EventType.BEFORE_DAMAGE, GetCurrentTime(), source=source_entity,
                                     data={'character': source_entity, 'target': target_entity, 'damage': dmg_geo}))
        
        assert any(d.name == "碎冰" for d in self.captured_damages)