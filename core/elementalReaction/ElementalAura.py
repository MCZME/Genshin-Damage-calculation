from math import sqrt
from core.Event import ElementalReactionEvent, EventBus
from core.Tool import GetCurrentTime
from core.elementalReaction.ElementalReaction import ElementalReaction, ElementalReactionType, ReactionMMap

class ElementalAura:
    def __init__(self):
        self.elementalAura = []

    def getElementalAura(self):
        return self.elementalAura
    
    def setElementalAura(self, elementalAura):
        self.elementalAura = elementalAura

    def apply_elemental_aura(self, damage):
        if self._check_reactions(damage.element[0]):
            return self.process_elemental_reactions(damage)
        else:
            if damage.element[0] not in {"风", "岩"}:
                self._attach_new_element(damage.element[0], damage.element[1])
            return None

    def process_elemental_reactions(self, damage):
        reaction_triggers = []
        trigger_element, trigger_amount = damage.element

        freeze = next((x for x in self.elementalAura if x['element'] == '冻' and x['current_amount'] > 0), None)
        if freeze:
            return self.handle_in_freeze_reaction(damage)

        electro_charged = [x for x in self.elementalAura if x['element'] in ['水', '雷'] and x['current_amount'] > 0 ]
        if electro_charged and (len(electro_charged) == 2 or 
            (trigger_element in ['水', '雷'] and trigger_element != electro_charged[0]['element'] 
             and len(electro_charged) == 1)):
            return self.handle_electro_charged_reaction(damage)
        
        freeze = next((x for x in self.elementalAura if x['element'] in ['水', '冰'] and x['current_amount'] > 0 and trigger_element != x['element']), None)
        if freeze:
            return self.handle_freeze_reaction(damage)

        for aura in self.elementalAura:
            base_element = aura['element']
            base_acmount = aura['current_amount']
            reaction_type = ReactionMMap.get((trigger_element, base_element), None)
            if reaction_type and trigger_amount > 0:
                # 计算消耗比例
                ratio = self._get_element_ratio(trigger_element, base_element)
                
                # 计算实际消耗
                actual_base_consumed = trigger_amount * ratio[1] / ratio[0]
                actual_trigger_consumed = base_acmount * ratio[0] / ratio[1]
                
                # 执行元素量更新
                aura['current_amount'] -= actual_base_consumed
                trigger_amount -= actual_trigger_consumed
                    
                # 生成反应事件
                e = ElementalReaction(damage)
                e.set_reaction_elements(trigger_element, base_element if base_element != '冻' else '冰')
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
            return max(reaction_triggers)
        else:
            return None

    def handle_electro_charged_reaction(self,damage):
        """处理感电反应"""
        reaction_triggers = []
        trigger_element, trigger_amount = damage.element
        if trigger_element in ['水', '雷']:
            base_element = next((a['element'] for a in self.elementalAura if a['element'] in ['水', '雷'] and
                            a['element'] != trigger_element), None)
            self._attach_new_element(trigger_element, trigger_amount)
            e = ElementalReaction(damage)
            e.set_reaction_elements(trigger_element, base_element)
            event = ElementalReactionEvent(e, GetCurrentTime())
            EventBus.publish(event)
        else:
            s = {'水': 1, '雷': 0}
            for aura in sorted(self.elementalAura, key=lambda x: s.get(x['element'], 6)):
                r = ReactionMMap.get((trigger_element, aura['element']), None)
                if r:
                    ratio = self._get_element_ratio(trigger_element, aura['element'])
                    actual_trigger_consumed = (aura['current_amount']) * ratio[0] / ratio[1]
                    actual_base_consumed = trigger_amount * ratio[1] / ratio[0]
                    if aura['current_amount'] >= actual_base_consumed:
                        aura['current_amount'] -= actual_base_consumed
                        trigger_amount = 0
                    else:
                        aura['current_amount'] = 0
                        trigger_amount -= actual_trigger_consumed
                    e = ElementalReaction(damage)
                    e.set_reaction_elements(trigger_element, aura['element'])
                    event = ElementalReactionEvent(e, GetCurrentTime())
                    EventBus.publish(event)

                    if event.data['elementalReaction'].reaction_type[0] == '剧变反应':
                        reaction_triggers.append(0)
                    else:
                        reaction_triggers.append(event.data['elementalReaction'].reaction_multiplier)
                
                if trigger_amount <= 0:
                    break
                if trigger_element == '岩':
                    break
        if reaction_triggers:
            return max(reaction_triggers)
        else:
            return None

    def handle_in_freeze_reaction(self, damage):
        """处理冻结下的反应"""
        trigger_element, trigger_amount = damage.element
        base_element = next((a for a in self.elementalAura if a['element'] == '冻'), None)
        if not base_element:
            return
        if (trigger_element == '岩' or damage.hit_type == '钝击') and base_element['current_amount'] > 0.5:
            base_element['current_amount'] -= 8
            event = self._create_reaction_event(damage, '岩', '冻')
            EventBus.publish(event)
        self.update() # 更新元素附着状态
        if trigger_element == '风':
            s = {'冻':6}
            return self._handle_in_freeze_special_reaction(damage, s)
        elif trigger_element in ['雷', '火']:
            s = {'冻':1, '冰':0}
            return self._handle_in_freeze_special_reaction(damage, s)
        elif trigger_element in ['水', '冰']:
            self.handle_freeze_reaction(damage)
        return None
    
    def _handle_in_freeze_special_reaction(self, damage, sort_list):
        """处理冻结下的特殊反应"""
        trigger_element, trigger_amount = damage.element
        reaction_triggers = []
        for aura in sorted(self.elementalAura, key=lambda x: sort_list.get(x['element'], 6)):
            r = ReactionMMap.get((trigger_element, aura['element']), None)
            if r and r[0] == ElementalReactionType.ELECTRO_CHARGED:
                # 如果先触发的是冻元素则不进行下一步感电反应
                continue
            elif r:
                ratio = self._get_element_ratio(trigger_element, aura['element'])
                actual_trigger_consumed = (aura['current_amount']) * ratio[0] / ratio[1]
                actual_base_consumed = trigger_amount * ratio[1] / ratio[0]
                if aura['current_amount'] >= actual_base_consumed:
                    aura['current_amount'] -= actual_base_consumed
                    trigger_amount = 0
                else:
                    aura['current_amount'] = 0
                    trigger_amount -= actual_trigger_consumed
                event = self._create_reaction_event(damage, trigger_element, aura['element'] if aura['element'] != '冻' else '冰')
                EventBus.publish(event)
                if event.data['elementalReaction'].reaction_type[0] != '剧变反应':
                    reaction_triggers.append(event.data['elementalReaction'].reaction_multiplier)
                if trigger_amount <= 0:
                    break
        if reaction_triggers:
            return max(reaction_triggers)
        else:
            return None

    def handle_freeze_reaction(self, damage):
        trigger_element, trigger_amount = damage.element
        base_element = next((a for a in self.elementalAura if a['element'] in ['水', '冰'] and
                            a['element'] != trigger_element), None)
        if base_element:
            if trigger_amount > base_element['current_amount']:
                amount = base_element['current_amount']
                base_element['current_amount'] = 0
            else:
                amount = trigger_amount
                base_element['current_amount'] -= trigger_amount
            self._attach_freeze_element('冻', 2*amount)
            event = self._create_reaction_event(damage, trigger_element, base_element['element'])
            EventBus.publish(event)
        else:
            self._attach_new_element(trigger_element, trigger_amount)
        return None

    def _get_element_ratio(self, trigger, base):
        """获取元素消耗比例 (trigger:base)"""
        # 检查触发元素和基础元素是否为特定组合，并返回相应的消耗比例
        if (trigger, base) in [('水', '火'), ('火', '冰'), ('火', '冻')]:
            return (1, 2) 
        if (trigger, base) in [('火', '水'), ('冰', '火')]:
            return (2, 1)  
        if trigger in {'风','岩'} and base in {'水','雷','冰','火', '冻'}:
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

    def _attach_freeze_element(self, element_type, applied_amount):
        """处理冻元素附着"""
        existing_aura = next((a for a in self.elementalAura if a['element'] == element_type), None)
        duration = 2 * sqrt(5 * applied_amount + 4) - 4

        if existing_aura:
            duration = duration * 0.7 + existing_aura['current_amount'] / existing_aura['decay_rate']
            amount = max(applied_amount, existing_aura['current_amount'])
            existing_aura.update({
                'initial_amount': amount,
                'current_amount': amount,
                'decay_rate': amount / duration
            })
        else:   
            self.elementalAura.append({
                'element': element_type,
                'initial_amount': applied_amount,
                'current_amount': applied_amount,
                'decay_rate': applied_amount / duration
            })

    def _check_reactions(self, element):
        """检查元素反应"""
        for e in self.elementalAura:
            e1, e2 = element, e['element']
            r = ReactionMMap.get((e1, e2), None)
            if r:
                return True
        return False

    def _create_reaction_event(self, damage, trigger, base):
        e = ElementalReaction(damage)
        e.set_reaction_elements(trigger, base)
        return ElementalReactionEvent(e, GetCurrentTime())

    def update(self):
        """更新元素衰减状态"""
        removed = []
        for aura in self.elementalAura:
            # 按帧衰减（每秒60帧）
            aura['current_amount'] -= aura['decay_rate'] / 60
            # 清除已衰减完毕的元素
            if aura['current_amount'] <= 0:
                removed.append(aura)
        for aura in removed:
            self.elementalAura.remove(aura)

    def clear(self):
        self.elementalAura.clear()
