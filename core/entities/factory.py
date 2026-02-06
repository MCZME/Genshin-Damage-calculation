from typing import Any, Dict, Type, TypeVar, Optional
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
    def spawn_energy(character: Any, element_energy: Any, time: int = 40) -> None:
        """工厂化的能量产生快捷方法。"""
        from core.entities.energy import EnergyDropsObject
        EntityFactory.create_entity(EnergyDropsObject, character, element_energy, life_frame=time)
