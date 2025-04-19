from core.Event import DamageEvent, EventBus
from core.Tool import GetCurrentTime
from core.Logger import get_emulation_logger

class Effect:
    def __init__(self, character,duration=0):
        self.character = character
        self.current_character = character
        self.duration = duration
        self.max_duration = self.duration
        self.name = f"{self.__class__.__name__}"
        self.is_active = False
        self.msg = ""
        
    def apply(self):
        """应用效果"""
        self.is_active = True
    
    def remove(self):
        """移除效果"""
        self.is_active = False
    
    def update(self,target):
        """更新持续时间"""
        if self.duration > 0:
            self.duration -= 1
            if self.duration <= 0:
                self.remove()

class DamageBoostEffect(Effect):
    """伤害提升效果"""
    def __init__(self, character, current_character, name, bonus, duration):
        super().__init__(character, duration)
        self.bonus = bonus
        self.name = name
        self.attribute_name = '伤害加成'
        self.current_character = current_character
        self.msg = f"""
        <p><span style="color: #faf8f0; font-size: 14pt;">{self.character.name} - {self.name}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">获得{self.bonus:.2f}%伤害加成</span></p>
        """
        
    def apply(self):
        super().apply()
        existing = next((e for e in self.current_character.active_effects 
                       if isinstance(e, DamageBoostEffect) and e.name == self.name), None)
        if existing:
            existing.duration = self.duration  # 刷新持续时间
            return
            
        self.current_character.add_effect(self)
        self.setEffect()

    def setEffect(self):
        self.current_character.attributePanel[self.attribute_name] += self.bonus
        get_emulation_logger().log_effect(f"{self.current_character.name}获得{self.name}效果")

    def remove(self):
        super().remove()
        self.romoveEffect()

    def romoveEffect(self):
        self.current_character.attributePanel[self.attribute_name] -= self.bonus
        get_emulation_logger().log_effect(f"{self.current_character.name}: {self.name}的伤害加成效果结束")

class CritRateBoostEffect(Effect):
    """暴击率提升效果"""
    def __init__(self, character, name, bonus, duration):
        super().__init__(character, duration)
        self.bonus = bonus
        self.name = name
        self.attribute_name = '暴击率'
        self.msg = f"""
        <p><span style="color: #faf8f0; font-size: 14pt;">{self.character.name}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">获得{self.bonus:.2f}%暴击率</span></p>
        """
        
    def apply(self, character=None):
        super().apply()
        self.current_character = character if character else self.character
        # 防止重复应用
        existing = next((e for e in self.current_character.active_effects 
                       if isinstance(e, CritRateBoostEffect) and e.name == self.name), None)
        if existing:
            existing.duration = self.duration  # 刷新持续时间
            return
            
        self.current_character.add_effect(self)
        self.setEffect()

    def setEffect(self):
        self.current_character.attributePanel[self.attribute_name] += self.bonus
        get_emulation_logger().log_effect(f"{self.current_character.name}获得{self.name}效果，暴击率提升{self.bonus}%")

    def remove(self):
        self.removeEffect()
        super().remove()

    def removeEffect(self):
        self.current_character.attributePanel[self.attribute_name] -= self.bonus
        get_emulation_logger().log_effect(f"{self.current_character.name}: {self.name}的暴击率提升效果结束")

class ElementalDamageBoostEffect(DamageBoostEffect):
    """元素伤害提升效果"""
    def __init__(self, character, current_character,name, element_type, bonus, duration):
        super().__init__(character, current_character, name, bonus, duration)
        self.current_character = current_character
        self.element_type = element_type
        self.msg = f"""
        <p><span style="color: #faf8f0; font-size: 14pt;">{self.character.name} - {self.name}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">获得{self.bonus:.2f}%{self.element_type}元素伤害加成</span></p>
        """
    
    def setEffect(self):
        self.current_character.attributePanel[self.element_type+'元素伤害加成'] += self.bonus
        get_emulation_logger().log_effect(f"{self.current_character.name}获得{self.name}效果")
    
    def romoveEffect(self):
        self.current_character.attributePanel[self.element_type+'元素伤害加成'] -= self.bonus
        get_emulation_logger().log_effect(f"{self.current_character.name}: {self.name}的{self.element_type}元素伤害提升效果结束")

