from typing import Any, Dict, Type, TypeVar
from core.entities.base_entity import BaseEntity
from core.context import get_context

T = TypeVar("T", bound=BaseEntity)

class EntityFactory:
    """
    实体工厂。
    统一实体的创建入口，负责自动注入 Context 并处理注册。
    """
    
    # 用于未来的池化管理
    _pool: Dict[str, Any] = {}

    @staticmethod
    def create_entity(cls: Type[T], *args: Any, **kwargs: Any) -> T:
        """
        创建一个实体并自动应用。
        
        Args:
            cls: 实体类。
            *args, **kwargs: 传递给实体构造函数的参数。
        """
        # 1. 尝试从 kwargs 获取 context，否则自动获取
        ctx = kwargs.get("context")
        if not ctx:
            try:
                ctx = get_context()
                kwargs["context"] = ctx
            except RuntimeError:
                pass
        
        # 2. 实例化
        instance = cls(*args, **kwargs)
        
        # 3. 自动应用到环境 (加入 Team)
        instance.apply()
        
        return instance

    @staticmethod
    def spawn_energy(num: int, character: Any, element_energy: Any, is_fixed: bool = False, is_alone: bool = False, time: int = 40) -> None:
        """
        统一的能量产生接口。
        
        Args:
            num: 产生数量（或球数）。
            character: 目标角色。
            element_energy: 元素类型与基础值。
            is_fixed: 是否为固定回能。
            is_alone: 是否为独立回能。
            time: 延迟帧数。如果为 0，则立即触发回能事件。
        """
        if time != 0:
            from core.entities.energy import EnergyDropsObject
            for _ in range(num):
                EntityFactory.create_entity(EnergyDropsObject, character, element_energy, life_frame=time)
        else:
            from core.event import EnergyChargeEvent
            from core.tool import get_current_time
            ctx = get_context()
            energy_event = EnergyChargeEvent(character, element_energy, get_current_time(),
                                            is_fixed=is_fixed, is_alone=is_alone)
            ctx.event_engine.publish(energy_event)
