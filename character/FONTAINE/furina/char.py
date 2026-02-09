from typing import Dict, Any, List
from core.registry import register_character
from character.FONTAINE.fontaine import Fontaine
from core.mechanics.energy import ElementalEnergy
from core.event import EventHandler, EventType, GameEvent
from core.action.damage import Damage, DamageType
from core.entities.arkhe import ArkheObject
from character.FONTAINE.furina.skills import SalonSolitaire, UniversalRevelry, FurinaChargedAttack
from character.FONTAINE.furina.talents import (
    PassiveSkillEffect_1, PassiveSkillEffect_2,
    ConstellationEffect_1, ConstellationEffect_2, ConstellationEffect_4, ConstellationEffect_6
)

class ArkheAttackHandler(EventHandler):
    """处理普攻触发始基力伤害"""
    def __init__(self, character: Any):
        self.character = character
        self.last_trigger_time = -360
        self.multipliers = [9.46, 10.23, 11, 12.1, 12.87, 13.75, 14.96, 16.17, 17.38, 18.7, 20.02, 21.34, 22.66, 23.98, 25.3]

    def handle_event(self, event: GameEvent):
        if event.event_type == EventType.AFTER_NORMAL_ATTACK and event.source == self.character:
            now = event.frame
            if now - self.last_trigger_time >= 360:
                self.last_trigger_time = now
                name = '流涌之刃' if self.character.arkhe == '荒性' else '灵息之刺'
                damage = Damage(self.multipliers[self.character.skill_params[0]-1], ('水', 0), DamageType.NORMAL, name)
                ArkheObject(name, self.character, self.character.arkhe, damage, 18).apply()

@register_character("芙宁娜")
class FURINA(Fontaine):
    """芙宁娜 - 完整复刻版"""
    def __init__(self, level: int = 1, skill_params: List[int] = None, constellation: int = 0, base_data: Dict[str, Any] = None):
        super().__init__(id=75, level=level, skill_params=skill_params, constellation=constellation, base_data=base_data)

    def _init_character(self):
        self.elemental_energy = ElementalEnergy(self, ('水', 60))
        self.arkhe = "荒性"
        
        # 技能实例化
        self.Skill = SalonSolitaire(self.skill_params[1])
        self.Burst = UniversalRevelry(self.skill_params[2])
        self.ChargedAttack = FurinaChargedAttack(self.skill_params[0])
        
        # 始基力攻击处理器
        self.arkhe_handler = ArkheAttackHandler(self)
        self.event_engine.subscribe(EventType.AFTER_NORMAL_ATTACK, self.arkhe_handler)
        
        # 天赋与命座
        self.talent1 = PassiveSkillEffect_1()
        self.talent2 = PassiveSkillEffect_2()
        
        self.constellation_effects = [
            ConstellationEffect_1(),
            ConstellationEffect_2(),
            None, # 3命通常是等级加成
            ConstellationEffect_4(),
            None, # 5命通常是等级加成
            ConstellationEffect_6()
        ]

    def _get_action_data(self, name: str, params: Any) -> Any:
        if name == "elemental_skill": return self.Skill.to_action_data()
        if name == "elemental_burst": return self.Burst.to_action_data()
        if name == "charged_attack": return self.ChargedAttack.to_action_data()
        return super()._get_action_data(name, params)