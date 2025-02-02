from .weapon import Weapon
from DataRequest import DR
from DataProcessing import DataProcessing as DP

class SerpentSpine(Weapon):
    ID = 1
    def __init__(self,level):
        super().__init__(self.ID)
        self.level = level
        SQL = "SELECT * FROM `weapon_stats` WHERE w_id = {}".format(self.ID)
        self.stats = DR.read_data(SQL)[0]
        self.name = self.stats[1]
        self.damage = self.stats[2]

        l = DP.level(self.level)
        self.attributeData["攻击力"] = self.stats[3+l]
        t = DP.attributeId(self.stats[-1])
        self.attributeData[t] = self.stats[11+l]