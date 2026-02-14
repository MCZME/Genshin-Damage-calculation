import importlib
import pkgutil
import sys
from typing import Dict, Type, Any

# ---------------------------------------------------------
# 全局注册表
# ---------------------------------------------------------
CharacterClassMap: Dict[str, Type[Any]] = {}
WeaponClassMap: Dict[str, Type[Any]] = {}
ArtifactSetMap: Dict[str, Type[Any]] = {}


# ---------------------------------------------------------
# 注册装饰器
# ---------------------------------------------------------
def register_character(char_name: str):
    """
    角色注册装饰器。
    用法: @register_character("夏洛蒂")
    """

    def decorator(cls: Type[Any]):
        CharacterClassMap[char_name] = cls
        cls.NAME = char_name
        return cls

    return decorator


def register_weapon(weapon_name: str, weapon_type: str = None):
    """
    武器注册装饰器。
    """

    def decorator(cls: Type[Any]):
        WeaponClassMap[weapon_name] = cls
        if weapon_type:
            cls.weapon_type = weapon_type
        return cls

    return decorator


def register_artifact_set(set_name: str):
    """
    圣遗物套装注册装饰器。
    """

    def decorator(cls: Type[Any]):
        ArtifactSetMap[set_name] = cls
        return cls

    return decorator


# ---------------------------------------------------------
# 动态发现逻辑
# ---------------------------------------------------------
_initialized = False


def discover_modules(package_name: str):
    """
    递归扫描并导入指定包下的所有子模块，从而触发装饰器注册。
    """
    try:
        package = importlib.import_module(package_name)
    except ImportError as e:
        print(f"Registry: Root package {package_name} not found: {e}")
        return

    if not hasattr(package, "__path__"):
        return

    # walk_packages 能够递归扫描子包
    for loader, module_name, is_pkg in pkgutil.walk_packages(
        package.__path__, package.__name__ + "."
    ):
        try:
            # 如果是子包，继续递归导入其 __init__
            # 如果是模块 (如 char.py)，导入它以激活装饰器
            if module_name not in sys.modules:
                importlib.import_module(module_name)
        except Exception as e:
            print(f"Registry: Failed to load module {module_name}: {e}")


def initialize_registry():
    """
    一键初始化所有注册表。具备防重入保护。
    """
    global _initialized
    if _initialized:
        return

    # 扫描核心包
    discover_modules("character")
    discover_modules("weapon")
    discover_modules("artifact.sets")

    # 同步更新武器分类表
    try:
        from weapon import update_weapon_table

        update_weapon_table()
    except Exception:
        pass

    _initialized = True
    print(f"Registry initialized. Characters: {list(CharacterClassMap.keys())}")
