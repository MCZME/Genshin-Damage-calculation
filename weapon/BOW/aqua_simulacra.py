from weapon.weapon import Weapon
from core.registry import register_weapon

@register_weapon("若水", "弓")
class AquaSimulacra(Weapon):
    ID = 130
    def __init__(self, character, level=1, lv=1):
        super().__init__(character, AquaSimulacra.ID, level, lv)
        self.hp_bonus = [16,20,24,28,32]
        self.dmg_bonus = [20,25,30,35,40]

    def skill(self):
        # 默认周围存在敌人
        self.character.attribute_data["生命值%"] += self.hp_bonus[self.lv - 1]
        self.character.attribute_data["伤害加成"] += self.dmg_bonus[self.lv - 1]
