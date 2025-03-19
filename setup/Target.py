from DataRequest import DR
from setup.ElementalReaction import ReactionMMap

class Target:
    def __init__(self, id, level):
        self.id = id
        self.level = level
        self.get_data()

        self.current_frame = 0
        self.defense = level*5 + 500
        self.elementalAura = []
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
        return self.elementalAura
    
    def setElementalAura(self, elementalAura):
        self.elementalAura = elementalAura

    def apply_elemental_aura(self, element):
        trigger_element, trigger_amount = element 
        
        # 先处理元素反应（如果有附着元素存在）
        if len(self.elementalAura)>0:
            base_element = self.elementalAura[0]['element'] 
            
            # 检查是否可以发生反应
            reaction_type = ReactionMMap.get((trigger_element, base_element), None)
            if reaction_type and trigger_amount > 0:
                base_current = self.elementalAura[0]['current_amount']
                trigger_actual = trigger_amount  # 后手元素不产生附着时无20%损耗
                
                # 确定消耗比例
                ratio = self._get_element_ratio(trigger_element, base_element)
                
                # 计算实际消耗
                if trigger_actual/ratio[0] > base_current/ratio[1]:
                    self.elementalAura.clear()
                    return base_element
                else:
                    actual_base_consumed = trigger_actual*ratio[0]/ratio[1]

                # 更新元素量
                self.elementalAura[0]['current_amount'] -= actual_base_consumed
                return base_element
        if trigger_element not in {'风', '岩'}:
            self._attach_new_element(trigger_element, trigger_amount)
        return None

    def _get_element_ratio(self, trigger, base):
        """获取元素消耗比例 (trigger:base)"""
        if (trigger, base) in [('水', '火'), ('火', '冰')]:
            return (1, 2) 
        if (trigger, base) in [('火', '水'), ('冰', '火')]:
            return (2, 1)  
        if trigger in {'风','岩'} and base in {'水','雷','冰','火'}:
            return (2, 1) 
        return (1, 1)

    def _attach_new_element(self, element_type, applied_amount):
        """处理新元素附着"""
        existing_aura = next((a for a in self.elementalAura if a['element'] == element_type), None)
        duration = 7 + applied_amount * 2.5

        if existing_aura:
            new_applied = applied_amount*0.8
            if new_applied > existing_aura['current_amount']:
                existing_aura.update({
                    'initial_amount': new_applied,
                    'current_amount': new_applied,
                })
        else:   
            self.elementalAura.append({
                'element': element_type,
                'initial_amount': applied_amount*0.8,
                'current_amount': applied_amount*0.8,
                'decay_rate': applied_amount*0.8 / duration
            })

    def add_effect(self, effect):
        self.effects.append(effect)

    def remove_effect(self, effect):
        self.effects.remove(effect)

    def update(self):
        self.current_frame += 1
        # 更新元素衰减状态
        for aura in self.elementalAura:
            # 按帧衰减（每秒60帧）
            aura['current_amount'] -= aura['decay_rate'] / 60
            # 清除已衰减完毕的元素
            if aura['current_amount'] <= 0:
                self.elementalAura.remove(aura)
        
        # 更新其他效果状态
        for effect in self.effects:
            effect.update(self)
