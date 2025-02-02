from .weapon import Weapon


class SerpentSpine(Weapon):
    ID = 1
    def __init__(self,level):
        super().__init__(self.ID)
        self.level = level
        self.get_data(level)


