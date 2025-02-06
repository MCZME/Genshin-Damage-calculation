from DataRequest import DR
from DataProcessing import DataProcessing as DP

class Role:
    def __init__(self,id=1,level=1):
        self.id = id
        self.level = level
        self.attributeData ={
            "生命值" : 0,
            "攻击力": 0,
            "防御力": 0,
            "元素精通" : 0,
            "暴击率" : 5,
            "暴击伤害" : 50,
            "治疗加成" : 0,
            "受治疗加成" : 0,
            "元素充能效率" : 100,
            "生命值%" : 0,
            "攻击力%": 0,
            "防御力%": 0,
            "元素伤害加成" : {
                "火": 0,
                "水": 0,
                "雷": 0,
                "冰": 0,
                "岩": 0,
                "风": 0,
                "草": 0,
                "物理": 0
            }
        }

        SQL = "SELECT * FROM `role_stats` WHERE role_id = {}".format(self.id)
        self.data = DR.read_data(SQL)[0]
        self.name = self.data[1]
        self.element = self.data[2]
        self.get_data(level)

    def get_data(self,level):
        l = DP.level(level)
        self.attributeData["生命值"] = self.data[5+l]
        self.attributeData["攻击力"] = self.data[13+l]
        self.attributeData["防御力"] = self.data[21+l]
        t = DP.attributeId(self.data[-1])
        if t != "元素伤害加成":
            self.attributeData[t] = self.data[29+l]
        else:
            self.attributeData[t][self.element] = self.data[29+l]

    def attributePanel(self):
        return self.attributeData

    def elementalSkill(self):
        return 0

    def elementalBurst(self):
        return 0
    
    def uniqueAbility(self):
        pass

    def constellation(self):
        pass

    def to_dict(self):
        return {
            'id':self.id,
            'level':self.level
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(data['level'])
    