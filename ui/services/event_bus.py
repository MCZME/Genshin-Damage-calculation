from typing import Dict, List, Callable
from core.logger import get_ui_logger

class UIEventBus:
    """
    UI 事件总线：解耦状态变更与视图刷新。
    负责管理订阅者并分发状态变更信号。
    """
    def __init__(self):
        self._observers: Dict[str, List[Callable]] = {
            "strategic": [],
            "tactical": [],
            "scene": [],
            "simulation": [],
            "global": []
        }

    def subscribe(self, event_type: str, callback: Callable):
        if event_type in self._observers:
            self._observers[event_type].append(callback)
        else:
            get_ui_logger().log_warning(f"UIEventBus: Attempted to subscribe to unknown event type '{event_type}'")

    def unsubscribe(self, event_type: str, callback: Callable):
        if event_type in self._observers:
            try:
                self._observers[event_type].remove(callback)
            except ValueError:
                pass

    def notify(self, event_type: str, *args, **kwargs):
        """发送通知给所有订阅者"""
        # 同时触发特定事件和全局事件
        targets = self._observers.get(event_type, [])
        global_targets = self._observers.get("global", [])
        
        # 依次执行回调
        for callback in targets + global_targets:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                get_ui_logger().log_error(f"UIEventBus Notify Error ({event_type}): {e}")
