def level(level):
    Level = [1,20,40,50,60,70,80,90]
    for i in Level:
        if level <= i:
            return Level.index(i)
    return 0

def attributeId(attributeId):
    AttributeId = {1:'暴击率',2:'暴击伤害',3:'生命值',4:'防御力',5:'攻击力',6:'元素精通',7:'元素充能效率',8:'治疗加成',
                9:'元素伤害加成',10:'受治疗加成',11:'生命值%',12:'攻击力%',13:'防御力%'}
    return AttributeId[attributeId]