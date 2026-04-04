"""元素能量管理类。"""


class ElementalEnergy:
    """
    元素能量管理器。

    管理角色的元素能量状态，包括当前能量、能量上限和元素类型。
    """

    def __init__(self, element: str = "无", max_energy: int = 0) -> None:
        """初始化元素能量。

        Args:
            element: 元素类型（火/水/雷/冰/风/岩/草）
            max_energy: 能量上限
        """
        self.element: str = element
        self.max_energy: int = max_energy
        self.current_energy: float = float(max_energy)

    def is_full(self) -> bool:
        """检查能量是否已满。"""
        return self.current_energy >= self.max_energy

    def is_empty(self) -> bool:
        """检查能量是否为空。"""
        return self.current_energy <= 0

    def clear(self) -> None:
        """清空能量。"""
        self.current_energy = 0.0

    def fill(self) -> None:
        """填满能量。"""
        self.current_energy = float(self.max_energy)

    def gain(self, amount: float) -> float:
        """恢复能量。

        Args:
            amount: 恢复的能量值

        Returns:
            实际恢复的能量值
        """
        old_energy = self.current_energy
        self.current_energy = min(self.max_energy, self.current_energy + amount)
        return self.current_energy - old_energy

    def get_progress(self) -> float:
        """获取能量进度百分比（0.0 ~ 1.0）。"""
        if self.max_energy == 0:
            return 0.0
        return self.current_energy / self.max_energy

    def get_remaining(self) -> float:
        """获取距离满能量还需多少。"""
        return max(0.0, self.max_energy - self.current_energy)