class AttackBoostEffect(Effect):
    """攻击力提升效果"""
    def __init__(self, character, name, bonus, duration):
        super().__init__(character, duration)
        self.bonus = bonus
        self.name = name
        self.msg = f"""
        <p><span style="color: #faf8f0; font-size: 14pt;">{self.character.name} - {self.name}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">获得{self.bonus:.2f}%攻击力</span></p>
        """
        
    def apply(self,character=None):
        super().apply()
        self.current_character = character if character else self.character
        # 防止重复应用
        existing = next((e for e in self.current_character.active_effects 
                       if isinstance(e, AttackBoostEffect) and e.name == self.name), None)
        if existing:
            existing.duration = self.duration  # 刷新持续时间
            return
            
        self.current_character.add_effect(self)
        self.current_character.attributePanel['攻击力%'] += self.bonus
        get_emulation_logger().log_effect(f"{self.current_character.name} 获得 {self.name} ,攻击力提升了{self.bonus}%")

    def remove(self):
        super().remove()
        self.current_character.attributePanel['攻击力%'] -= self.bonus
        get_emulation_logger().log_effect(f"{self.current_character.name}: {self.name}攻击力提升效果结束")

class AttackValueBoostEffect(Effect):
    """攻击力值提升效果（固定数值）"""
    def __init__(self, character, current_character, name, bonus, duration):
        super().__init__(character,duration)
        self.current_character = current_character
        self.bonus = bonus
        self.name = name
        self.msg = f"""
        <p><span style="color: #faf8f0; font-size: 14pt;">{self.character.name} - {self.name}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">获得{self.bonus:.2f}点攻击力</span></p>
        """
        
    def apply(self):
        super().apply()
        existing = next((e for e in self.current_character.active_effects 
                       if isinstance(e, AttackValueBoostEffect) and e.name == self.name), None)
        if existing:
            existing.duration = self.duration  # 刷新持续时间
            return
            
        self.current_character.add_effect(self)
        self.current_character.attributePanel['固定攻击力'] += self.bonus
        get_emulation_logger().log_effect(f"{self.current_character.name}的攻击力提升了{self.bonus:.2f}点")

    def remove(self):
        super().remove()
        self.current_character.attributePanel['固定攻击力'] -= self.bonus
        get_emulation_logger().log_effect(f"{self.current_character.name}: {self.name}基础攻击力提升效果结束")

class HealthBoostEffect(Effect):
    """生命值提升效果"""
    def __init__(self, character, name, bonus, duration):
        super().__init__(character,duration)
        self.bonus = bonus
        self.name = name
        self.msg = f"""
        <p><span style="color: #faf8f0; font-size: 14pt;">{self.character.name} - {self.name}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">获得{self.bonus:.2f}%生命值</span></p>
        """
        
    def apply(self):
        super().apply()
        existing = next((e for e in self.character.active_effects 
                       if isinstance(e, HealthBoostEffect) and e.name == self.name), None)
        if existing:
            existing.duration = self.duration
            return
            
        self.character.add_effect(self)
        self.character.attributePanel['生命值%'] += self.bonus
        get_emulation_logger().log_effect(f"{self.character.name}的生命值提升了{self.bonus}%")

    def remove(self):
        super().remove()
        self.character.attributePanel['生命值%'] -= self.bonus
        get_emulation_logger().log_effect(f"{self.character.name}: {self.name} 生命值提升效果结束")

