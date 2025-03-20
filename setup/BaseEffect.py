from setup.Tool import GetCurrentTime

class Effect:
    def __init__(self, character):
        self.character = character
        self.duration = 0
        
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

class AttackBoostEffect(Effect):
    """攻击力提升效果"""
    def __init__(self, character, name, bonus, duration):
        super().__init__(character)
        self.bonus = bonus  # 攻击力提升
        self.duration = duration  # 持续时间（秒）
        self.original_attack_percent = 0
        self.name = name
        
    def apply(self):
        # 防止重复应用
        existing = next((e for e in self.character.active_effects 
                       if isinstance(e, AttackBoostEffect) and e.name == self.name), None)
        if existing:
            existing.duration = self.duration  # 刷新持续时间
            return
            
        self.character.add_effect(self)
        self.character.attributePanel['攻击力%'] += self.bonus
        print(f"{self.character.name}的攻击力提升了{self.bonus}%")

    def remove(self):
        self.character.attributePanel['攻击力%'] -= self.bonus
        self.character.remove_effect(self)
        print(f"{self.name}攻击力提升效果结束")

class AttackValueBoostEffect(Effect):
    """攻击力值提升效果（固定数值）"""
    def __init__(self, character, name, bonus, duration):
        super().__init__(character)
        self.bonus = bonus  # 攻击力固定值提升
        self.duration = duration  # 持续时间（秒）
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
        print(f"{self.character.name}的攻击力提升了{self.bonus:.2f}点")

    def remove(self):
        self.character.attributePanel['固定攻击力'] -= self.bonus
        self.character.remove_effect(self)
        print(f"{self.name}基础攻击力提升效果结束")

class HealthBoostEffect(Effect):
    """生命值提升效果"""
    def __init__(self, character, name, bonus, duration):
        super().__init__(character)
        self.bonus = bonus  # 生命值提升百分比
        self.duration = duration  # 持续时间
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
        print(f"{self.character.name}的生命值提升了{self.bonus}%")

    def remove(self):
        self.character.attributePanel['生命值%'] -= self.bonus
        self.character.remove_effect(self)
        print(f"生命值提升效果结束")

class DefenseDebuffEffect(Effect):
    def __init__(self, source, target, debuff_rate, duration):
        super().__init__(source)
        self.target = target
        self.debuff_rate = debuff_rate
        self.duration = duration  # 持续时间（帧数）
        self.source_signature = f"c2_def_debuff_{source.id}"  # 唯一标识
        
    def apply(self):
        # 检查现有效果
        existing = next((e for e in self.target.effects 
                       if isinstance(e, DefenseDebuffEffect) 
                       and e.source_signature == self.source_signature), None)
        if existing:
            existing.duration = self.duration  # 刷新持续时间
            return
        self.target.defense = self.target.defense * (1 - self.debuff_rate)
        self.target.add_effect(self)
        
    def remove(self):
        self.target.remove_effect(self)

class ElementalInfusionEffect(Effect):
    """元素附魔效果"""
    def __init__(self, character, name, element_type, duration, is_unoverridable=False):
        super().__init__(character)
        self.name = name
        self.element_type = element_type  # 元素类型
        self.duration = duration  # 持续时间（秒）
        self.is_unoverridable = is_unoverridable  # 是否不可覆盖
        self.apply_time = None  # 效果应用时间
        
    def apply(self):
        # 防止重复应用
        existing = next((e for e in self.character.active_effects 
                       if isinstance(e, ElementalInfusionEffect) and e.name == self.name), None)
        if existing:
            existing.duration = self.duration
            return
            
        self.apply_time = GetCurrentTime()
        self.character.add_effect(self)
        print(f"{self.character.name}获得{self.element_type}元素附魔")
        
    def remove(self):
        self.character.remove_effect(self)
        print(f"{self.name}元素附魔效果结束")
