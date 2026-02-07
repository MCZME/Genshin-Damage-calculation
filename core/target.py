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
        super().__init__(
            name='测试人偶', 
            faction=Faction.ENEMY, 
            pos=(0.0, 0.0, 0.0)
        )
        
        self.level = data['level']
        
        # 统一初始化 attribute_panel 以对齐新架构
        self.attribute_panel = {
            '防御力': self.level * 5 + 500,
            '固定防御力': 0.0,
            '防御力%': 0.0
        }
        
        # 填充抗性
        resists = data.get('resists', {})
        for el in ['火', '水', '雷', '草', '冰', '岩', '风', '物理']:
            val = resists.get(el, 10.0)
            self.attribute_panel[f"{el}元素抗性"] = val
            
    def handle_damage(self, damage: Damage) -> None:
        """
        [核心协议实现] 接收并处理伤害。
        """
        damage.set_target(self)
        
        # 触发元素碰撞逻辑，基类已处理 reaction_results 同步
        self.apply_elemental_aura(damage)

    def apply_elemental_aura(self, damage: Damage) -> List[Any]:
        """
        物理伤害过滤。
        """
        atk_el, _ = damage.element
        if atk_el == Element.PHYSICAL:
            return []
        return super().apply_elemental_aura(damage)

    def clear(self):
        """重置实体状态"""
        from core.mechanics.aura import AuraManager
        self.aura = AuraManager()
        self.active_effects.clear()
        self.current_frame = 0