class DefenseBoostEffect(Effect):
    """防御力提升效果"""
    def __init__(self, character, name, bonus, duration):
        super().__init__(character, duration)
        self.bonus = bonus  # 防御力提升百分比
        self.name = name
        self.msg = f"""
        <p><span style="color: #faf8f0; font-size: 14pt;">{self.character.name} - {self.name}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">获得{self.bonus:.2f}%防御力</span></p>
        """
        
    def apply(self):
        super().apply()
        existing = next((e for e in self.character.active_effects 
                       if isinstance(e, DefenseBoostEffect) and e.name == self.name), None)
        if existing:
            existing.duration = self.duration
            return
            
        self.character.add_effect(self)
        self.character.attributePanel['防御力%'] += self.bonus
        get_emulation_logger().log_effect(f"{self.character.name} 获得 {self.name},防御力提升了{self.bonus}%")

    def remove(self):
        super().remove()
        self.character.attributePanel['防御力%'] -= self.bonus
        get_emulation_logger().log_effect(f"{self.character.name}: {self.name}防御力提升效果结束")

class DefenseValueBoostEffect(Effect):
    """防御力值提升效果（固定数值）"""
    def __init__(self, character, name, bonus, duration):
        super().__init__(character,duration)
        self.bonus = bonus
        self.name = name
        self.msg = f"""
        <p><span style="color: #faf8f0; font-size: 14pt;">{self.character.name} - {self.name}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">获得{self.bonus:.2f}点防御力</span></p>
        """
        
    def apply(self):
        super().apply()
        existing = next((e for e in self.character.active_effects 
                       if isinstance(e, DefenseValueBoostEffect) and e.name == self.name), None)
        if existing:
            existing.duration = self.duration  # 刷新持续时间
            return
            
        self.character.add_effect(self)
        self.character.attributePanel['固定防御力'] += self.bonus
        get_emulation_logger().log_effect(f"{self.character.name}的防御力提升了{self.bonus:.2f}点")

    def remove(self):
        super().remove()
        self.character.attributePanel['固定防御力'] -= self.bonus
        get_emulation_logger().log_effect(f"{self.character.name}: {self.name}基础防御力提升效果结束")

class DefenseDebuffEffect(Effect):
    def __init__(self, source, target, debuff_rate, duration,name):
        super().__init__(source,duration)
        self.target = target
        self.debuff_rate = debuff_rate
        self.name = name
        self.msg = f"""
        <p><span style="color: #faf8f0; font-size: 14pt;">{self.character.name} - {self.name}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">降低{self.debuff_rate:.2f}%防御力</span></p>
        """
        
    def apply(self):
        super().apply()
        existing = next((e for e in self.target.effects 
                       if isinstance(e, DefenseDebuffEffect) 
                       and e.name == self.name), None)
        if existing:
            existing.duration = self.duration  # 刷新持续时间
            return
        self.target.defense = self.target.defense * (1 - self.debuff_rate/100)
        self.target.add_effect(self)
        get_emulation_logger().log_effect(f"🛡️ {self.name} 降低目标防御力{self.debuff_rate}%")
        
    def remove(self):
        super().remove()
        self.target.defense = self.target.defense / (1 - self.debuff_rate/100)
        get_emulation_logger().log_effect(f"🛡️ {self.target.name} 的 {self.name} 结束")

    def update(self):
        super().update(None)

class ResistanceDebuffEffect(Effect):
    """元素抗性降低效果"""
    def __init__(self, name, source, target, elements, debuff_rate, duration):
        super().__init__(source,duration)
        self.name = name
        self.target = target
        self.elements = elements
        self.debuff_rate = debuff_rate
        self.msg = f"""
        <p><span style="color: #faf8f0; font-size: 14pt;">{self.character.name} - {self.name}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">降低{','.join(self.elements)}抗{self.debuff_rate:.2f}%</span></p>
        """
        
    def apply(self):
        super().apply()
        existing = next((e for e in self.target.effects 
                       if isinstance(e, ResistanceDebuffEffect) 
                       and e.name == self.name), None)
        if existing:
            existing.duration = self.duration  # 刷新持续时间
            return

        for element in self.elements:
            self.target.current_resistance[element] -= self.debuff_rate
        self.target.add_effect(self)
        get_emulation_logger().log_effect(f"🛡️ {self.character.name} 降低目标{','.join(self.elements)}抗性{self.debuff_rate}%")
        
    def remove(self):
        super().remove()
        for element in self.elements:
            self.target.current_resistance[element] += self.debuff_rate
        get_emulation_logger().log_effect(f"🛡️ {self.target.name} 的抗性降低效果结束")

    def update(self):
        super().update(None)

