from typing import Dict, List
from core.registry import WeaponClassMap

__all__ = ['weapon_table']

# weapon_table 将在 initialize_registry() 调用后通过此函数或属性获取最新数据
# 为了保持兼容性，我们保留这个变量，但它最初可能是空的。
# 在 UI 中使用时，请确保 initialize_registry() 已经执行。
weapon_table: Dict[str, List[str]] = {
    '长柄武器': [],
    '双手剑': [],
    '单手剑': [],
    '弓': [],
    '法器': []
}

def update_weapon_table():
    """根据 WeaponClassMap 更新 weapon_table 分类数据"""
    # 先清空
    for k in weapon_table:
        weapon_table[k] = []
    
    # 重新填充
    for name, cls in WeaponClassMap.items():
        w_type = getattr(cls, 'weapon_type', '未知武器')
        if w_type in weapon_table:
            if name not in weapon_table[w_type]:
                weapon_table[w_type].append(name)
        else:
            # 如果是新类型，动态添加
            if w_type not in weapon_table:
                weapon_table[w_type] = []
            weapon_table[w_type].append(name)

# 注意：initialize_registry() 会在 create_context() 中被调用。
# 我们需要确保在初始化后同步更新这个 table。