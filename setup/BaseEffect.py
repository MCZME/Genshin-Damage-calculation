from setup.Event import DamageEvent, EventBus, EventHandler, EventType
from setup.Tool import GetCurrentTime
from setup.Logger import get_emulation_logger

class Effect:
    def __init__(self, character,duration=0):
        self.character = character
        self.current_character = character
        self.duration = duration
        self.max_duration = self.duration
        self.name = f"{self.__class__.__name__}"
        
    def apply(self):
        """应用效果"""
        pass
    
    def remove(self):
        """移除效果"""
        pass
    
    def update(self,target):
        """更新持续时间"""
        if self.duration > 0:
            self.duration -= 1
            if self.duration <= 0:
                self.remove()

class DamageBoostEffect(Effect):
    """伤害提升效果"""
    def __init__(self, character, name, bonus, duration):
        super().__init__(character, duration)
        self.bonus = bonus  # 伤害提升
        self.name = name
        self.attribute_name = '伤害加成'  # 属性名称
        
    def apply(self):
        # 防止重复应用
        existing = next((e for e in self.character.active_effects 
                       if isinstance(e, DamageBoostEffect) and e.name == self.name), None)
        if existing:
            existing.duration = self.duration  # 刷新持续时间
            return
            
        self.character.add_effect(self)
        self.setEffect()

    def setEffect(self):
        self.character.attributePanel[self.attribute_name] += self.bonus
        get_emulation_logger().log_effect(f"{self.character.name}获得{self.name}效果")

    def remove(self):
        self.romoveEffect()
        self.character.remove_effect(self)

    def romoveEffect(self):
        self.character.attributePanel[self.attribute_name] -= self.bonus
        get_emulation_logger().log_effect(f"{self.character.name}: {self.name}的伤害加成效果结束")

class CritRateBoostEffect(Effect):
    """暴击率提升效果"""
    def __init__(self, character, name, bonus, duration):
        super().__init__(character, duration)
        self.bonus = bonus  # 暴击率提升值
        self.name = name
        self.attribute_name = '暴击率'  # 属性名称
        
    def apply(self, character=None):
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
        self.current_character.remove_effect(self)

    def removeEffect(self):
        self.current_character.attributePanel[self.attribute_name] -= self.bonus
        get_emulation_logger().log_effect(f"{self.current_character.name}: {self.name}的暴击率提升效果结束")

class ElementalDamageBoostEffect(DamageBoostEffect):
    """元素伤害提升效果"""
    def __init__(self, character, name, element_type, bonus, duration):
        super().__init__(character, name, bonus, duration)
        self.element_type = element_type  # 元素类型
    
    def setEffect(self):
        self.character.attributePanel[self.element_type+'元素伤害加成'] += self.bonus
        get_emulation_logger().log_effect(f"{self.character.name}获得{self.name}效果")
    
    def romoveEffect(self):
        self.character.attributePanel[self.element_type+'元素伤害加成'] -= self.bonus
        get_emulation_logger().log_effect(f"{self.character.name}: {self.name}的{self.element_type}元素伤害提升效果结束")

class AttackBoostEffect(Effect):
    """攻击力提升效果"""
    def __init__(self, character, name, bonus, duration):
        super().__init__(character, duration)
        self.bonus = bonus  # 攻击力提升
        self.name = name
        
    def apply(self,character=None):
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
        self.current_character.attributePanel['攻击力%'] -= self.bonus
        self.current_character.remove_effect(self)
        get_emulation_logger().log_effect(f"{self.current_character.name}: {self.name}攻击力提升效果结束")

class AttackValueBoostEffect(Effect):
    """攻击力值提升效果（固定数值）"""
    def __init__(self, character, name, bonus, duration):
        super().__init__(character,duration)
        self.bonus = bonus  # 攻击力固定值提升
        self.name = name
        
    def apply(self):
        # 防止重复应用
        existing = next((e for e in self.character.active_effects 
                       if isinstance(e, AttackValueBoostEffect) and e.name == self.name), None)
        if existing:
            existing.duration = self.duration  # 刷新持续时间
            return
            
        self.character.add_effect(self)
        self.character.attributePanel['固定攻击力'] += self.bonus
        get_emulation_logger().log_effect(f"{self.character.name}的攻击力提升了{self.bonus:.2f}点")

    def remove(self):
        self.character.attributePanel['固定攻击力'] -= self.bonus
        self.character.remove_effect(self)
        get_emulation_logger().log_effect(f"{self.character.name}: {self.name}基础攻击力提升效果结束")

class HealthBoostEffect(Effect):
    """生命值提升效果"""
    def __init__(self, character, name, bonus, duration):
        super().__init__(character,duration)
        self.bonus = bonus  # 生命值提升百分比
        self.name = name
        
    def apply(self):
        # 防止重复应用
        existing = next((e for e in self.character.active_effects 
                       if isinstance(e, HealthBoostEffect) and e.name == self.name), None)
        if existing:
            existing.duration = self.duration
            return
            
        self.character.add_effect(self)
        self.character.attributePanel['生命值%'] += self.bonus
        get_emulation_logger().log_effect(f"{self.character.name}的生命值提升了{self.bonus}%")

    def remove(self):
        self.character.attributePanel['生命值%'] -= self.bonus
        self.character.remove_effect(self)
        get_emulation_logger().log_effect(f"{self.character.name}: {self.name} 生命值提升效果结束")

