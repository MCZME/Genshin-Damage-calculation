import pytest
from core.systems.reaction_system import ReactionSystem
from core.event import ElementalReactionEvent, EventType, EventHandler
from core.action.reaction import ElementalReaction, ElementalReactionType
from core.action.damage import Damage, DamageType
from core.tool import GetCurrentTime

class TestReactionSystemUnit:
    """ReactionSystem 逻辑单元测试"""

    @pytest.fixture
    def reaction_sys(self, event_engine):
        """提供初始化好的反应系统"""
        sys = ReactionSystem()
        class MockContext:
            pass
        ctx = MockContext()
        ctx.event_engine = event_engine
        ctx.team = None
        sys.initialize(ctx)
        return sys

    def test_amplifying_reaction_injection(self, reaction_sys, event_engine, source_entity, target_entity):
        """测试增幅反应 (蒸发) 的数据注入"""
        dmg = Damage(100.0, ('火', 1), DamageType.NORMAL, "火攻击")
        dmg.source = source_entity
        dmg.target = target_entity
        
        reaction = ElementalReaction(dmg, '火', '水')
        
        # 修正: 移除不支持的 before 关键字
        event = ElementalReactionEvent(EventType.BEFORE_ELEMENTAL_REACTION, GetCurrentTime(), 
                                       source=source_entity, elemental_reaction=reaction)
        reaction_sys.handle_event(event)
        
        assert reaction.reaction_type[1] == ElementalReactionType.VAPORIZE
        assert dmg.data['反应系数'] == 1.5

    def test_transformative_reaction_event_publishing(self, reaction_sys, event_engine, source_entity, target_entity):
        """测试剧变反应 (超载) 是否发布了新的伤害事件"""
        dmg = Damage(0, ('雷', 1), DamageType.NORMAL, "雷攻击")
        dmg.source = source_entity
        dmg.target = target_entity
        
        reaction = ElementalReaction(dmg, '雷', '火')
        
        published_damages = []
        class DamageCaptureHandler(EventHandler):
            def handle_event(self, event):
                if event.event_type == EventType.BEFORE_DAMAGE:
                    published_damages.append(event.data['damage'])
        
        event_engine.subscribe(EventType.BEFORE_DAMAGE, DamageCaptureHandler())

        event = ElementalReactionEvent(EventType.BEFORE_ELEMENTAL_REACTION, GetCurrentTime(), 
                                       source=source_entity, elemental_reaction=reaction)
        reaction_sys.handle_event(event)
        
        overload_dmg = next((d for d in published_damages if d.name == "超载"), None)
        assert overload_dmg is not None
        assert overload_dmg.damage_type == DamageType.REACTION
        assert '等级系数' in overload_dmg.data

    def test_catalyze_reaction_injection(self, reaction_sys, event_engine, source_entity, target_entity):
        """测试激化反应 (超激化) 的注入"""
        dmg = Damage(100.0, ('雷', 1), DamageType.NORMAL, "雷攻击")
        dmg.source = source_entity
        dmg.target = target_entity
        
        reaction = ElementalReaction(dmg, '雷', '激')
        
        event = ElementalReactionEvent(EventType.BEFORE_ELEMENTAL_REACTION, GetCurrentTime(), 
                                       source=source_entity, elemental_reaction=reaction)
        reaction_sys.handle_event(event)
        
        assert reaction.reaction_type[1] == ElementalReactionType.AGGRAVATE
        assert dmg.data['等级系数'] > 0
        assert dmg.reaction_type[1] == ElementalReactionType.AGGRAVATE
