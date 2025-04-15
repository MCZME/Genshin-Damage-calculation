from DataRequest import DR
from setup.Calculation.DamageCalculation import Damage, DamageType
from setup.ElementalReaction import ElementalReaction, ElementalReactionType, ReactionMMap
from setup.Event import DamageEvent, ElementalReactionEvent, EventBus
from setup.Tool import GetCurrentTime

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

    def apply_elemental_aura(self, damage):
        
        reaction_multiplier = None

        if len(self.elementalAura) > 0:
            if (damage.element[0] in ['水','雷'] and self.elementalAura[0]['element'] in ['火','雷'] and
                damage.element[0] != self.elementalAura[0]['element']):
                return self.apply_electro_charged_reaction(damage)
            reaction_multiplier = self.process_elemental_reactions(damage)

        # 若未触发反应且非风/岩，则附着新元素
        if not reaction_multiplier and damage.element[0] not in {'风', '岩'}:
            self._attach_new_element(damage.element[0], damage.element[1])

        return reaction_multiplier
    
    def process_elemental_reactions(self, damage):
        trigger_element, trigger_amount = damage.element
        base_element = self.elementalAura[0]['element'] 
            
        # 检查是否可以发生反应
        reaction_type = ReactionMMap.get((trigger_element, base_element), None)
        if reaction_type and trigger_amount > 0:
            base_current = self.elementalAura[0]['current_amount']
            trigger_actual = trigger_amount  # 后手元素不产生附着时无20%损耗
            
            # 确定消耗比例
            ratio = self._get_element_ratio(trigger_element, base_element)
            
            # 计算实际消耗
            actual_base_consumed = trigger_actual*ratio[1]/ratio[0]

            # 更新元素量
            self.elementalAura[0]['current_amount'] -= actual_base_consumed

            if self.elementalAura[0]['current_amount'] <= 0:
                self.elementalAura.pop(0)
            
            # 生成反应事件
            e = ElementalReaction(damage)
            e.set_reaction_elements(trigger_element, base_element)
            event = ElementalReactionEvent(e, GetCurrentTime())
            EventBus.publish(event)

            if event.data['elementalReaction'].reaction_type[0] == '剧变反应':
                return 1
            return event.data['elementalReaction'].reaction_multiplier
        return None

    def _trigger_reaction(self, trigger_element, trigger_amount, base_element, base_aura):
        reaction_type, reaction_ratio = ReactionMMap.get((trigger_element, base_element), (None, None))
        if not reaction_type:
            return None

        # 计算元素消耗比例
        ratio = self._get_element_ratio(trigger_element, base_element)
        base_current = base_aura['current_amount']
        trigger_actual = trigger_amount  # 后手元素无衰减

        # 计算实际消耗量
        if trigger_actual / ratio[0] > base_current / ratio[1]:
            # 完全消耗基底元素
            self.elementalAura.remove(base_aura)
            consumed_base = base_current
        else:
            consumed_base = trigger_actual * ratio[1] / ratio[0]
            base_aura['current_amount'] -= consumed_base
            if base_aura['current_amount'] <= 0:
                self.elementalAura.remove(base_aura)

        # 生成反应事件
        reaction_event = {
            'trigger_element': trigger_element,
            'base_element': base_element,
            'reaction_type': reaction_type,
            'consumed_base': consumed_base,
            'consumed_trigger': trigger_actual
        }
        return reaction_event

    def apply_swirl_reaction(self, trigger_element, trigger_amount, base_element):
        ...

    def apply_electro_charged_reaction(self,damage):
        """处理感电反应"""
        trigger_element, trigger_amount = damage.element
        base_element = self.elementalAura[0]['element']
        self._attach_new_element(trigger_element, trigger_amount)
         # 生成反应事件
        e = ElementalReaction(damage)
        e.set_reaction_elements(trigger_element, base_element)
        event = ElementalReactionEvent(e, GetCurrentTime())
        EventBus.publish(event)
        
        return 1

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

    def clear(self):
        self.elementalAura.clear()
        self.effects.clear()
        self.current_frame = 0