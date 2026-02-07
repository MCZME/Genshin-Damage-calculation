from core.mechanics.aura import AuraManager, Element
from core.action.damage import Damage

class Target:
    def __init__(self, data):
        self.level = data['level']
        self.get_data(data['resists'])

        self.current_frame = 0
        self.defense = self.level * 5 + 500
        # 使用重构后的 AuraManager
        self.aura = AuraManager()
        self.effects = []

    def get_data(self, data):
        self.name = '测试人偶'
        self.element_resistance = {
            '火': data['火'],
            '水': data['水'],
            '雷': data['雷'],
            '草': data['草'],
            '冰': data['冰'],
            '岩': data['岩'],
            '风': data['风'],
            '物理': data['物理']
        }
        self.current_resistance = self.element_resistance.copy()
    
    def get_current_resistance(self):
        return self.current_resistance
    
    def apply_elemental_aura(self, damage: Damage):
        """
        核心入口：将伤害中的元素应用到目标身上。
        返回触发的所有反应结果列表。
        """
        # damage.element 现在统一为 (Element枚举, U值)
        atk_el, u_val = damage.element

        # 物理伤害不参与附着系统
        if atk_el == Element.PHYSICAL:
            return []

        # 调用物理引擎结算
        results = self.aura.apply_element(atk_el, float(u_val))
        return results
    
    def add_effect(self, effect):
        self.effects.append(effect)

    def remove_effect(self, effect):
        self.effects.remove(effect)

    def update(self):
        self.current_frame += 1
        # 更新元素衰减状态 (每帧 1/60s)
        self.aura.update(1/60)
        
        # 更新其他效果状态
        removed_effects = []
        for effect in self.effects:
            effect.update()
            if not effect.is_active:
                removed_effects.append(effect)
        for effect in removed_effects:
            self.effects.remove(effect)

    def clear(self):
        self.aura = AuraManager()
        self.effects.clear()
        self.current_frame = 0