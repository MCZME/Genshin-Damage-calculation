from setup.BaseClass import Effect


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
        print(f"攻击力提升效果结束")

class DefenseDebuffEffect(Effect):
    def __init__(self, source, target, debuff_rate, duration):
        super().__init__(source)
        self.target = target
        self.debuff_rate = debuff_rate
        self.duration = duration  # 持续时间（帧数）
        self.source_signature = f"c2_def_debuff_{source.id}"  # 唯一标识
        
    def apply(self):
        # 检查现有效果
        existing = next((e for e in self.target.active_effects 
                       if isinstance(e, DefenseDebuffEffect) 
                       and e.source_signature == self.source_signature), None)
        if existing:
            existing.duration = self.duration  # 刷新持续时间
            return
        self.target.add_effect(self)
        
    def remove(self):
        self.target.remove_effect(self)