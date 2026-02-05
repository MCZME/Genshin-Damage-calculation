from core.event import EventBus, EventType, GameEvent, EventHandler
from core.context import SimulationContext, set_context

class MockHandler(EventHandler):
    def __init__(self):
        self.triggered = False
        self.received_data = None

    def handle_event(self, event: GameEvent):
        self.triggered = True
        self.received_data = event.data

def test_event_bus_proxy():
    # 使用 SimulationContext 启动测试环境 (with 语法)
    with SimulationContext() as ctx:
        handler = MockHandler()
        test_type = EventType.FRAME_END
        test_data = {"test_key": "test_value"}
        
        # 1. 订阅
        EventBus.subscribe(test_type, handler)
        
        # 2. 发布
        event = GameEvent(event_type=test_type, frame=0, data=test_data)
        EventBus.publish(event)
        
        # 3. 验证
        assert handler.triggered is True
        assert handler.received_data["test_key"] == "test_value"
        
        # 4. 取消订阅
        EventBus.unsubscribe(test_type, handler)
        print("EventBus Smoke Test Passed!")

if __name__ == "__main__":
    test_event_bus_proxy()
