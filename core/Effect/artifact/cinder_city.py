from typing import Any, Dict
from core.effect.base import BaseEffect

class CinderCityEffect(BaseEffect):
    """烬城勇者绘卷套装效果"""
    def __init__(self, owner: Any, source_char: Any):
        super().__init__(owner, "烬城勇者绘卷", duration=12*60)
        self.source_char = source_char
        self.stacks: Dict[str, int] = {}
        self.nightsoul_stacks: Dict[str, int] = {}
        self.bonus = 12
        self.nightsoul_bonus = 28

    def on_apply(self):
        # 初始应用逻辑由外部调用触发
        pass

    def update_elements(self, elements: list):
        """外部调用：触发特定元素的加成"""
        for e in elements:
            # 转换名称 (冻 -> 冰, 激 -> 草)
            real_e = {'冻': '冰', '激': '草'}.get(e, e)
            
            # 基础加成
            if real_e not in self.stacks:
                self.owner.attribute_panel[real_e + '元素伤害加成'] += self.bonus
            self.stacks[real_e] = 12*60
            
            # 夜魂加成
            if getattr(self.source_char, 'Nightsoul_Blessing', False):
                if real_e not in self.nightsoul_stacks:
                    self.owner.attribute_panel[real_e + '元素伤害加成'] += self.nightsoul_bonus
                self.nightsoul_stacks[real_e] = 20*60

    def on_tick(self, target: Any):
        # 处理普通层数过期
        to_remove = []
        for e in self.stacks:
            self.stacks[e] -= 1
            if self.stacks[e] <= 0: to_remove.append(e)
        for e in to_remove:
            self.owner.attribute_panel[e + '元素伤害加成'] -= self.bonus
            del self.stacks[e]

        # 处理夜魂层数过期
        to_remove_ns = []
        for e in self.nightsoul_stacks:
            self.nightsoul_stacks[e] -= 1
            if self.nightsoul_stacks[e] <= 0: to_remove_ns.append(e)
        for e in to_remove_ns:
            self.owner.attribute_panel[e + '元素伤害加成'] -= self.nightsoul_bonus
            del self.nightsoul_stacks[e]

        if not self.stacks and not self.nightsoul_stacks:
            self.remove()
