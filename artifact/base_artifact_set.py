from typing import Any
from core.event import EventHandler


class BaseArtifactSet(EventHandler):
    """
    圣遗物套装效果基类。
    """

    def __init__(self, name: str = ""):
        self.name = name

    def apply_2_set_effect(self, character: Any) -> None:
        """应用2件套效果。"""
        pass

    def apply_4_set_effect(self, character: Any) -> None:
        """应用4件套效果。"""
        pass

    def handle_event(self, event: Any) -> None:
        """处理套装相关的事件（由子类重写）。"""
        pass
