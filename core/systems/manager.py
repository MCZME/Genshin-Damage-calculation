from typing import List, Type, Any, Optional
from core.context import SimulationContext
from core.systems.base_system import GameSystem

class SystemManager:
    """
    负责管理和自动装配所有的 GameSystem。
    """
    def __init__(self, context: SimulationContext):
        self.context = context
        self.systems: List[GameSystem] = []

    def add_system(self, system_cls: Type[GameSystem]) -> GameSystem:
        """实例化并注册一个新系统"""
        system = system_cls()
        system.initialize(self.context)
        self.systems.append(system)
        return system

    def get_system(self, cls_or_name: Any) -> Optional[GameSystem]:
        """根据类或名称获取系统实例"""
        for system in self.systems:
            if isinstance(cls_or_name, str):
                if system.__class__.__name__ == cls_or_name:
                    return system
            else:
                if isinstance(system, cls_or_name):
                    return system
        return None

    def shutdown(self):
        """清理所有系统（如果需要）"""
        # 未来可以在这里添加 unregister 逻辑
        self.systems.clear()
