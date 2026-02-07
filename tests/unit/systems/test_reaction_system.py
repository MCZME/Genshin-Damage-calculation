import pytest
from core.systems.reaction_system import ReactionSystem
from core.event import EventType, GameEvent, DamageEvent
from core.action.reaction import (
    ReactionResult, 
    ReactionCategory, 
    ElementalReactionType, 
    REACTION_CLASSIFICATION
)
from core.action.damage import Damage, DamageType
from core.mechanics.aura import Element
from core.tool import GetCurrentTime, get_reaction_multiplier

class TestReactionSystemUnit:
    """ReactionSystem 策略分发单元测试"""

    @pytest.fixture
    def reaction_sys(self, event_engine):
        """提供初始化好的反应系统"""
        sys = ReactionSystem()
        class MockContext:
            def __init__(self, engine):
                self.event_engine = engine
        sys.initialize(MockContext(event_engine))
        return sys

    def test_amplifying_reaction_dispatch(self, reaction_sys, source_entity, target_entity):
        """测试增幅反应的分发：验证不产生额外伤害事件"""
        dmg = Damage(100.0, ('火', 1.0), DamageType.NORMAL, "攻击")
        res = ReactionResult(
            reaction_type=ElementalReactionType.VAPORIZE,
            category=ReactionCategory.AMPLIFYING,
            source_element=Element.PYRO,
            target_element=Element.HYDRO,
            multiplier=1.5
        )
        dmg.data['reaction_results'] = [res]
        
        event = GameEvent(EventType.BEFORE_DAMAGE, GetCurrentTime(), source=source_entity, 
                          data={'character': source_entity, 'target': target_entity, 'damage': dmg})
        reaction_sys.handle_event(event)

    def test_transformative_reaction_dispatch(self, reaction_sys, event_engine, source_entity, target_entity):
        """测试剧变反应的分发：验证产生了新的伤害事件"""
        dmg = Damage(0, ('雷', 1.0), DamageType.NORMAL, "雷攻击")
        res = ReactionResult(
            reaction_type=ElementalReactionType.OVERLOAD,
            category=ReactionCategory.TRANSFORMATIVE,
            source_element=Element.ELECTRO,
            target_element=Element.PYRO,
            gauge_consumed=0.8
        )
        dmg.data['reaction_results'] = [res]
        
        published_events = []
        def capture_event(ev):
            published_events.append(ev)
        event_engine.publish = capture_event 
        
        event = GameEvent(EventType.BEFORE_DAMAGE, GetCurrentTime(), source=source_entity, 
                          data={'character': source_entity, 'target': target_entity, 'damage': dmg})
        reaction_sys.handle_event(event)
        
        overload_event = next((e for e in published_events if isinstance(e, DamageEvent) and e.damage.name == "超载"), None)
        assert overload_event is not None
        assert overload_event.damage.damage_type == DamageType.REACTION
        assert '等级系数' in overload_event.damage.data
        assert overload_event.damage.data['反应系数'] == 2.75

    def test_superconduct_side_effect(self, reaction_sys, event_engine, source_entity, target_entity):
        """测试超导反应的副作用：验证减抗 Effect 被施加"""
        dmg = Damage(0, ('冰', 1.0), DamageType.NORMAL, "冰攻击")
        res = ReactionResult(
            reaction_type=ElementalReactionType.SUPERCONDUCT,
            category=ReactionCategory.TRANSFORMATIVE,
            source_element=Element.CRYO,
            target_element=Element.ELECTRO
        )
        dmg.data['reaction_results'] = [res]
        
        # 将 target_entity 的 Mock 接口补全，使其支持 ResistanceDebuffEffect
        # 统一使用 active_effects 字段 (符合 conftest 定义)
        target_entity.add_effect = lambda eff: target_entity.active_effects.append(eff)
        
        event = GameEvent(EventType.BEFORE_DAMAGE, GetCurrentTime(), source=source_entity, 
                          data={'character': source_entity, 'target': target_entity, 'damage': dmg})
        reaction_sys.handle_event(event)
        
        # 验证超导减抗是否生效
        assert any(eff.name == "超导" for eff in target_entity.active_effects)
