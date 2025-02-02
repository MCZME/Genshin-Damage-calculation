

class Role:
    def __init__(self,id):
        self.id = id
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

    def attributePanel(self):
        pass

    def elementalSkill(self):
        return 0

    def elementalBurst(self):
        return 0
    
    def uniqueAbility(self):
        pass

    def constellation(self):
        pass