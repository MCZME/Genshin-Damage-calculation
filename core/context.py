from __future__ import annotations
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

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

    # 核心组件
    event_engine: EventEngine | None = field(default=None)
    space: CombatSpace | None = None
    system_manager: SystemManager | None = None
    logger: SimulationLogger | None = None

    # 内部状态管理
    _modifier_id_counter: int = field(default=0, init=False)
    _instance_id_counter: int = field(default=0, init=False)
    _seen_entities: set[int] = field(default_factory=set, init=False)
    _token: Any | None = field(default=None, init=False, repr=False)

    def get_next_modifier_id(self) -> int:
        """获取下一个全局唯一的修饰符 ID。"""
        self._modifier_id_counter += 1
        return self._modifier_id_counter

    def get_next_instance_id(self) -> int:
        """获取下一个全局唯一的效果实例 ID。"""
        self._instance_id_counter += 1
        return self._instance_id_counter

    def __post_init__(self) -> None:
        """完成上下文组件的自动初始化。"""
        if self.event_engine is None:
            self.event_engine = EventEngine()

        if self.space is None:
            from core.combat_space import CombatSpace
            self.space = CombatSpace()

    def __enter__(self) -> SimulationContext:
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
        """推进全局时间轴一帧，并驱动物理空间更新。
        在推进前会清空上一帧的业务事件缓冲区。
        """
        if self.event_engine:
            self.event_engine.clear_frame_events()
            
        self.current_frame += 1
        if self.space:
            self.space.on_frame_update()

    def get_system(self, cls_or_name: str | type) -> Any | None:
        """获取已挂载的仿真系统实例。

        Args:
            cls_or_name: 系统的类定义或字符串名称。

        Returns:
            Any | None: 系统实例，若未找到则返回 None。
        """
        if self.system_manager:
            return self.system_manager.get_system(cls_or_name)
        return None

    def reset(self) -> None:
        """重置上下文状态至初始点，清除所有实体与缓存。"""
        self.current_frame = 0
        self.global_move_dist = 0.0
        self.global_vertical_dist = 0.0
        self._seen_entities.clear()
        if self.event_engine:
            self.event_engine.clear()

        # 记录重置日志
        if self.logger:
            self.logger.log_info("Context Reset", sender="Context")

    def take_snapshot(self) -> dict[str, Any]:
        """抓取当前仿真场景的全量状态快照 (V3.0 自动化登记增强版)。"""
        snapshot: dict[str, Any] = {
            "frame": self.current_frame,
            "global": {
                "move_dist": round(self.global_move_dist, 3),
                "vertical_dist": round(self.global_vertical_dist, 3),
            },
            "team": [],
            "entities": [],
            "events": [],
            "entities_meta": [] # 存放首次发现的实体静态数据
        }

        if self.space:
            from core.entities.base_entity import Faction
            
            # 统一处理所有实体
            all_current_entities: list[Any] = []
            if self.space.team:
                all_current_entities.extend(self.space.team.get_members())
            
            for faction in Faction:
                all_current_entities.extend(self.space._entities.get(faction, []))

            for entity in all_current_entities:
                # 1. 发现新实体，导出元数据进行登记
                eid = int(entity.entity_id)
                is_new = eid not in self._seen_entities
                meta = None
                if is_new:
                    meta = entity.export_static_data()
                    snapshot["entities_meta"].append(meta)
                    self._seen_entities.add(eid)

                # 2. 导出状态
                state = entity.export_state()
                
                # 判定实体类型 (优先从 meta 获取，否则兜底)
                etype = meta["entity_type"] if meta else getattr(entity, "_db_entity_type", "UNKNOWN")
                if is_new:
                    entity._db_entity_type = etype # 缓存类型避免重复导出 meta

                if etype == "CHARACTER":
                    snapshot["team"].append(state)
                else:
                    snapshot["entities"].append(state)

        if self.event_engine:
            snapshot["events"] = list(self.event_engine.current_frame_events)

        return snapshot


# ---------------------------------------------------------
# Event Engine (Instance-based)
# ---------------------------------------------------------


class EventEngine:
    """基于实例的事件驱动引擎。

    支持在特定的 SimulationContext 内进行事件订阅、取消订阅与发布。
    支持业务事件的帧内缓冲，以便于战果复盘持久化。
    """

    def __init__(self, parent: EventEngine | None = None):
        """初始化事件引擎。

        Args:
            parent: 可选的父引擎，若存在，事件将向上冒泡发布。
        """
        self._handlers: dict[Any, list[Any]] = {}
        self.parent = parent
        # 缓存当前帧的关键业务事件，供快照导出使用
        self.current_frame_events: list[dict[str, Any]] = []

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

    def publish(self, event: Any) -> None:
        """发布一个事件，触发所有对应的处理程序。
        具有“审计价值”的事件将被自动拦截并存入帧缓冲区。
        """
        # 拦截关键业务事件 (V2.5 增强版：包含生命周期与跳变事件)
        from core.event import EventType
        review_targets = {
            EventType.AFTER_DAMAGE, 
            EventType.AFTER_ELEMENTAL_REACTION, 
            EventType.AFTER_HEAL,
            EventType.AFTER_ENERGY_CHANGE,
            EventType.AFTER_HEALTH_CHANGE,
            EventType.ON_MODIFIER_ADDED,
            EventType.ON_MODIFIER_REMOVED,
            EventType.ON_EFFECT_ADDED,
            EventType.ON_EFFECT_REMOVED
        }
        
        if hasattr(event, "event_type") and event.event_type in review_targets:
            self.current_frame_events.append({
                "type": event.event_type.name,
                "frame": event.frame,
                "source_id": getattr(event.source, "entity_id", None),
                "source_name": getattr(event.source, "name", "Unknown"),
                "payload": event.data 
            })

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

    def clear_frame_events(self) -> None:
        """清空当前帧的事件缓冲区。"""
        self.current_frame_events.clear()

    def clear(self) -> None:
        """清除所有订阅记录与事件缓冲。"""
        self._handlers.clear()
        self.current_frame_events.clear()


# ---------------------------------------------------------
# Context Management Utilities
# ---------------------------------------------------------

_current_context: ContextVar[SimulationContext | None] = ContextVar(
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
    from core.systems.damage import DamageSystem
    from core.systems.energy_system import EnergySystem
    from core.systems.health_system import HealthSystem
    from core.systems.manager import SystemManager
    from core.systems.moonsign_system import MoonsignSystem
    from core.systems.natlan_system import NatlanSystem
    from core.systems.reaction import ReactionSystem
    from core.systems.shield_system import ShieldSystem
    from core.systems.resonance_system import ResonanceSystem
    from core.systems.lunar_system import LunarReactionSystem
    from core.systems.rule_system import RuleSystem

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
    ctx.system_manager.add_system(MoonsignSystem)
    ctx.system_manager.add_system(LunarReactionSystem)
    ctx.system_manager.add_system(RuleSystem)

    return ctx
