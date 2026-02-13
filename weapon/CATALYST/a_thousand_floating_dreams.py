from core.team import Team

import core.tool as T
from weapon.weapon import Weapon
from core.registry import register_weapon

@register_weapon("千夜浮梦", "法器")
class AThousandFloatingDreams(Weapon):
    ID =207
    def __init__(self, character, level=1, lv=1):
        super().__init__(character, AThousandFloatingDreams.ID, level, lv)
        self.same = 0
        self.different = 0
        self.damage_bonus = [10,14,18,22,26]
        self.em_bonus_0 = [32,40,48,56,64]
        self.em_bonus_1 = [40,42,44,46,48]

    def skill(self):
        for c in Team.team:
            if c != self.character:
                c.attribute_data["元素精通"] += self.em_bonus_1[self.lv-1]
    
    def getElementNum(self):
        self.same = 0
        self.different = 0
        for c in Team.team:
            if c != self.character:
                if c.element != self.character.element:
                    self.different += 1
                else:
                    self.same += 1

    def applyEffect(self):
        if self.same != 0:
            self.character.attribute_data["元素精通"] += self.em_bonus_0[self.lv-1] * self.same
        if self.different != 0:
            self.character.attribute_data[self.character.element + "元素伤害加成"] += self.damage_bonus[self.lv-1] * self.different

    def removeEffect(self):
        if self.same != 0:
            self.character.attribute_data["元素精通"] -= self.em_bonus_0[self.lv-1] * self.same
        if self.different != 0:
            self.character.attribute_data[self.character.element + "元素伤害加成"] -= self.damage_bonus[self.lv-1] * self.different

    def update(self, target):
        if T.get_current_time() % 60 == 1:
            self.removeEffect()
            self.getElementNum()
            self.applyEffect()
