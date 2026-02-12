from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from core.combat_space import CombatSpace
    from core.systems.manager import SystemManager
    from core.logger import SimulationLogger

# ---------------------------------------------------------
# Simulation Context
# ---------------------------------------------------------

@dataclass
class SimulationContext:
    """模拟上下文，持有当前仿真实例的所有运行状态与核心组件。

    Attributes:
        current_frame: 当前仿真的总帧数。
        global_move_dist: 角色在场景中累计的水平移动距离。
        global_vertical_dist: 角色在场景中累计的垂直移动距离。
        event_engine: 负责该上下文内部事件分发的引擎。
        space: 战场空间管理器，负责实体物理位置与碰撞。
        system_manager: 管理并驱动所有仿真子系统 (如伤害、反应系统)。
        logger: 仿真的日志记录器。
    """

    # 基础状态
    current_frame: int = 0

    # 全局计数器
    global_move_dist: float = 0.0
    global_vertical_dist: float = 0.0

    # 核心组件 (使用字符串前向引用规避循环引用)
    event_engine: Optional["EventEngine"] = field(default=None)
    space: Optional["CombatSpace"] = None
    system_manager: Optional["SystemManager"] = None
    logger: Optional["SimulationLogger"] = None

    # 上下文管理器状态
    _token: Optional[Any] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        """完成上下文组件的自动初始化。"""
        if self.event_engine is None:
            self.event_engine = EventEngine()

        if self.space is None:
            from core.combat_space import CombatSpace
            self.space = CombatSpace()

    def __enter__(self) -> "SimulationContext":
        """激活上下文，使其成为当前线程/协程的活跃上下文。"""
        self._token = _current_context.set(self)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """退出并清理上下文。"""
        if self._token:
            _current_context.reset(self._token)
            self._token = None
        self.reset()

    def advance_frame(self) -> None:
        """推进全局时间轴一帧，并驱动物理空间更新。"""
        self.current_frame += 1
        if self.space:
            self.space.update()

    def get_system(self, cls_or_name: Union[str, Type]) -> Optional[Any]:
        """获取已挂载的仿真系统实例。

        Args:
            cls_or_name: 系统的类定义或字符串名称。

        Returns:
            Optional[Any]: 系统实例，若未找到则返回 None。
        """
        if self.system_manager:
            return self.system_manager.get_system(cls_or_name)
        return None

    def reset(self) -> None:
        """重置上下文状态至初始点，清除所有实体与缓存。"""
        self.current_frame = 0
        self.global_move_dist = 0.0
        self.global_vertical_dist = 0.0
        if self.event_engine:
            self.event_engine.clear()
        
        # 记录重置日志
        if self.logger:
            self.logger.log_info("Context Reset", sender="Context")

    def take_snapshot(self) -> Dict[str, Any]:
        """抓取当前仿真场景的全量状态快照。

        Returns:
            Dict[str, Any]: 包含帧数、全局变量及所有实体状态的字典。
        """
        snapshot = {
            "frame": self.current_frame,
            "global": {
                "move_dist": round(self.global_move_dist, 3),
                "vertical_dist": round(self.global_vertical_dist, 3)
            },
            "entities": []
        }

        if self.space:
            from core.entities.base_entity import Faction
            for faction in Faction:
                # 访问 CombatSpace 内部存储的实体列表
                for entity in self.space._entities.get(faction, []):
                    snapshot["entities"].append(entity.export_state())

        return snapshot


# ---------------------------------------------------------
# Event Engine (Instance-based)
# ---------------------------------------------------------

class EventEngine:
    """基于实例的事件驱动引擎。
    
    支持在特定的 SimulationContext 内进行事件订阅、取消订阅与发布。
    支持父子引擎链式发布。
    """

    def __init__(self, parent: Optional["EventEngine"] = None):
        """初始化事件引擎。

        Args:
            parent: 可选的父引擎，若存在，事件将向上冒泡发布。
        """
        self._handlers: Dict[Any, List[Any]] = {}
        self.parent = parent

    def subscribe(self, event_type: Any, handler: Any) -> None:
        """订阅特定类型的事件。

        Args:
            event_type: 事件类型枚举。
            handler: 处理函数或实现了 handle_event 的对象。
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: Any, handler: Any) -> None:
        """取消对特定事件的订阅。

        Args:
            event_type: 事件类型枚举。
            handler: 之前订阅的处理程序。
        """
        if event_type in self._handlers:
            if handler in self._handlers[event_type]:
                self._handlers[event_type].remove(handler)
            if not self._handlers[event_type]:
                del self._handlers[event_type]

    def publish(self, event: Any) -> None:
        """发布一个事件，触发所有对应的处理程序。

        Args:
            event: 事件对象。需具备 event_type 属性。
        """
        if hasattr(event, "event_type"):
            # 使用快照迭代以防止处理过程中订阅列表发生变化
            handlers = self._handlers.get(event.event_type, []).copy()
            for handler in handlers:
                # 卫语句：如果事件已被标记为取消，停止分发
                if getattr(event, "cancelled", False):
                    return
                handler.handle_event(event)

        # 冒泡至父引擎
        if getattr(event, "propagation_stopped", False):
            return
        if self.parent:
            self.parent.publish(event)

    def clear(self) -> None:
        """清除所有订阅记录。"""
        self._handlers.clear()


# ---------------------------------------------------------
# Context Management Utilities
# ---------------------------------------------------------

_current_context: ContextVar[Optional[SimulationContext]] = ContextVar(
    "current_simulation_context", default=None
)

def get_context() -> SimulationContext:
    """获取当前活跃的仿真上下文。

    Raises:
        RuntimeError: 当当前环境中不存在活跃上下文时抛出。

    Returns:
        SimulationContext: 当前活跃的上下文实例。
    """
    ctx = _current_context.get()
    if ctx is None:
        raise RuntimeError("No active SimulationContext found.")
    return ctx

def set_context(ctx: SimulationContext) -> None:
    """手动设置当前的活跃上下文。

    Args:
        ctx: 待设定的上下文实例。
    """
    _current_context.set(ctx)

def create_context() -> SimulationContext:
    """工厂函数：创建一个完整配置的仿真上下文实例。
    
    该函数会自动初始化注册表、日志系统以及挂载所有核心仿真子系统。

    Returns:
        SimulationContext: 已就绪的上下文实例。
    """
    from core.logger import SimulationLogger
    from core.registry import initialize_registry
    from core.systems.damage_system import DamageSystem
    from core.systems.energy_system import EnergySystem
    from core.systems.health_system import HealthSystem
    from core.systems.manager import SystemManager
    from core.systems.natlan_system import NatlanSystem
    from core.systems.reaction_system import ReactionSystem
    from core.systems.shield_system import ShieldSystem
    from core.systems.resonance_system import ResonanceSystem

    # 1. 基础环境准备
    initialize_registry()
    ctx = SimulationContext()
    set_context(ctx)

    # 2. 挂载核心组件
    ctx.logger = SimulationLogger()
    ctx.system_manager = SystemManager(ctx)

    # 3. 注册标准子系统
    ctx.system_manager.add_system(DamageSystem)
    ctx.system_manager.add_system(ReactionSystem)
    ctx.system_manager.add_system(HealthSystem)
    ctx.system_manager.add_system(ShieldSystem)
    ctx.system_manager.add_system(EnergySystem)
    ctx.system_manager.add_system(NatlanSystem)
    ctx.system_manager.add_system(ResonanceSystem)

    return ctx