class ElementalInfusionEffect(Effect):
    """元素附魔效果"""
    def __init__(self, character, current_character, name, element_type, duration, is_unoverridable=False):
        super().__init__(character,duration)
        self.name = name
        self.current_character = current_character
        self.element_type = element_type
        self.is_unoverridable = is_unoverridable
        self.apply_time = None
        # 冷却控制参数
        self.sequence = [1, 0, 0]  # 攻击序列冷却模板
        self.sequence_index = 0     # 当前序列索引
        self.last_trigger_time = 0  # 最后触发时间
        self.cooldown_reset_time = 2.5*60  # 冷却重置时间（秒）
        self.msg = f"""
        <p><span style="color: #faf8f0; font-size: 14pt;">{self.character.name} - {self.name}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">{self.element_type}元素附魔</span></p>
        """
        
    def should_apply_infusion(self,damage_type):
        """判断是否应该应用元素附着"""
        if damage_type.value in ['重击', '下落攻击']:
            return 1
        current_time = GetCurrentTime()
        time_since_last = current_time - self.last_trigger_time
        
        # 时间冷却优先：超过设定阈值则重置序列
        if time_since_last > self.cooldown_reset_time:
            self.sequence_index = 0
            allow = self.sequence[self.sequence_index]
            self.sequence_index = (self.sequence_index + 1) % len(self.sequence)
            self.last_trigger_time = current_time
            return allow
            
        # 攻击序列冷却模式
        allow = self.sequence[self.sequence_index]
        self.sequence_index = (self.sequence_index + 1) % len(self.sequence)
        self.last_trigger_time = current_time
        return allow

    def apply(self):
        super().apply()
        existing = next((e for e in self.current_character.active_effects 
                       if isinstance(e, ElementalInfusionEffect) and e.name == self.name), None)
        if existing:
            existing.duration = self.duration
            return
            
        self.apply_time = GetCurrentTime()
        self.current_character.add_effect(self)
        get_emulation_logger().log_effect(f"{self.current_character.name}获得{self.element_type}元素附魔")
        
    def remove(self):
        super().remove()
        get_emulation_logger().log_effect(f"{self.current_character.name}: {self.name}元素附魔效果结束")

class ShieldEffect(Effect):
    """护盾效果基类"""
    def __init__(self, character, name, element_type, shield_value, duration):
        super().__init__(character, duration)
        self.name = name
        self.element_type = element_type
        self.shield_value = shield_value
        self.max_shield_value = shield_value  # 记录最大护盾值
        
    def apply(self):
        super().apply()
        existing = next((e for e in self.character.active_effects 
                       if isinstance(e, ShieldEffect) and e.name == self.name), None)
        if existing:
            existing.duration = self.duration  # 刷新持续时间
            existing.shield_value = self.shield_value  # 更新护盾值
            return
            
        self.character.add_shield(self)
        get_emulation_logger().log_effect(f"{self.character.name}获得{self.name}护盾，{self.element_type}元素护盾量为{self.shield_value:.2f}")
        
    def remove(self):
        super().remove()
        get_emulation_logger().log_effect(f"{self.character.name}: {self.name}护盾效果结束")

