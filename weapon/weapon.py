from DataRequest import DR
from character.character import Character
import core.Tool as T

class Weapon:
    def __init__(self,character:Character,id=1,level=1,lv=1):
        self.character = character
        self.id = id
        self.level = level
        self.lv = lv
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
            "火元素伤害加成": 0,
            "水元素伤害加成": 0,
            "雷元素伤害加成": 0,
            "冰元素伤害加成": 0,
            "岩元素伤害加成": 0,
            "风元素伤害加成": 0,
            "草元素伤害加成": 0,
            "物理伤害加成": 0
        }

        SQL = "SELECT * FROM `weapon_stats` WHERE w_id = {}".format(self.id)
        self.stats = DR.read_data(SQL)[0]
        self.name = self.stats[1]
        self.damage = self.stats[2]
        self.get_data(level)

    def get_data(self,level):
        l = T.level(level)
        self.attributeData["攻击力"] = self.stats[4+l]
        t = T.attributeId(self.stats[-1])
        self.attributeData[t] = self.stats[12+l]

    def updatePanel(self):
        attributePanel = self.character.attributePanel
        for i in self.attributeData:
            attributePanel[i] += self.attributeData[i]

    def skill(self):
        ...

    def update(self,target):
        ...

    def to_dict(self):
        return {
            'id': self.id,
            'level': self.level,
            'lv': self.lv
        }