class DefenseBoostEffect(Effect):
    """防御力提升效果"""
    def __init__(self, character, name, bonus, duration):
        super().__init__(character, duration)
        self.bonus = bonus  # 防御力提升百分比
        self.name = name
        
    def apply(self):
        # 防止重复应用
        existing = next((e for e in self.character.active_effects 
                       if isinstance(e, DefenseBoostEffect) and e.name == self.name), None)
        if existing:
            existing.duration = self.duration  # 刷新持续时间
            return
            
        self.character.add_effect(self)
        self.character.attributePanel['防御力%'] += self.bonus
        get_emulation_logger().log_effect(f"{self.character.name} 获得 {self.name},防御力提升了{self.bonus}%")

    def remove(self):
        self.character.attributePanel['防御力%'] -= self.bonus
        self.character.remove_effect(self)
        get_emulation_logger().log_effect(f"{self.character.name}: {self.name}防御力提升效果结束")

class DefenseValueBoostEffect(Effect):
    """防御力值提升效果（固定数值）"""
    def __init__(self, character, name, bonus, duration):
        super().__init__(character,duration)
        self.bonus = bonus  # 防御力固定值提升
        self.name = name
        
    def apply(self):
        # 防止重复应用
        existing = next((e for e in self.character.active_effects 
                       if isinstance(e, DefenseValueBoostEffect) and e.name == self.name), None)
        if existing:
            existing.duration = self.duration  # 刷新持续时间
            return
            
        self.character.add_effect(self)
        self.character.attributePanel['固定防御力'] += self.bonus
        get_emulation_logger().log_effect(f"{self.character.name}的防御力提升了{self.bonus:.2f}点")

    def remove(self):
        self.character.attributePanel['固定防御力'] -= self.bonus
        self.character.remove_effect(self)
        get_emulation_logger().log_effect(f"{self.character.name}: {self.name}基础防御力提升效果结束")

class DefenseDebuffEffect(Effect):
    def __init__(self, source, target, debuff_rate, duration,name):
        super().__init__(source,duration)
        self.target = target
        self.debuff_rate = debuff_rate
        self.name = name
        
    def apply(self):
        # 检查现有效果
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
        self.target.defense = self.target.defense / (1 - self.debuff_rate/100)
        self.target.remove_effect(self)
        get_emulation_logger().log_effect(f"🛡️ {self.target.name} 的 {self.name} 结束")

class ResistanceDebuffEffect(Effect):
    """元素抗性降低效果"""
    def __init__(self, name, source, target, elements, debuff_rate, duration):
        super().__init__(source,duration)
        self.name = name
        self.target = target
        self.elements = elements
        self.debuff_rate = debuff_rate
        
    def apply(self):
        # 检查现有效果
        existing = next((e for e in self.target.effects 
                       if isinstance(e, ResistanceDebuffEffect) 
                       and e.name == self.name), None)
        if existing:
            existing.duration = self.duration  # 刷新持续时间
            return

        for element in self.elements:
            self.target.element_resistance[element] -= self.debuff_rate
        self.target.add_effect(self)
        get_emulation_logger().log_effect(f"🛡️ {self.character.name} 降低目标{','.join(self.elements)}抗性{self.debuff_rate}%")
        
    def remove(self):
        self.target.remove_effect(self)
        for element in self.elements:
            self.target.element_resistance[element] += self.debuff_rate
        get_emulation_logger().log_effect(f"🛡️ {self.target.name} 的抗性降低效果结束")

class ElementalInfusionEffect(Effect):
    """元素附魔效果"""
    def __init__(self, character, name, element_type, duration, is_unoverridable=False):
        super().__init__(character,duration)
        self.name = name
        self.element_type = element_type
        self.is_unoverridable = is_unoverridable
        self.apply_time = None
        # 冷却控制参数
        self.sequence = [1, 0, 0]  # 攻击序列冷却模板
        self.sequence_index = 0     # 当前序列索引
        self.last_trigger_time = 0  # 最后触发时间
        self.cooldown_reset_time = 2.5*60  # 冷却重置时间（秒）
        
    def should_apply_infusion(self):
        """判断是否应该应用元素附着"""
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
        # 防止重复应用
        existing = next((e for e in self.character.active_effects 
                       if isinstance(e, ElementalInfusionEffect) and e.name == self.name), None)
        if existing:
            existing.duration = self.duration
            return
            
        self.apply_time = GetCurrentTime()
        self.character.add_effect(self)
        get_emulation_logger().log_effect(f"{self.character.name}获得{self.element_type}元素附魔")
        
    def remove(self):
        self.character.remove_effect(self)
        get_emulation_logger().log_effect(f"{self.character.name}: {self.name}元素附魔效果结束")

