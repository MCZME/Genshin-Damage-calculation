# ---------------------------------------------------------
# 兼容性代理 (Backward Compatibility Proxy)
# ---------------------------------------------------------
# 该文件已被 core/registry.py 取代。
# 为了不破坏现有代码，我们将新的注册表导出到这里。

from core.registry import CharacterClassMap, WeaponClassMap, initialize_registry

# 注意：使用此模块前，建议先调用 initialize_registry() 确保所有模块已加载。
# 目前为了兼容，如果在 import 时 Map 还是空的，说明动态扫描尚未执行。
