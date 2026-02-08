from typing import Dict
from core.effect.BaseEffect import Effect

class ChiliPepperEffect(Effect):
    """
    绝云朝天椒：拾取辣椒后获得的攻击力加成效果。
    """
    def __init__(self, owner):
        # 持续 10 秒
        super().__init__(owner, 10 * 60)
        self.name = "绝云朝天椒"
        self.atk_boost_percent = 10.0 # 10% 攻击力提升

    def get_additional_stats(self) -> Dict[str, float]:
        """为角色动态提供攻击力百分比加成"""
        if not self.is_active:
            return {}
        return {"攻击力%": self.atk_boost_percent}

class PyronadoBuffEffect(Effect):
    """
    命座6效果：旋火轮持续期间，全队获得 15% 火伤加成。
    """
    def __init__(self, owner):
        super().__init__(owner, float('inf'))
        self.name = "大龙卷旋火轮"
        self.pyro_bonus = 15.0

    def get_additional_stats(self) -> Dict[str, float]:
        return {"火元素伤害加成": self.pyro_bonus}