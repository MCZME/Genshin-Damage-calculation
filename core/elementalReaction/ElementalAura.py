from math import sqrt
from core.event import ElementalReactionEvent, EventBus
from core.tool import GetCurrentTime
from core.elementalReaction.ElementalReaction import ElementalReaction, ElementalReactionType, ReactionMMap

class ElementalAura:
    def __init__(self):
        self.elementalAura = []
        self.burning_elements = {}
        self.quicken_elements = {}

    def getElementalAura(self):
        return self.elementalAura
    
    def setElementalAura(self, elementalAura):
        self.elementalAura = elementalAura

    def apply_elemental_aura(self, damage):
        if damage.element[1] <= 0:
            return None
        if self._check_reactions(damage.element[0]):
            return self.process_elemental_reactions(damage)
        else:
            if damage.element[0] not in {"风", "岩"}:
                self._attach_new_element(damage.element[0], damage.element[1])
            return None

    def process_elemental_reactions(self, damage):
        reaction_triggers = []

        freeze = next((x for x in self.elementalAura if x['element'] == '冻' and x['current_amount'] > 0), None)
        if freeze:
            return self.handle_in_freeze_reaction(damage)

        electro_charged = [x for x in self.elementalAura if x['element'] in ['水', '雷'] and x['current_amount'] > 0 ]
        if electro_charged and (len(electro_charged) == 2 or 
            (damage.element[0] in ['水', '雷'] and damage.element[0] != electro_charged[0]['element'] 
             and len(electro_charged) == 1)):
            return self.handle_electro_charged_reaction(damage)
        
        if self.burning_elements:
            return self.handle_in_burning_reaction(damage)
        
        if self.quicken_elements:
            return self.handle_in_quicken_reaction(damage)

        freeze = next((x for x in self.elementalAura if x['element'] in ['水', '冰'] and x['current_amount'] > 0 and damage.element[0] != x['element']), None)
        if freeze and damage.element[0] in ['水', '冰']:
            return self.handle_freeze_reaction(damage)

        for aura in self.elementalAura:
            base_element = aura['element']
            base_acmount = aura['current_amount']
            reaction_type = ReactionMMap.get((damage.element[0], base_element), None)
            if reaction_type and reaction_type[0] == ElementalReactionType.BURNING:
                reaction_triggers.append(self.handle_burning_reaction(damage))
                continue
            elif reaction_type and reaction_type[0] == ElementalReactionType.QUICKEN:
                reaction_triggers.append(self.handle_quicken_reaction(damage))
                continue
            elif reaction_type and damage.element[1] > 0:
                # 计算消耗比例
                ratio = self._get_element_ratio(damage.element[0], base_element)
                
                # 计算实际消耗
                actual_base_consumed = damage.element[1] * ratio[1] / ratio[0]
                actual_trigger_consumed = base_acmount * ratio[0] / ratio[1]
                
                # 执行元素量更新
                aura['current_amount'] -= actual_base_consumed
                damage.element = (damage.element[0], damage.element[1] - actual_trigger_consumed)
                    
                # 生成反应事件
                e = ElementalReaction(damage)
                e.set_reaction_elements(damage.element[0], base_element if base_element != '冻' else '冰')
                event = ElementalReactionEvent(e, GetCurrentTime())
                EventBus.publish(event)
                
                # 记录反应类型
                if event.data['elementalReaction'].reaction_type[0] == '剧变反应':
                    reaction_triggers.append(None)
                else:
                    reaction_triggers.append(event.data['elementalReaction'].reaction_multiplier)
                
                # 如果触发元素已耗尽则停止
                if damage.element[1] <= 0:
                    break
                
        if reaction_triggers and next((x for x in reaction_triggers if x is not None), None):
            return max(reaction_triggers)
        else:
            return None

    def handle_electro_charged_reaction(self,damage):
        """处理感电反应"""
        reaction_triggers = []
        if damage.element[0] in ['水', '雷']:
            base_element = next((a['element'] for a in self.elementalAura if a['element'] in ['水', '雷'] and
                            a['element'] != damage.element[0]), None)
            self._attach_new_element(damage.element[0], damage.element[1])
            e = ElementalReaction(damage)
            e.set_reaction_elements(damage.element[0], base_element)
            event = ElementalReactionEvent(e, GetCurrentTime())
            EventBus.publish(event)
        else:
            s = {'水': 1, '雷': 0}
            for aura in sorted(self.elementalAura, key=lambda x: s.get(x['element'], 6)):
                r = ReactionMMap.get((damage.element[0], aura['element']), None)
                if r:
                    ratio = self._get_element_ratio(damage.element[0], aura['element'])
                    actual_trigger_consumed = (aura['current_amount']) * ratio[0] / ratio[1]
                    actual_base_consumed = damage.element[1] * ratio[1] / ratio[0]
                    if aura['current_amount'] >= actual_base_consumed:
                        aura['current_amount'] -= actual_base_consumed
                        damage.element = (damage.element[0], 0)
                    else:
                        aura['current_amount'] = 0
                        damage.element = (damage.element[0], damage.element[1] - actual_trigger_consumed)
                    e = ElementalReaction(damage)
                    e.set_reaction_elements(damage.element[0], aura['element'])
                    event = ElementalReactionEvent(e, GetCurrentTime())
                    EventBus.publish(event)

                    if event.data['elementalReaction'].reaction_type[0] == '剧变反应':
                        reaction_triggers.append(0)
                    else:
                        reaction_triggers.append(event.data['elementalReaction'].reaction_multiplier)
                
                if damage.element[1] <= 0:
                    break
                if damage.element[0] == '岩':
                    break
        if reaction_triggers:
            return max(reaction_triggers)
        else:
            return None

    def handle_in_freeze_reaction(self, damage):
        """处理冻结下的反应"""
        base_element = next((a for a in self.elementalAura if a['element'] == '冻'), None)
        if not base_element:
            return
        if (damage.element[0] == '岩' or damage.hit_type == '钝击') and base_element['current_amount'] > 0.5:
            base_element['current_amount'] -= 8
            event = self._create_reaction_event(damage, '岩', '冻')
            EventBus.publish(event)
        self.update() # 更新元素附着状态
        if damage.element[0] == '风':
            s = {'火':0, '雷':1, '水':2, '冰':3,'冻':6}
            return self._handle_in_freeze_special_reaction(damage, s)
        elif damage.element[0] in ['雷', '火']:
            s = {'冻':1, '冰':0}
            return self._handle_in_freeze_special_reaction(damage, s)
        elif damage.element[0] in ['水', '冰']:
            self.handle_freeze_reaction(damage)
        return None
    
    def _handle_in_freeze_special_reaction(self, damage, sort_list):
        """处理冻结下的特殊反应"""
        reaction_triggers = []
        for aura in sorted(self.elementalAura, key=lambda x: sort_list.get(x['element'], 6)):
            r = ReactionMMap.get((damage.element[0], aura['element']), None)
            if r and r[0] == ElementalReactionType.ELECTRO_CHARGED:
                # 如果先触发的是冻元素则不进行下一步感电反应
                continue
            elif r:
                ratio = self._get_element_ratio(damage.element[0], aura['element'])
                actual_trigger_consumed = (aura['current_amount']) * ratio[0] / ratio[1]
                actual_base_consumed = damage.element[1] * ratio[1] / ratio[0]
                if aura['current_amount'] >= actual_base_consumed:
                    aura['current_amount'] -= actual_base_consumed
                    damage.element = (damage.element[0], 0)
                else:
                    aura['current_amount'] = 0
                    damage.element = (damage.element[0], damage.element[1] - actual_trigger_consumed)
                event = self._create_reaction_event(damage, damage.element[0], aura['element'] if aura['element'] != '冻' else '冰')
                EventBus.publish(event)
                if event.data['elementalReaction'].reaction_type[0] != '剧变反应':
                    reaction_triggers.append(event.data['elementalReaction'].reaction_multiplier)
                if damage.element[1] <= 0:
                    break
        if reaction_triggers:
            return max(reaction_triggers)
        else:
            return None

    def handle_freeze_reaction(self, damage):
        base_element = next((a for a in self.elementalAura if a['element'] in ['水', '冰'] and
                            a['element'] != damage.element[0]), None)
        if base_element:
            if damage.element[1] > base_element['current_amount']:
                amount = base_element['current_amount']
                base_element['current_amount'] = 0
            else:
                amount = damage.element[1]
                base_element['current_amount'] -= damage.element[1]
            self._attach_freeze_element('冻', 2*amount)
            event = self._create_reaction_event(damage, damage.element[0], base_element['element'])
            EventBus.publish(event)
        else:
            self._attach_new_element(damage.element[0], damage.element[1])
        return None

    def handle_burning_reaction(self, damage):
        base_aura = next((a for a in self.elementalAura if a['element'] in ['火', '草'] and a['element'] != damage.element[0]), None)
        if base_aura or (self.quicken_elements and damage.element[0] == '火'):
            self._attach_burning_element(damage.element[0], damage.element[1])
            self.burning_elements = {
                'element': '燃',
                'initial_amount': 2,
                'current_amount': 2,
                'decay_rate': 0
            }
            event = self._create_reaction_event(damage, damage.element[0], base_aura['element'] if base_aura else '激')
            EventBus.publish(event)
            if damage.element[0] == '火':
                if self.quicken_elements:
                    self.quicken_elements['decay_rate'] *= 4
                else:
                    a = next((a for a in self.elementalAura if a['element'] == '草'), None)
                    if a:
                        a['decay_rate'] *= 4
        else:
            self._attach_new_element(damage.element[0], damage.element[1])
        return None

    def handle_in_burning_reaction(self, damage):
        """处理在燃烧下的反应"""
        reaction_triggers = []
        if damage.element[0] not in ['火', '草']:
            s = {'火':0, '草':1}
            for aura in sorted(self.elementalAura, key=lambda x: s.get(x['element'], 6)):
                r = ReactionMMap.get((damage.element[0], aura['element']), None)
                if r:
                    ratio = self._get_element_ratio(damage.element[0], aura['element'])
                    if aura['element'] == '火':
                        base_amount = max(self.burning_elements['current_amount'], damage.element[1])
                    else:
                        base_amount = aura['current_amount']
                    actual_trigger_consumed = (base_amount) * ratio[0] / ratio[1]
                    actual_base_consumed = damage.element[1] * ratio[1] / ratio[0]
                    if aura['current_amount'] >= actual_base_consumed:
                        aura['current_amount'] -= actual_base_consumed
                        damage.element = (damage.element[0], 0)
                    else:
                        aura['current_amount'] = 0
                        damage.element = (damage.element[0], damage.element[1] - actual_trigger_consumed)
                    if aura['element'] == '火':
                            self.burning_elements['current_amount'] -= actual_base_consumed
                    event = self._create_reaction_event(damage, damage.element[0], aura['element'])
                    EventBus.publish(event)
                    if event.data['elementalReaction'].reaction_type[0] != '剧变反应':
                        reaction_triggers.append(event.data['elementalReaction'].reaction_multiplier)
                    if damage.element[1] <= 0:
                        break
        else:
            self._attach_burning_element(damage.element[0], damage.element[1])

        if reaction_triggers:
            return max(reaction_triggers)
        else:
            return None

    def handle_quicken_reaction(self, damage):
        base_aura = next((a for a in self.elementalAura if a['element'] in ['雷', '草'] and a['element'] != damage.element[0]), None)
        if base_aura:
            if damage.element[1] > base_aura['current_amount']:
                amount = base_aura['current_amount']
                base_aura['current_amount'] = 0
            else:
                amount = damage.element[1]
                base_aura['current_amount'] -= damage.element[1]
            self._attach_quicken_element(amount)
            event = self._create_reaction_event(damage, damage.element[0], base_aura['element'])
            EventBus.publish(event)
        else:
            self._attach_new_element(damage.element[0], damage.element[1])
        return None

    def handle_in_quicken_reaction(self, damage):
        reaction_triggers = []
        s = {'雷':3, '草':4, '水':1, '冰':2, '火':0}
        for aura in sorted(self.elementalAura, key=lambda x: s.get(x['element'], 6)):
            r = ReactionMMap.get((damage.element[0], aura['element']), None)
            if r:
                ratio = self._get_element_ratio(damage.element[0], aura['element'])

                if aura['element'] == '草':
                    self.quicken_elements['current_amount'] -= damage.element[1] * ratio[1] / ratio[0]
                if aura['current_amount'] >= damage.element[1] * ratio[1] / ratio[0]:
                    aura['current_amount'] -= damage.element[1] * ratio[1] / ratio[0]
                    damage.element = (damage.element[0], 0)
                else:
                    damage.element = (damage.element[0], damage.element[1] - aura['current_amount'] * ratio[0] / ratio[1])
                    aura['current_amount'] = 0

                event = self._create_reaction_event(damage, damage.element[0], aura['element'])
                EventBus.publish(event)

                if event.data['elementalReaction'].reaction_type[0] != '剧变反应':
                    reaction_triggers.append(event.data['elementalReaction'].reaction_multiplier)
                if damage.element[1] <= 0:
                    break
        
        if self.quicken_elements['current_amount'] > 0:
            r = ReactionMMap.get((damage.element[0], '激'), None)
            if r:
                if r[0] == ElementalReactionType.BURNING:
                    self.handle_burning_reaction(damage)
                elif r[0] in [ElementalReactionType.AGGRAVATE, ElementalReactionType.SPREAD]:
                    self._attach_new_element(damage.element[0], damage.element[1])
                else:
                    ratio = self._get_element_ratio(damage.element[0], '激')

                    if self.quicken_elements['current_amount'] >= damage.element[1] * ratio[1] / ratio[0]:
                        self.quicken_elements['current_amount'] -= damage.element[1] * ratio[1] / ratio[0]
                        damage.element = (damage.element[0], 0)
                    else:
                        damage.element = (damage.element[0], damage.element[1] - self.quicken_elements['current_amount'] * ratio[0] / ratio[1])
                        self.quicken_elements['current_amount'] = 0
                
                event = self._create_reaction_event(damage, damage.element[0], '激')
                EventBus.publish(event)
                if event.data['elementalReaction'].reaction_type[0] != '剧变反应':
                    reaction_triggers.append(event.data['elementalReaction'].reaction_multiplier)

        if reaction_triggers:
            return max(reaction_triggers)
        else:
            return None

    def _get_element_ratio(self, trigger, base):
        """获取元素消耗比例 (trigger:base)"""
        # 检查触发元素和基础元素是否为特定组合，并返回相应的消耗比例
        if (trigger, base) in [('水', '火'), ('火', '冰'), ('火', '冻'), ('草','水')]:
            return (1, 2) 
        if (trigger, base) in [('火', '水'), ('冰', '火'), ('水','草')]:
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

    def _attach_burning_element(self, element_type, applied_amount):
        """处理燃烧反应元素附着"""
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
                'decay_rate': applied_amount*0.8 / duration if element_type != '草' else 4 * applied_amount*0.8 / duration
            })

    def _attach_quicken_element(self, applied_amount):
        """处理原激化反应元素附着"""
        duration = 5 * applied_amount + 6

        if self.quicken_elements:
            self.quicken_elements['initial_amount'] = applied_amount
            self.quicken_elements['current_amount'] = applied_amount
            self.quicken_elements['decay_rate'] = applied_amount / duration
        else:
            self.quicken_elements = {
                'element': '激',
                'initial_amount': applied_amount,
                'current_amount': applied_amount,
                'decay_rate': applied_amount / duration
            }

    def _check_reactions(self, element):
        """检查元素反应"""
        for e in self.elementalAura:
            e1, e2 = element, e['element']
            r = ReactionMMap.get((e1, e2), None)
            if r:
                return True
        if self.quicken_elements:
            if ReactionMMap.get((element, '激'), None):
                return True
        if self.burning_elements:
            if ReactionMMap.get((element, '火'), None):
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
        if self.quicken_elements:
            self.quicken_elements['current_amount'] -= self.quicken_elements['decay_rate'] / 60
            if self.quicken_elements['current_amount'] <= 0:
                self.quicken_elements = {}
        for aura in removed:
            self.elementalAura.remove(aura)

    def clear(self):
        self.elementalAura.clear()
