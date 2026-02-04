import os
import importlib
import pkgutil
from typing import Dict, Type, Any

# ---------------------------------------------------------
# 全局注册表
# ---------------------------------------------------------
CharacterClassMap: Dict[int, Type[Any]] = {}
WeaponClassMap: Dict[str, Type[Any]] = {}
ArtifactSetMap: Dict[str, Type[Any]] = {}

# ---------------------------------------------------------
# 注册装饰器
# ---------------------------------------------------------
def register_character(char_id: int):
    """
    角色注册装饰器。
    用法:
        @register_character(10000001)
        class MyCharacter(Character): ...
    """
    def decorator(cls: Type[Any]):
        CharacterClassMap[char_id] = cls
        # 顺便设置类的 ID 属性以保持兼容
        cls.ID = char_id 
        return cls
    return decorator

def register_weapon(weapon_name: str):
    """
    武器注册装饰器。
    用法:
        @register_weapon("祭礼剑")
        class SacrificialSword(Weapon): ...
    """
    def decorator(cls: Type[Any]):
        WeaponClassMap[weapon_name] = cls
        return cls
    return decorator

# ---------------------------------------------------------
# 动态发现逻辑
# ---------------------------------------------------------
def discover_modules(package_name: str):
    """
    递归扫描并导入指定包下的所有子模块，从而触发装饰器注册。
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
        except Exception as e:
            # 这里记录错误但继续扫描，防止单个文件报错导致全盘失效
            from core.logger import get_emulation_logger
            get_emulation_logger().log_error(f"无法发现模块 {module_name}: {e}")

def initialize_registry():
    """
    一键初始化所有注册表。
    """
    discover_modules("character")
    discover_modules("weapon")
    # 如果圣遗物也需要动态注册
    # discover_modules("artifact")
