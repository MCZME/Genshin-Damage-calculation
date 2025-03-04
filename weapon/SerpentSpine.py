from .weapon import Weapon


class SerpentSpine(Weapon):
    ID = 1
    def __init__(self,character,level,lv):
        super().__init__(character,self.ID,level,lv)
