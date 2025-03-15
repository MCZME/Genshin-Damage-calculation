from DataRequest import DR

class Target:
    def __init__(self, id, level):
        """
        初始化目标对象
        
        参数:
        - id: 目标的唯一标识符
        - level: 目标的等级
        """
        self.id = id
        self.level = level
        self.get_data()
        self.elementalAura = ('物理',0)
        self.current_frame = 0

    def get_data(self):
        data = DR.read_data(f'SELECT * FROM `monster` WHERE `ID`={self.id}')
        self.name = data[0][1]
        self.element_resistance = {
            '火': data[0][2],
            '水': data[0][3],
            '雷': data[0][4],
            '草': data[0][5],
            '冰': data[0][6],
            '岩': data[0][7],
            '风': data[0][8],
            '物理': data[0][9]
        }
        self.current_resistance = self.element_resistance.copy()
    
    def get_current_resistance(self):
        return self.current_resistance
    
    def getElementalAura(self):
        return self.elementalAura
    
    def setElementalAura(self, elementalAura):
        self.elementalAura = elementalAura

    def update(self):
        self.current_frame += 1
