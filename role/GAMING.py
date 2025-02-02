from .role import Role
from DataRequest import DR
from DataProcessing import DataProcessing as DP

class GaMing(Role):
    ID = 1
    def __init__(self,level):
        super().__init__(self.ID)
        self.level = level
        SQL = "SELECT * FROM `role_stats` WHERE role_id = {}".format(self.ID)
        self.data = DR.read_data(SQL)[0]
        self.name = self.data[1]
        self.element = self.data[2]

        
    def get_data(self):
        l = DP.level(self.level)
        self.attributeData["生命值"] = self.data[3+l]
        self.attributeData["攻击力"] = self.data[11+l]
        self.attributeData["防御力"] = self.data[19+l]
        t = DP.attributeId(self.data[-1])
        if t != "元素伤害加成":
            self.attributeData[t] = self.data[27+l]
        else:
            self.attributeData[t][self.element] = self.data[27+l]

    def get_name(self):
        return self.name

    def get_element(self):
        return self.element
    
    def attributePanel(self):
        pass