import pytest
from core.context import create_context
from core.systems.contract.damage import Damage
from core.systems.contract.reaction import ReactionResult, ElementalReactionType, ReactionCategory
from core.mechanics.aura import Element
from core.event import GameEvent, EventType, EventHandler
from core.tool import get_current_time

class TestReactionSystemUnit:
    @pytest.fixture
    def sim_ctx(self):
        return create_context()

    @pytest.fixture
    def reaction_sys(self, sim_ctx):
        return sim_ctx.get_system("ReactionSystem")

    def test_transformative_reaction_dispatch(self, reaction_sys, sim_ctx, source_entity, target_entity):
        """测试剧变反应的分发：验证产生了新的伤害事件"""
        dmg = Damage(
            element=(Element.ELECTRO, 1.0),
            damage_multiplier=0,
            scaling_stat="攻击力",
            name="雷攻击"
        )
        res = ReactionResult(
            reaction_type=ElementalReactionType.OVERLOAD,
            category=ReactionCategory.TRANSFORMATIVE,
            source_element=Element.ELECTRO,
            target_element=Element.PYRO,
            gauge_consumed=0.8
        )
        # 手动注入反应结果
        dmg.reaction_results = [res]

        published_events = []
        class CaptureHandler(EventHandler):
            def handle_event(self, event: GameEvent):
                if event.event_type == EventType.BEFORE_DAMAGE:
                    published_events.append(event)
        
        handler = CaptureHandler()
        sim_ctx.event_engine.subscribe(EventType.BEFORE_DAMAGE, handler)

        # 触发反应处理
        event = GameEvent(EventType.BEFORE_DAMAGE, get_current_time(), source=source_entity,
                          data={'character': source_entity, 'target': target_entity, 'damage': dmg})
        reaction_sys.handle_event(event)

        # 验证是否产生了名为 "超载" 的剧变伤害事件
        assert any(isinstance(e.data.get('damage'), Damage) and e.data['damage'].name == "超载" for e in published_events)
