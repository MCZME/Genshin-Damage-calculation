from DataRequest import DR
from core.elementalReaction.ElementalAura import ElementalAura

class Target:
    def __init__(self, id, level):
        self.id = id
        self.level = level
        self.get_data()

        self.current_frame = 0
        self.defense = level*5 + 500
        self.aura = ElementalAura()
        self.effects = []

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
        return self.aura.getElementalAura()
    
    def setElementalAura(self, elementalAura):
        self.aura.setElementalAura(elementalAura)

    def apply_elemental_aura(self, damage):
        return self.aura.apply_elemental_aura(damage)

    def add_effect(self, effect):
        self.effects.append(effect)

    def remove_effect(self, effect):
        self.effects.remove(effect)

    def update(self):
        self.current_frame += 1
        # 更新元素衰减状态
        self.aura.update()
        
        # 更新其他效果状态
        removed_effects = []
        for effect in self.effects:
            effect.update()
            if not effect.is_active:
                removed_effects.append(effect)
        for effect in removed_effects:
            self.effects.remove(effect)

    def clear(self):
        self.aura.clear()
        self.effects.clear()
        self.current_frame = 0
