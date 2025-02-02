from DataRequest import DR
from DataProcessing import DataProcessing as DP

class Weapon:
    def __init__(self,id):
        self.id = id
        self.attributeData = {
            "攻击力": 0,
            "元素精通" : 0,
            "暴击率" : 0,
            "暴击伤害" : 0,
            "治疗加成" : 0,
            "受治疗加成" : 0,
            "元素充能效率" : 0,
            "生命值%" : 0,
            "攻击力%": 0,
            "防御力%": 0,
        }

        SQL = "SELECT * FROM `weapon_stats` WHERE w_id = {}".format(self.id)
        self.stats = DR.read_data(SQL)[0]
        self.name = self.stats[1]
        self.damage = self.stats[2]

    def get_data(self,level):
        l = DP.level(level)
        self.attributeData["攻击力"] = self.stats[3+l]
        t = DP.attributeId(self.stats[-1])
        self.attributeData[t] = self.stats[11+l]

    def skill(self):
        ...