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

    def skill(self):
        ...