class ShieldEffect(Effect):
    """护盾效果基类"""
    def __init__(self, character, name, element_type, shield_value, duration):
        super().__init__(character, duration)
        self.name = name
        self.element_type = element_type
        self.shield_value = shield_value
        self.max_shield_value = shield_value  # 记录最大护盾值
        
    def apply(self):
        # 防止重复应用
        existing = next((e for e in self.character.active_effects 
                       if isinstance(e, ShieldEffect) and e.name == self.name), None)
        if existing:
            existing.duration = self.duration  # 刷新持续时间
            existing.shield_value = self.shield_value  # 更新护盾值
            return
            
        self.character.add_shield(self)
        get_emulation_logger().log_effect(f"{self.character.name}获得{self.name}护盾，{self.element_type}元素护盾量为{self.shield_value:.2f}")
        
    def remove(self):
        self.character.remove_shield(self)
        get_emulation_logger().log_effect(f"{self.character.name}: {self.name}护盾效果结束")

class ElementalMasteryBoostEffect(Effect):
    """元素精通提升效果"""
    def __init__(self, character, name, bonus, duration):
        super().__init__(character, duration)
        self.bonus = bonus  # 元素精通提升值
        self.name = name  # 效果名称
        self.attribute_name = '元素精通'  # 属性名称
        
    def apply(self,character):
        self.current_character = character
        # 防止重复应用
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
        self.current_character.remove_effect(self)

    def removeEffect(self):
        self.current_character.attributePanel[self.attribute_name] -= self.bonus
        get_emulation_logger().log_effect(f"{self.current_character.name}: {self.name}的元素精通提升效果结束")

class EnergyRechargeBoostEffect(Effect):
    """元素充能效率提升效果"""
    def __init__(self, character, name, bonus, duration):
        super().__init__(character, duration)
        self.bonus = bonus  # 充能效率提升值
        self.name = name
        self.attribute_name = '元素充能效率%'  # 属性名称
        
    def apply(self):
        # 防止重复应用
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
        self.character.remove_effect(self)

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
        
    def apply(self):
        electroCharged = next((e for e in self.target.effects if isinstance(e, ElectroChargedEffect)), None)
        if electroCharged:
            return
        self.target.add_effect(self)
        get_emulation_logger().log_effect(f"{self.target.name}获得感电")

    def remove(self):
        self.target.remove_effect(self)
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

class STWHealthBoostEffect(HealthBoostEffect):
    def __init__(self, character):
        super().__init__(character, '静水流涌之辉_生命值', 14, 6*60)
        self.stack = 0
        self.last_trigger = 0
        self.interval = 0.2*60

    def apply(self):
        healthBoost = next((e for e in self.character.active_effects if isinstance(e, STWHealthBoostEffect)), None)
        if healthBoost:
            if GetCurrentTime() - self.last_trigger > self.interval:
                if healthBoost.stack < 2:
                    healthBoost.removeEffect()
                    healthBoost.stack += 1
                    healthBoost.setEffect()
                    healthBoost.last_trigger = GetCurrentTime()
                healthBoost.duration = self.duration
            return
        self.character.add_effect(self)
        self.stack = 1
        self.setEffect()
        get_emulation_logger().log_effect(f"{self.character.name}获得{self.name}效果")

    def setEffect(self):
        self.character.attributePanel['生命值%'] += self.bonus * self.stack

    def removeEffect(self):
        self.character.attributePanel['生命值%'] -= self.bonus * self.stack

    def remove(self):
        self.character.remove_effect(self)
        self.removeEffect()
        get_emulation_logger().log_effect(f"{self.character.name}: {self.name}效果结束")

class STWElementSkillBoostEffect(Effect,EventHandler):
    def __init__(self, character):
        super().__init__(character, 6*60)
        self.name = '静水流涌之辉_元素战技'
        self.bonus = 8
        self.stack = 0
        self.last_trigger = 0
        self.interval = 0.2*60

    def apply(self):
        existing = next((e for e in self.character.active_effects if isinstance(e, STWElementSkillBoostEffect)), None)
        if existing:
            if GetCurrentTime() - self.last_trigger > self.interval:
                if existing.stack < 3:
                    existing.stack += 1
            existing.duration = self.duration
            return
        self.character.add_effect(self)
        EventBus.subscribe(EventType.BEFORE_DAMAGE_BONUS,self)
        get_emulation_logger().log_effect(f"{self.character.name}获得{self.name}效果")

    def remove(self):
        self.character.remove_effect(self)
        EventBus.unsubscribe(EventType.BEFORE_DAMAGE_BONUS,self)
        get_emulation_logger().log_effect(f"{self.character.name}: {self.name}效果结束")

    def handle_event(self, event):
        if event.event_type == EventType.BEFORE_DAMAGE_BONUS:
            if event.data['character'] == self.character and event.data['damage'].damageType.value == '元素战技':
                event.data['damage'].panel['伤害加成'] += self.bonus * self.stack
                event.data['damage'].setDamageData(self.name, self.bonus * self.stack)

