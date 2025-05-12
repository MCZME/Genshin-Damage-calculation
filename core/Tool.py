from core.Event import EnergyChargeEvent, EventBus


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

def GetCurrentTime():
    from Emulation import Emulation
    return Emulation.current_frame

reaction_coefficients = {
    1: 17.17, 2: 18.54, 3: 19.9, 4: 21.27, 5: 22.65, 6: 24.65, 7: 26.64, 8: 28.87, 9: 31.37, 10: 34.14,
    11: 37.2, 12: 40.66, 13: 44.45, 14: 48.56, 15: 53.75, 16: 59.08, 17: 64.42, 18: 69.72, 19: 75.12, 20: 80.58,
    21: 86.11, 22: 91.7, 23: 97.24, 24: 102.81, 25: 108.41, 26: 113.2, 27: 118.1, 28: 122.98, 29: 129.73, 30: 136.29,
    31: 142.67, 32: 149.03, 33: 155.42, 34: 161.83, 35: 169.11, 36: 176.52, 37: 184.07, 38: 191.71, 39: 199.56, 40: 207.38,
    41: 215.4, 42: 224.17, 43: 233.5, 44: 243.35, 45: 256.06, 46: 268.54, 47: 281.53, 48: 295.01, 49: 309.07, 50: 323.6,
    51: 336.76, 52: 350.53, 53: 364.48, 54: 378.62, 55: 398.6, 56: 416.4, 57: 434.39, 58: 452.57, 59: 471.43, 60: 490.48,
    61: 513.57, 62: 539.1, 63: 565.51, 64: 592.54, 65: 624.44, 66: 651.47, 67: 679.5, 68: 707.79, 69: 736.67, 70: 765.64,
    71: 794.77, 72: 824.68, 73: 851.16, 74: 877.74, 75: 914.23, 76: 946.75, 77: 979.41, 78: 1011.22, 79: 1044.79, 80: 1077.44,
    81: 1110.0, 82: 1142.98, 83: 1176.37, 84: 1210.18, 85: 1253.84, 86: 1288.95, 87: 1325.48, 88: 1363.46, 89: 1405.1, 90: 1446.85
}

def get_reaction_multiplier(level):
    return reaction_coefficients[level]

def summon_energy(num, character, element_energy, is_fixed=False, is_alone=False, time=40):
    from core.BaseObject import EnergyDropsObject
    if time != 0:
        for _ in range(num):
            EnergyDropsObject(character, element_energy, time, is_fixed, is_alone).apply()
    else:
        energy_event = EnergyChargeEvent(character, element_energy, GetCurrentTime(),
                                        is_fixed=is_fixed, is_alone=is_alone)
        EventBus.publish(energy_event)

def get_shield(name = None):
    from core.Team import Team
    from core.BaseObject import ShieldObject
    if name:
        shield = next((e for e in Team.active_objects if isinstance(e, ShieldObject) and e.name == name), None)
    else:
        shield = next((e for e in Team.active_objects if isinstance(e, ShieldObject)), None)
    return shield