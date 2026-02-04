from typing import List, Type
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

    def shutdown(self):
        """清理所有系统（如果需要）"""
        # 未来可以在这里添加 unregister 逻辑
        self.systems.clear()
