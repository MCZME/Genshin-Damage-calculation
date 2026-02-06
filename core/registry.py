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

def register_weapon(weapon_name: str, weapon_type: str = None):
    """
    武器注册装饰器。
    用法:
        @register_weapon("祭礼剑", "单手剑")
        class SacrificialSword(Weapon): ...
    """
    def decorator(cls: Type[Any]):
        WeaponClassMap[weapon_name] = cls
        if weapon_type:
            # 可以在这里存储类型信息，或者直接给类打标签
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
            # 记录错误但不崩溃，允许渐进式重构。
            print(f"Skipping module {module_name}: {e}")

def initialize_registry():
    """
    一键初始化所有注册表。
    """
    discover_modules("character")
    discover_modules("weapon")
    discover_modules("artifact.sets")
    
    # 同步更新武器分类表 (用于 UI)
    from weapon import update_weapon_table
    update_weapon_table()
