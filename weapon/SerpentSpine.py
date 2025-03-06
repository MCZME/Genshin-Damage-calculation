from .weapon import Weapon


class SerpentSpine(Weapon):
    ID = 1
    def __init__(self,character,level,lv):
        super().__init__(character,self.ID,level,lv)
        self.skill_param = [6,7,8,9,10]

    def skill(self):
        attributePanel = self.character.attributePanel
        attributePanel['伤害加成'] += 5*self.skill_param[self.lv-1]
