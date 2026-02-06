from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------
# 类型定义 (前置声明，避免循环引用)
# ---------------------------------------------------------
# 这里我们使用字符串类型提示，或者由使用者自行 import
EventHandlerType = Any 
EventTypeType = Any
GameEventType = Any

# ---------------------------------------------------------
# Event Engine (Instance-based)
# ---------------------------------------------------------
class EventEngine:
    """
    基于实例的事件引擎，支持层级冒泡。
    """
    def __init__(self, parent: Optional['EventEngine'] = None):
        self._handlers: Dict[Any, List[EventHandlerType]] = {}
        self.parent = parent

    def subscribe(self, event_type: Any, handler: EventHandlerType) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: Any, handler: EventHandlerType) -> None:
        if event_type in self._handlers:
            if handler in self._handlers[event_type]:
                self._handlers[event_type].remove(handler)
            if not self._handlers[event_type]:
                del self._handlers[event_type]

    def publish(self, event: Any) -> None:
        # 1. 触发本地监听器
        if hasattr(event, 'event_type'):
            handlers = self._handlers.get(event.event_type, []).copy()
            for handler in handlers:
                if getattr(event, 'cancelled', False):
                    return # 如果被取消，停止一切处理
                handler.handle_event(event)
        
        # 2. 检查是否需要停止冒泡
        # (假设 event 对象可能有 stop_propagation 方法或属性，这里简单检查属性)
        if getattr(event, 'propagation_stopped', False):
            return

        # 3. 向上冒泡到父级 Engine
        if self.parent:
            self.parent.publish(event)

    def clear(self) -> None:
        self._handlers.clear()

# ---------------------------------------------------------
# Simulation Context
# ---------------------------------------------------------
@dataclass
class SimulationContext:
    """
    模拟上下文，持有当前模拟的所有状态。
    """
    # 基础状态
    current_frame: int = 0
    
    # 全局计数器 (用于特殊机制)
    global_move_dist: float = 0.0      # 累计水平移动距离
    global_vertical_dist: float = 0.0  # 累计垂直移动距离 (下落)

    # 核心组件
    event_engine: EventEngine = field(default_factory=EventEngine)
    
    # 队伍与目标 (将在 TeamFactory 中初始化)
    team: Optional[Any] = None
    target: Optional[Any] = None
    
    # 系统管理器与日志
    system_manager: Optional[Any] = None
    logger: Optional[Any] = None

    # 上下文管理器状态
    _token: Optional[Any] = field(default=None, init=False, repr=False)

    def __enter__(self) -> 'SimulationContext':
        """进入 with 块时自动设置为当前上下文。"""
        self._token = _current_context.set(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出 with 块时自动清理。"""
        if self._token:
            _current_context.reset(self._token)
            self._token = None
        self.reset()

    def advance_frame(self) -> None:
        self.current_frame += 1

    def health_check(self) -> bool:
        """
        验证上下文健康状态。
        检查 EventEngine 和基础组件是否就绪。
        """
        if self.event_engine is None:
            return False
        # 如果有 logger，记录一条健康日志
        if self.logger:
            self.logger.log_info("Context health check passed.")
        return True

    def reset(self) -> None:
        self.current_frame = 0
        self.global_move_dist = 0.0
        self.global_vertical_dist = 0.0
        self.event_engine.clear()
        self.team = None
        self.target = None
        if self.logger:
            self.logger.log_info("Context Reset")

# ---------------------------------------------------------
# Context Management (Singleton-like Access)
# ---------------------------------------------------------
_current_context: ContextVar[Optional[SimulationContext]] = ContextVar("current_simulation_context", default=None)

def get_context() -> SimulationContext:
    """获取当前激活的模拟上下文。如果不存在，抛出异常。"""
    ctx = _current_context.get()
    if ctx is None:
        raise RuntimeError("No active SimulationContext found. Ensure you are running within a simulation scope.")
    return ctx

def set_context(ctx: SimulationContext) -> None:
    """设置当前激活的模拟上下文。"""
    _current_context.set(ctx)

def create_context() -> SimulationContext:
    """创建一个新的上下文并设置为当前激活状态。"""
    # 延迟导入以避免循环引用
    from core.systems.manager import SystemManager
    from core.systems.damage_system import DamageSystem
    from core.systems.reaction_system import ReactionSystem
    from core.systems.health_system import HealthSystem
    from core.systems.shield_system import ShieldSystem
    from core.systems.energy_system import EnergySystem
    from core.systems.natlan_system import NatlanSystem
    from core.registry import initialize_registry
    from core.logger import SimulationLogger
    
    # 1. 初始化注册表 (加载所有角色/武器类)
    initialize_registry()
    
    ctx = SimulationContext()
    set_context(ctx)
    
    # 2. 初始化日志 (每个 Context 拥有独立 Logger)
    ctx.logger = SimulationLogger()
    
    # 3. 初始化系统管理器
    ctx.system_manager = SystemManager(ctx)
    
    # 4. 自动装配核心系统
    ctx.system_manager.add_system(DamageSystem)
    ctx.system_manager.add_system(ReactionSystem)
    ctx.system_manager.add_system(HealthSystem)
    ctx.system_manager.add_system(ShieldSystem)
    ctx.system_manager.add_system(EnergySystem)
    ctx.system_manager.add_system(NatlanSystem)
    
    return ctx
