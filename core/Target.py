from DataRequest import DR
from core.ElementalReaction import ElementalReaction, ReactionMMap
from core.Event import ElementalReactionEvent, EventBus
from core.Tool import GetCurrentTime

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

        # 获取当前所有存在的元素类型
        current_elements = {aura["element"] for aura in self.elementalAura}

        # 情况1: 已存在水雷共存状态，且新元素是水/雷
        if {"水", "雷"}.issubset(current_elements) and damage.element[0] in ["水", "雷"]:
            return self.apply_electro_charged_reaction(damage)

        # 情况2: 原有逻辑（初次触发感电：水+雷不同元素）
        elif len(self.elementalAura) > 0:
            if (damage.element[0] in ["水", "雷"]
                and self.elementalAura[0]["element"] in ["水", "雷"]
                and damage.element[0] != self.elementalAura[0]["element"]):
                return self.apply_electro_charged_reaction(damage)
            reaction_multiplier = self.process_elemental_reactions(damage)

        if not reaction_multiplier and damage.element[0] not in {"风", "岩"}:
            self._attach_new_element(damage.element[0], damage.element[1])

        return reaction_multiplier
    
    def process_elemental_reactions(self, damage):
        reaction_triggers = []
        trigger_element, trigger_amount = damage.element
        
        # 定义元素反应优先级（例如：雷元素优先）
        priority_elements = ['雷', '水'] if any(x['element'] in ('雷', '水') for x in self.elementalAura) else None
        
        # 根据优先级遍历元素（如果是感电环境则按雷->水顺序，否则正常顺序）
        for element in (priority_elements if priority_elements else self.elementalAura):
            # 查找当前优先处理的元素
            if priority_elements:
                aura = next((x for x in self.elementalAura if x['element'] == element), None)
            else:
                aura = element  # 普通情况直接遍历
                
            if not aura:
                continue
                
            base_element = aura['element']
            base_acmount = aura['current_amount']
            reaction_type = ReactionMMap.get((trigger_element, base_element), None)
            
            if reaction_type and trigger_amount > 0:
                # 计算消耗比例
                ratio = self._get_element_ratio(trigger_element, base_element)
                
                # 计算实际消耗（后手元素无损耗）
                actual_base_consumed = trigger_amount * ratio[1] / ratio[0]
                actual_trigger_consumed = base_acmount * ratio[0] / ratio[1]
                
                # 执行元素量更新
                aura['current_amount'] -= actual_base_consumed
                trigger_amount -= actual_trigger_consumed
                
                # 移除耗尽元素
                if aura['current_amount'] <= 0:
                    self.elementalAura.remove(aura)  # 正确从列表中移除整个元素
                    
                # 生成反应事件
                e = ElementalReaction(damage)
                e.set_reaction_elements(trigger_element, base_element)
                event = ElementalReactionEvent(e, GetCurrentTime())
                EventBus.publish(event)
                
                # 记录反应类型
                if event.data['elementalReaction'].reaction_type[0] == '剧变反应':
                    reaction_triggers.append(None)
                else:
                    reaction_triggers.append(event.data['elementalReaction'].reaction_multiplier)
                
                # 如果触发元素已耗尽则停止
                if trigger_amount <= 0:
                    break
        if reaction_triggers:
            # 优先返回非剧变反应的倍率
            return max(reaction_triggers)
        else:
            return None

    def apply_electro_charged_reaction(self,damage):
        """处理感电反应"""
        trigger_element, trigger_amount = damage.element
        base_element = next((a['element'] for a in self.elementalAura if a['element'] in ['水', '雷'] and
                             a['element'] != trigger_element), None)
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