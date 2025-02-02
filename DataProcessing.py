from DataRequest import DR

class DataProcessing:
    def __init__(self):
        ...

    @staticmethod
    def level(level):
        Level = [1,20,40,50,60,70,80,90]
        for i in Level:
            if level <= i:
                return Level.index(i)
        return 0
    
    @staticmethod
    def attributeId(attributeId):
        AttributeId = {1:'暴击率',2:'暴击伤害',3:'生命值',4:'防御力',5:'攻击力',6:'元素精通',7:'元素充能效率',8:'治疗加成',
                   9:'元素伤害加成',10:'受治疗加成',11:'生命值%',12:'攻击力%',13:'防御力%'}
        return AttributeId[attributeId]
    
    @staticmethod
    def element(element):
        Element = {1:'火',2:'水',3:'雷',4:'草',5:'冰',6:'岩',7:'物理',8:'风'}
        return Element[element]