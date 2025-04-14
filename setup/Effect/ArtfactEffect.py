from setup.Effect.BaseEffect import ElementalDamageBoostEffect
from setup.Logger import get_emulation_logger


class CinderCityEffect(ElementalDamageBoostEffect):
    """烬城勇者绘卷效果"""
    def __init__(self, character,current_character,element_type):
        super().__init__(character, '烬城勇者绘卷', element_type, 12, 12*60)
        self.stacks = {}
        self.nightsoul_stacks = {}
        self.nightsoul_duration = 20*60
        self.nightsoul_bonus = 28
        self.current_character = current_character

    def apply(self,element_type):
        # 防止重复应用
        existing = next((e for e in self.current_character.active_effects 
                    if isinstance(e, CinderCityEffect)), None)
        if existing:
            for i in element_type:
                if i in existing.stacks.keys():
                    existing.stacks[i] = self.duration
                else:
                    existing.apply_element(i)
                if self.character.Nightsoul_Blessing:
                    if i in existing.nightsoul_stacks.keys():
                        existing.nightsoul_stacks[i] = self.nightsoul_bonus
                    else:
                        existing.apply_nightsoul(i)
            return
        for element in self.element_type:
            self.current_character.attributePanel[element+'元素伤害加成'] += self.bonus
            self.stacks[element] = self.duration
            if self.character.Nightsoul_Blessing:
                self.current_character.attributePanel[element+'元素伤害加成'] += self.nightsoul_bonus
                self.nightsoul_stacks[element] = self.nightsoul_duration
        self.current_character.add_effect(self)
        get_emulation_logger().log_effect(f"🌋 {self.current_character.name}获得{element_type}烬城勇者绘卷效果")

    def apply_element(self,element):
        self.current_character.attributePanel[element+'元素伤害加成'] += self.bonus
        self.stacks[element] = self.duration
        get_emulation_logger().log_effect(f"🌋 {self.current_character.name}触发烬城勇者绘卷 效果")

    def apply_nightsoul(self,element):
        self.current_character.attributePanel[element+'元素伤害加成'] += self.nightsoul_bonus
        self.nightsoul_stacks[element] = self.nightsoul_duration
        get_emulation_logger().log_effect(f"🌋 {self.current_character.name}触发烬城勇者绘卷 夜魂效果")
        
    def remove(self):
        for element in self.element_type:
            self.current_character.attributePanel[element+'元素伤害加成'] -= self.bonus
        self.current_character.remove_effect(self)
        get_emulation_logger().log_effect(f"🌋 {self.current_character.name}失去{self.name}效果")

    def remove_element(self,element):
        self.current_character.attributePanel[element+'元素伤害加成'] -= self.bonus
        del self.stacks[element]
        get_emulation_logger().log_effect(f"🌋 {self.current_character.name}失去{element}烬城勇者绘卷 效果")

    def remove_nightsoul(self,element):
        self.current_character.attributePanel[element+'元素伤害加成'] -= self.nightsoul_bonus
        del self.nightsoul_stacks[element]
        get_emulation_logger().log_effect(f"🌋 {self.current_character.name}失去{element}烬城勇者绘卷 夜魂效果")

    def update(self,target):
        keys_to_remove = [elemment for elemment, time in self.stacks.items() if time <= 0]
        for elemment in keys_to_remove:
            self.remove_element(elemment)
        for elemment,time in self.stacks.items():
            self.stacks[elemment] -= 1
        keys_to_remove = [elemment for elemment, time in self.nightsoul_stacks.items() if time <= 0]
        for elemment in keys_to_remove:
            self.remove_nightsoul(elemment)
        for elemment,time in self.nightsoul_stacks.items():
            self.nightsoul_stacks[elemment] -= 1
        if sum(self.nightsoul_stacks.values()) <= 0 and sum(self.stacks.values()) <= 0:
            self.remove()
