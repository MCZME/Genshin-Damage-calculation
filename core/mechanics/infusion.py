from dataclasses import dataclass
from typing import List
from core.mechanics.aura import Element


@dataclass
class InfusionRecord:
    """单个附魔来源记录。"""

    element: Element
    priority: int
    source: str
    can_be_overridden: bool = True


class InfusionManager:
    """
    元素附魔管理器。
    采用三级优先级排序逻辑：强制性 > 显式优先级 > 元素权重(克制关系)。
    """

    # 元素相性权重：用于处理可覆盖附魔之间的竞争
    # 规则参考：水(4) > 火(3) > 冰(2) > 雷(1)
    ELEMENT_WEIGHT = {
        Element.HYDRO: 4,
        Element.PYRO: 3,
        Element.CRYO: 2,
        Element.ELECTRO: 1,
        Element.PHYSICAL: 0,
    }

    def __init__(self) -> None:
        self.active_infusions: List[InfusionRecord] = []

    def add_infusion(
        self,
        element: Element,
        priority: int,
        source: str,
        can_be_overridden: bool = True,
    ) -> None:
        """
        注册一个新的附魔源。
        """
        self.remove_infusion(source)

        record = InfusionRecord(element, priority, source, can_be_overridden)
        self.active_infusions.append(record)

        # 排序权重计算逻辑：
        # 1. 不可覆盖(True/False)
        # 2. 显式指定的 priority 数值
        # 3. 元素本身的相性权值
        self.active_infusions.sort(
            key=lambda x: (
                not x.can_be_overridden,
                x.priority,
                self.ELEMENT_WEIGHT.get(x.element, 0),
            ),
            reverse=True,
        )

    def remove_infusion(self, source: str) -> None:
        """
        注销特定来源的附魔。
        """
        self.active_infusions = [r for r in self.active_infusions if r.source != source]

    def get_current_element(self, base_element: Element = Element.PHYSICAL) -> Element:
        """
        计算当前的最终攻击元素。
        """
        if not self.active_infusions:
            return base_element

        # 返回最高优先级的附魔元素
        return self.active_infusions[0].element

    def clear(self) -> None:
        self.active_infusions.clear()
