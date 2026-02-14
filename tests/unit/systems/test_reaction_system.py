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
        # 1. 构造反应结果
        res = ReactionResult(
            reaction_type=ElementalReactionType.OVERLOAD,
            category=ReactionCategory.TRANSFORMATIVE,
            source_element=Element.ELECTRO,
            target_element=Element.PYRO,
            gauge_consumed=0.8
        )

        published_events = []
        class CaptureHandler(EventHandler):
            def handle_event(self, event: GameEvent):
                if event.event_type == EventType.BEFORE_DAMAGE:
                    published_events.append(event)
        
        handler = CaptureHandler()
        sim_ctx.event_engine.subscribe(EventType.BEFORE_DAMAGE, handler)

        # 2. 直接发布反应事件，模拟底层产出的反应
        sim_ctx.event_engine.publish(GameEvent(
            event_type=EventType.AFTER_ELEMENTAL_REACTION,
            frame=get_current_time(),
            source=source_entity,
            data={
                "target": target_entity,
                "elemental_reaction": res
            }
        ))

        # 3. 验证 ReactionSystem 是否截获该事件并发布了名为 "超载" 的剧变伤害事件
        assert any(isinstance(e.data.get('damage'), Damage) and e.data['damage'].name == "超载" for e in published_events)
