from typing import Any, Dict, Optional
from weapon.weapon import Weapon
from core.registry import register_weapon

@register_weapon("无锋剑", "单手剑")
class DullBlade(Weapon):
    """
    无锋剑：没有任何特性的少年的剑。
    """
    ID = 2 # 对应原生数据 ID
    
    def __init__(self, character: Any, level: int = 1, lv: int = 1, base_data: Optional[Dict[str, Any]] = None):
        super().__init__(character, DullBlade.ID, level, lv, base_data)

    def skill(self) -> None:
        """无锋剑没有武器技能。"""
        pass
