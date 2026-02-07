from core.effect.common import TalentEffect, ConstellationEffect

class Talent_1(TalentEffect):
    """交叉火力：锅巴喷火距离提升"""
    def __init__(self):
        super().__init__("交叉火力", unlock_level=20)

class Talent_2(TalentEffect):
    """绝云朝天椒：拾取辣椒加攻"""
    def __init__(self):
        super().__init__("绝云朝天椒", unlock_level=60)

class C1(ConstellationEffect):
    def __init__(self):
        super().__init__("外酥里嫩", unlock_constellation=1)

class C3(ConstellationEffect):
    def __init__(self):
        super().__init__("武火急烹", unlock_constellation=3)
    def on_apply(self):
        if "burst" in self.character.skills:
            self.character.skills["burst"].lv = min(self.character.skills["burst"].lv + 3, 15)

class C5(ConstellationEffect):
    def __init__(self):
        super().__init__("锅巴凶猛", unlock_constellation=5)
    def on_apply(self):
        if "skill" in self.character.skills:
            self.character.skills["skill"].lv = min(self.character.skills["skill"].lv + 3, 15)
