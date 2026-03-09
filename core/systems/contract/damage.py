from typing import Any, Dict, List, Optional, Tuple
from core.systems.contract.attack import AttackConfig
from core.mechanics.aura import Element


class Damage:
    """
    伤害行为载体。

    持有原始倍率、元素属性以及物理契约。
    数值结算由 DamageSystem 完成。
    """

    def __init__(
        self,
        element: Tuple[Element, float] = (Element.NONE, 1.0),
        damage_multiplier: Tuple[float, ...] = (0.0,),
        scaling_stat: Tuple[str, ...] = ("攻击力",),
        config: Optional[AttackConfig] = None,
        name: str = "Unknown Damage",
    ) -> None:
        """初始化伤害对象。"""
        self.element: Tuple[Element, float] = element
        # 严格赋值
        self.damage_multiplier = damage_multiplier
        self.scaling_stat = scaling_stat
        self.config: AttackConfig = config if config else AttackConfig()
        self.name: str = name

        # 运行时状态
        self.source: Any = None
        self.target: Any = None
        self.damage: float = 0.0
        self.is_crit: bool = False
        self.reaction_results: List[Any] = []
        self.data: Dict[str, Any] = {}

    def set_source(self, source: Any) -> None:
        """设置伤害来源实体。"""
        self.source = source

    def set_target(self, target: Any) -> None:
        """设置伤害的命中目标。"""
        self.target = target

    def set_scaling_stat(self, scaling_stat: Tuple[str, ...]) -> None:
        """修改伤害计算所依赖的属性向量。"""
        self.scaling_stat = scaling_stat

    def set_element(self, element: Element, element_u: float = 1.0) -> None:
        """修改伤害的元素属性。"""
        self.element = (element, element_u)

    def add_data(self, key: str, value: Any) -> None:
        """向伤害对象注入额外的运行时上下文数据。"""
        self.data[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """将伤害对象序列化为可持久化的字典。"""
        return {
            "name": self.name,
            "element": [self.element[0].name, self.element[1]],
            "multiplier": self.damage_multiplier,
            "scaling_stat": self.scaling_stat,
            "damage": self.damage,
            "is_crit": self.is_crit,
            "source": getattr(self.source, "name", "Unknown"),
            "target": getattr(self.target, "name", "Unknown"),
            "data": self.data # 包含审计链
        }
