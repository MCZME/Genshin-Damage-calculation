from typing import List, Optional, Dict, Any
from character.character import Character
from core.logger import get_emulation_logger
from core.effect.stat_modifier import AttackBoostEffect, HealthBoostEffect
from core.effect.resonance import CreepingGrassEffect, SteadfastStoneEffect, SwiftWindEffect
from core.event import CharacterSwitchEvent, EventBus
from core.tool import GetCurrentTime
from core.context import get_context

class Team:
    """
    队伍管理类。
    """
    # -----------------------------------------------------
    # 静态属性 (Deprecated)
    # -----------------------------------------------------
    team: List[Character] = []
    current_character: Optional[Character] = None
    current_frame: int = 0
    active_objects: List[Any] = []
    active_resonances: Dict[str, bool] = {}
    element_counts: Dict[str, int] = {}

    def __init__(self, characters: List[Character]):
        self.team = characters
        self.active_objects = []
        self.active_resonances = {}
        self.element_counts = {}
        self.swap_cd = 60
        self.swap_cd_timer = 0
        
        self.current_character = characters[0] if characters else None
        if self.current_character:
            self.current_character.on_field = True
            
        Team.team = self.team
        Team.current_character = self.current_character
        Team.active_objects = self.active_objects
        Team.active_resonances = self.active_resonances
        
        self._update_element_counts()
        self._apply_resonance_effects()

    def get_character_by_name(self, name: str) -> Optional[Character]:
        for char in self.team:
            if char.name == name: return char
        return None

    def _update_element_counts(self):
        self.element_counts = {}
        for char in self.team:
            element = char.element
            self.element_counts[element] = self.element_counts.get(element, 0) + 1
        Team.element_counts = self.element_counts

    def _apply_resonance_effects(self):
        for resonance in list(self.active_resonances.keys()):
            if not self._check_resonance_condition(resonance):
                self._remove_resonance(resonance)

        self._check_and_apply_resonance('热诚之火', '火', AttackBoostEffect, 25)
        self._check_and_apply_resonance('愈疗之水', '水', HealthBoostEffect, 25)
        self._check_and_apply_resonance('迅捷之风', '风', SwiftWindEffect)
        self._check_and_apply_resonance('蔓生之草', '草', CreepingGrassEffect)
        self._check_and_apply_resonance('坚定之岩', '岩', SteadfastStoneEffect)
        self._handle_special_resonance()

    def _check_and_apply_resonance(self, name, element, effect_cls, *args):
        if self.element_counts.get(element, 0) >= 2 and len(self.team) >= 4:
            if name not in self.active_resonances:
                for char in self.team:
                    if args:
                        effect = effect_cls(char, char, name, *args, float('inf'))
                    else:
                        effect = effect_cls(char)
                    effect.apply()
                self.active_resonances[name] = True

    def _handle_special_resonance(self):
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

    def _check_resonance_condition(self, resonance_name):
        mapping = {'热诚之火': '火', '愈疗之水': '水', '强能之雷': '雷', '粉碎之冰': '冰', '迅捷之风': '风', '蔓生之草': '草', '坚定之岩': '岩'}
        element = mapping.get(resonance_name)
        return self.element_counts.get(element, 0) >= 2 if element else False

    def _remove_resonance(self, resonance_name):
        if resonance_name in ['热诚之火', '愈疗之水', '迅捷之风', '蔓生之草', '坚定之岩']:
             for char in self.team:
                for eff in [e for e in char.active_effects if e.name == resonance_name]:
                    eff.remove()
        elif resonance_name == '强能之雷':
            from core.entities.elemental_entities import LightningBladeObject
            for obj in [o for o in self.active_objects if isinstance(o, LightningBladeObject)]:
                obj.on_finish(None)
        elif resonance_name == '粉碎之冰':
            from core.entities.combat_entities import ShatteredIceObject
            for obj in [o for o in self.active_objects if isinstance(o, ShatteredIceObject)]:
                obj.on_finish(None)
        self.active_resonances.pop(resonance_name, None)
    
    @classmethod
    def clear(cls):
        cls.team.clear()
        cls.active_objects.clear()
        cls.active_resonances.clear()
        cls.current_character = None
        cls.current_frame = 0
    
    def swap(self, action):
        char_name, method, params = action
        if char_name == self.current_character.name:
            return self._execute_action(self.current_character, method, params)
        else:
            if self.swap_cd_timer == 0:
                target_char = self.get_character_by_name(char_name)
                # 移除对 CharacterState.IDLE 的判断，ASM 会在 request_action 中处理拦截
                if target_char:
                    self._perform_switch(target_char)
                    return self._execute_action(self.current_character, method, params)
            elif self.swap_cd_timer % 30 == 0:
                get_emulation_logger().log('WARN', f"切换角色CD中 {self.swap_cd_timer}")
        return False

    def _perform_switch(self, new_char):
        EventBus.publish(CharacterSwitchEvent(self.current_character, new_char, frame=GetCurrentTime()))
        self.current_character.on_field = False
        new_char.on_field = True
        self.current_character = new_char
        Team.current_character = new_char
        self.swap_cd_timer = self.swap_cd
        Team.current_frame = self.swap_cd 

    def _execute_action(self, char, method, params):
        # 委托给角色的新接口 (snake_case)
        if hasattr(char, method):
            if params is not None: getattr(char, method)(params)
            else: getattr(char, method)()
            return True
        return False

    def update(self, target):
        for character in self.team: character.update(target)
        self.update_objects(target)
        if self.swap_cd_timer > 0:
            self.swap_cd_timer -= 1
            Team.current_frame = self.swap_cd_timer

    def update_objects(self, target):
        removed = [obj for obj in self.active_objects if not obj.is_active]
        for obj in self.active_objects:
            if obj.is_active: obj.update(target)
        for obj in removed: self.remove_object(obj)

    @classmethod
    def add_object(cls, obj):
        try:
            ctx = get_context()
            if ctx.team and obj not in ctx.team.active_objects: ctx.team.active_objects.append(obj)
        except: pass
        if obj not in cls.active_objects: cls.active_objects.append(obj)

    @classmethod
    def remove_object(cls, obj):
        try:
            ctx = get_context()
            if ctx.team and obj in ctx.team.active_objects: ctx.team.active_objects.remove(obj)
        except: pass
        if obj in cls.active_objects: cls.active_objects.remove(obj)
