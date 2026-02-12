from typing import List, Optional, Dict, Any, Type
from character.character import Character
from core.effect.stat_modifier import AttackBoostEffect, HealthBoostEffect
from core.effect.resonance import CreepingGrassEffect, SteadfastStoneEffect, SwiftWindEffect
from core.event import CharacterSwitchEvent, EventBus 
from core.context import get_context
from core.tool import get_current_time

class Team:
    """
    队伍管理类。
    负责角色编队、切换、共鸣逻辑。
    实体的物理生存与驱动由 CombatSpace 全权负责。
    """
    def __init__(self, characters: List[Character]):
        self.team: List[Character] = characters
        self.current_character: Optional[Character] = characters[0] if characters else None
        
        self.active_resonances: Dict[str, bool] = {}
        self.element_counts: Dict[str, int] = {}
        self.swap_cd: int = 60
        self.swap_cd_timer: int = 0
        
        if self.current_character:
            self.current_character.on_field = True
            
        # 自动化注册角色至战斗空间
        ctx = get_context()
        for char in self.team:
            ctx.space.register(char)
            
        self._update_element_counts()
        self._apply_resonance_effects()

    def get_character_by_name(self, name: str) -> Optional[Character]:
        for char in self.team:
            if char.name == name: return char
        return None

    def _update_element_counts(self) -> None:
        self.element_counts = {}
        for char in self.team:
            self.element_counts[char.element] = self.element_counts.get(char.element, 0) + 1

    def _apply_resonance_effects(self) -> None:
        for resonance in list(self.active_resonances.keys()):
            if not self._check_resonance_condition(resonance):
                self._remove_resonance(resonance)
        self._check_and_apply_resonance('热诚之火', '火', AttackBoostEffect, 25)
        self._check_and_apply_resonance('愈疗之水', '水', HealthBoostEffect, 25)
        self._check_and_apply_resonance('迅捷之风', '风', SwiftWindEffect)
        self._check_and_apply_resonance('蔓生之草', '草', CreepingGrassEffect)
        self._check_and_apply_resonance('坚定之岩', '岩', SteadfastStoneEffect)
        self._handle_special_resonance()

    def _check_and_apply_resonance(self, name: str, element: str, effect_cls: Type, *args) -> None:
        if self.element_counts.get(element, 0) >= 2 and len(self.team) >= 4:
            if name not in self.active_resonances:
                for char in self.team:
                    if args: effect = effect_cls(char, char, name, *args, float('inf'))
                    else: effect = effect_cls(char)
                    effect.apply()
                self.active_resonances[name] = True

    def _handle_special_resonance(self) -> None:
        if self.element_counts.get('雷', 0) >= 2 and len(self.team) >= 4:
            if '强能之雷' not in self.active_resonances:
                from core.entities.elemental_entities import LightningBladeObject
                LightningBladeObject().apply()
                self.active_resonances['强能之雷'] = True
        if self.element_counts.get('冰', 0) >= 2 and len(self.team) >= 4:
            if '粉碎之冰' not in self.active_resonances:
                from core.entities.combat_entities import ShatteredIceObject
                ShatteredIceObject().apply()
                self.active_resonances['粉碎之冰'] = True

    def _check_resonance_condition(self, resonance_name: str) -> bool:
        mapping = {'热诚之火':'火', '愈疗之水':'水', '强能之雷':'雷', '粉碎之冰':'冰', '迅捷之风':'风', '蔓生之草':'草', '坚定之岩':'岩'}
        el = mapping.get(resonance_name)
        return self.element_counts.get(el, 0) >= 2 if el else False

    def _remove_resonance(self, resonance_name: str) -> None:
        if resonance_name in ['热诚之火', '愈疗之水', '迅捷之风', '蔓生之草', '坚定之岩']:
             for char in self.team:
                for eff in [e for e in char.active_effects if e.name == resonance_name]: eff.remove()
        self.active_resonances.pop(resonance_name, None)
    
    def swap(self, action: tuple) -> bool:
        char_name, method, params = action
        if self.current_character is None: return False
        if char_name == self.current_character.name:
            return self._execute_action(self.current_character, method, params)
        else:
            if self.swap_cd_timer == 0:
                target_char = self.get_character_by_name(char_name)
                if target_char:
                    self._perform_switch(target_char)
                    return self._execute_action(self.current_character, method, params)
        return False

    def _perform_switch(self, new_char: Character) -> None:
        from core.logger import get_emulation_logger
        old_name = self.current_character.name if self.current_character else "None"
        get_emulation_logger().log_info(f"切换角色: {old_name} -> {new_char.name}", sender="Team")
        
        EventBus.publish(CharacterSwitchEvent(self.current_character, new_char, frame=get_current_time()))
        if self.current_character: self.current_character.on_field = False
        new_char.on_field = True
        self.current_character = new_char
        self.swap_cd_timer = self.swap_cd

    def _execute_action(self, char: Character, method: str, params: Any) -> bool:
        if hasattr(char, method):
            attr = getattr(char, method)
            if params is not None: attr(params)
            else: attr()
            return True
        return False

    def update(self) -> None:
        """驱动编队逻辑 (仅包含切换 CD)。实体驱动已外包。"""
        if self.swap_cd_timer > 0:
            self.swap_cd_timer -= 1

    def add_object(self, obj: Any) -> None:
        """注册实体到场景"""
        get_context().space.register(obj)

    def remove_object(self, obj: Any) -> None:
        """从场景注销实体"""
        get_context().space.unregister(obj)
            
    def reset(self) -> None:
        self.active_resonances.clear()
        self.swap_cd_timer = 0
        if self.current_character: self.current_character.on_field = False
        if self.team:
            self.current_character = self.team[0]
            self.current_character.on_field = True
