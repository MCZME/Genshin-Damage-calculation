from typing import Any, List
from core.entities.base_entity import CombatEntity, Faction
from core.action.damage import Damage
from core.mechanics.aura import Element

class Target(CombatEntity):
    """
    测试人偶 / 怪物实体。
    实现 CombatEntity 接口以接入 CombatSpace 广播系统。
    """
    def __init__(self, data: dict):
        # 初始化 CombatEntity (默认敌对，位于原点)
        super().__init__(
            name='测试人偶', 
            faction=Faction.ENEMY, 
            pos=(0.0, 0.0, 0.0)
        )
        
        self.level = data['level']
        self.get_data(data['resists'])
        self.defense = self.level * 5 + 500

    def get_data(self, data):
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

    def handle_damage(self, damage: Damage) -> None:
        """
        [核心协议实现] 接收并处理伤害。
        在此处触发元素附着判定，后续由 DamageSystem 完成数值计算。
        """
        # 设置伤害的目标引用 (兼容旧版 DamageContext)
        damage.set_target(self)
        
        # 1. 触发元素碰撞逻辑 (返回 ReactionResult 列表)
        # 此处调用继承自 CombatEntity -> AuraManager 的方法
        results = self.apply_elemental_aura(damage)
        
        # 2. 将反应结果存入 Damage 对象，供后续 Pipeline 计算
        damage.data['reaction_results'] = results

    def apply_elemental_aura(self, damage: Damage) -> List[Any]:
        """
        重写父类逻辑：增加物理伤害过滤。
        """
        atk_el, u_val = damage.element
        if atk_el == Element.PHYSICAL:
            return []
        # 调用 AuraManager 核心物理模拟
        return self.aura.apply_element(atk_el, float(u_val))

    def add_effect(self, effect):
        self.active_effects.append(effect)

    def remove_effect(self, effect):
        if effect in self.active_effects:
            self.active_effects.remove(effect)

    def clear(self):
        """重置实体状态"""
        from core.mechanics.aura import AuraManager
        self.aura = AuraManager()
        self.active_effects.clear()
        self.current_frame = 0
