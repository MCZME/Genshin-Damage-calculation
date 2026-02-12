from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

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
    event_engine: Any = field(default=None) # 延迟初始化以避免循环
    
    # -----------------------------------------------------
    # 场景化重构组件 (Issue #26)
    # -----------------------------------------------------
    space: Optional[Any] = None  # CombatSpace 实例
    
    # 系统管理器与日志
    system_manager: Optional[Any] = None
    logger: Optional[Any] = None

    # 上下文管理器状态
    _token: Optional[Any] = field(default=None, init=False, repr=False)

    def __post_init__(self):
        # 延迟导入 EventEngine 以规避可能的循环
        from core.context import EventEngine
        if self.event_engine is None:
            self.event_engine = EventEngine()
            
        # 自动初始化战场空间
        from core.combat_space import CombatSpace
        if self.space is None:
            self.space = CombatSpace()

    def __enter__(self) -> 'SimulationContext':
        self._token = _current_context.set(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._token:
            _current_context.reset(self._token)
            self._token = None
        self.reset()

    def advance_frame(self) -> None:
        self.current_frame += 1
        # 驱动场景物理更新
        if self.space:
            self.space.update()

    def get_system(self, cls_or_name: Any) -> Optional[Any]:
        if self.system_manager:
            return self.system_manager.get_system(cls_or_name)
        return None

    def reset(self) -> None:
        self.current_frame = 0
        self.global_move_dist = 0.0
        self.global_vertical_dist = 0.0
        if self.event_engine:
            self.event_engine.clear()
        if self.space:
            # 此处应有 Space 的重置逻辑
            pass
        if self.logger:
            self.logger.log_info("Context Reset")

    def take_snapshot(self) -> dict:
        """[核心] 抓取当前帧全场景状态快照"""
        snapshot = {
            "frame": self.current_frame,
            "global": {
                "move_dist": round(self.global_move_dist, 3),
                "vertical_dist": round(self.global_vertical_dist, 3)
            },
            "entities": []
        }
        
        if self.space:
            # 遍历所有阵营的实体
            from core.entities.base_entity import Faction
            for faction in Faction:
                for entity in self.space._entities.get(faction, []):
                    snapshot["entities"].append(entity.export_state())
                    
        return snapshot

# ---------------------------------------------------------
# Event Engine (Instance-based)
# ---------------------------------------------------------
class EventEngine:
    def __init__(self, parent: Optional['EventEngine'] = None):
        self._handlers: Dict[Any, List[Any]] = {}
        self.parent = parent

    def subscribe(self, event_type: Any, handler: Any) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: Any, handler: Any) -> None:
        if event_type in self._handlers:
            if handler in self._handlers[event_type]:
                self._handlers[event_type].remove(handler)
            if not self._handlers[event_type]:
                del self._handlers[event_type]

    def publish(self, event: Any) -> None:
        if hasattr(event, 'event_type'):
            handlers = self._handlers.get(event.event_type, []).copy()
            for handler in handlers:
                if getattr(event, 'cancelled', False): return
                handler.handle_event(event)
        if getattr(event, 'propagation_stopped', False): return
        if self.parent: self.parent.publish(event)

    def clear(self) -> None:
        self._handlers.clear()

_current_context: ContextVar[Optional[SimulationContext]] = ContextVar("current_simulation_context", default=None)

def get_context() -> SimulationContext:
    ctx = _current_context.get()
    if ctx is None: raise RuntimeError("No active SimulationContext found.")
    return ctx

def set_context(ctx: SimulationContext) -> None:
    _current_context.set(ctx)

def create_context() -> SimulationContext:
    from core.systems.manager import SystemManager
    from core.systems.damage_system import DamageSystem
    from core.systems.reaction_system import ReactionSystem
    from core.systems.health_system import HealthSystem
    from core.systems.shield_system import ShieldSystem
    from core.systems.energy_system import EnergySystem
    from core.systems.natlan_system import NatlanSystem
    from core.registry import initialize_registry
    from core.logger import SimulationLogger
    
    initialize_registry()
    ctx = SimulationContext()
    set_context(ctx)
    ctx.logger = SimulationLogger()
    ctx.system_manager = SystemManager(ctx)
    ctx.system_manager.add_system(DamageSystem)
    ctx.system_manager.add_system(ReactionSystem)
    ctx.system_manager.add_system(HealthSystem)
    ctx.system_manager.add_system(ShieldSystem)
    ctx.system_manager.add_system(EnergySystem)
    ctx.system_manager.add_system(NatlanSystem)
    return ctx