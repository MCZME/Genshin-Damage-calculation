import pkgutil
import importlib
from typing import Dict, Type, Any, Callable, List, Optional

# --- 存储容器 ---
CharacterClassMap: Dict[str, Type[Any]] = {}
WeaponClassMap: Dict[str, Type[Any]] = {}
ArtifactSetMap: Dict[str, Type[Any]] = {}

# --- 注册装饰器 ---

def register_character(name: str) -> Callable[[Type[Any]], Type[Any]]:
    """注册角色类到全局映射。"""
    def wrapper(cls: Type[Any]) -> Type[Any]:
        CharacterClassMap[name] = cls
        return cls
    return wrapper

def register_weapon(name: str) -> Callable[[Type[Any]], Type[Any]]:
    """注册武器类到全局映射。"""
    def wrapper(cls: Type[Any]) -> Type[Any]:
        WeaponClassMap[name] = cls
        return cls
    return wrapper

def register_artifact_set(name: str) -> Callable[[Type[Any]], Type[Any]]:
    """注册圣遗物套装类到全局映射。"""
    def wrapper(cls: Type[Any]) -> Type[Any]:
        ArtifactSetMap[name] = cls
        return cls
    return wrapper

def import_submodules(package_name: str) -> None:
    """
    递归导入指定包下的所有子模块。
    """
    try:
        package = importlib.import_module(package_name)
    except ImportError:
        return

    if not hasattr(package, "__path__"):
        return

    for loader, module_name, is_pkg in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        try:
            importlib.import_module(module_name)
        except Exception:
            # 忽略导入失败的模块
            continue

def initialize_registry(weapon_type: Optional[str] = None) -> None:
    """
    初始化注册表：自动发现并加载所有业务组件。
    """
    from core.logger import get_emulation_logger
    
    global _initialized
    if globals().get('_initialized', False):
        return

    # 1. 扫描角色包
    import_submodules("character")
    
    # 2. 扫描武器包
    import_submodules("weapon")
    
    # 3. 扫描圣遗物包
    import_submodules("artifact.sets")

    get_emulation_logger().log_debug(
        f"Registry initialized. {len(CharacterClassMap)} characters loaded.", 
        sender="Registry"
    )
    
    # 初始化武器静态数据 (通过 db)
    try:
        from weapon import update_weapon_table
        update_weapon_table()
    except Exception:
        pass

    _initialized = True
