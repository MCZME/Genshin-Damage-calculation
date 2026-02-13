
import core.tool as T
from weapon.weapon import Weapon
from core.registry import register_weapon

@register_weapon("风鹰剑", "单手剑")
class AquilaFavonia(Weapon):
    ID = 40
    def __init__(self, character, level=1, lv=1):
        super().__init__(character, AquilaFavonia.ID, level, lv)

    def get_data(self, level):
        l = T.get_ascension_index(level)
        self.attribute_data["攻击力"] = self.stats[4+l]
        self.attribute_data["物理伤害加成"] = self.stats[12+l]
    
    def skill(self):
        self.character.attribute_panel["攻击力%"] += 20