class ElementalMasteryBoostEffect(Effect):
    """元素精通提升效果"""
    def __init__(self, character, name, bonus, duration):
        super().__init__(character, duration)
        self.bonus = bonus 
        self.name = name
        self.attribute_name = '元素精通'
        self.msg = f"""
        <p><span style="color: #faf8f0; font-size: 14pt;">{self.character.name} - {self.name}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">元素精通提升{self.bonus:.2f}点</span></p>
        """
        
    def apply(self,character):
        self.current_character = character
        super().apply()
        existing = next((e for e in self.current_character.active_effects 
                       if isinstance(e, ElementalMasteryBoostEffect) and e.name == self.name), None)
        if existing:
            existing.duration = self.duration  # 刷新持续时间
            return
            
        self.current_character.add_effect(self)
        self.setEffect()

    def setEffect(self):
        self.current_character.attributePanel[self.attribute_name] += self.bonus
        get_emulation_logger().log_effect(f"{self.current_character.name}获得{self.name}效果，元素精通提升{self.bonus}点")

    def remove(self):
        self.removeEffect()
        super().remove()

    def removeEffect(self):
        self.current_character.attributePanel[self.attribute_name] -= self.bonus
        get_emulation_logger().log_effect(f"{self.current_character.name}: {self.name}的元素精通提升效果结束")

class EnergyRechargeBoostEffect(Effect):
    """元素充能效率提升效果"""
    def __init__(self, character, name, bonus, duration):
        super().__init__(character, duration)
        self.bonus = bonus
        self.name = name
        self.attribute_name = '元素充能效率'
        self.msg = f"""
        <p><span style="color: #faf8f0; font-size: 14pt;">{self.character.name} - {self.name}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">元素充能效率提升{self.bonus:.2f}%</span></p>
        """
        
    def apply(self):
        super().apply()
        existing = next((e for e in self.character.active_effects 
                       if isinstance(e, EnergyRechargeBoostEffect) and e.name == self.name), None)
        if existing:
            existing.duration = self.duration  # 刷新持续时间
            return
            
        self.character.add_effect(self)
        self.setEffect()

    def setEffect(self):
        self.character.attributePanel[self.attribute_name] += self.bonus
        get_emulation_logger().log_effect(f"{self.character.name}获得{self.name}效果，元素充能效率提升{self.bonus}%")

    def remove(self):
        self.removeEffect()
        super().remove()

    def removeEffect(self):
        self.character.attributePanel[self.attribute_name] -= self.bonus
        get_emulation_logger().log_effect(f"{self.character.name}: {self.name}的元素充能效率提升效果结束")

class ElectroChargedEffect(Effect):
    """感电效果"""
    def __init__(self, character, target,damage):
        super().__init__(character, 0)
        self.name = '感电'
        self.target = target
        self.current_frame = 0
        self.damage = damage
        self.msg = f"""
        <p><span style="color: #faf8f0; font-size: 14pt;">{self.character.name} - {self.name}</span></p>
        <p><span style="color: #c0e4e6; font-size: 12pt;">感电</span></p>
        """
        
    def apply(self):
        super().apply()
        electroCharged = next((e for e in self.target.effects if isinstance(e, ElectroChargedEffect)), None)
        if electroCharged:
            return
        self.target.add_effect(self)
        get_emulation_logger().log_effect(f"{self.target.name}获得感电")

    def remove(self):
        super().remove()
        get_emulation_logger().log_effect(f"{self.target.name}: 感电结束")

    def update(self, target):
        if len([e for e in self.target.elementalAura if e['element'] == '雷' or e['element'] == '水']) != 2:
            self.remove()
            return
        if self.current_frame % 60 == 0:
            EventBus.publish(DamageEvent(self.character, self.target, self.damage,GetCurrentTime()))
            for e in self.target.elementalAura:
                if e['element'] == '雷':
                    e['current_amount'] = max(0,e['current_amount']-0.4)
                elif e['element'] == '水':
                    e['current_amount'] = max(0,e['current_amount']-0.4)

        self.current_frame += 1
