from typing import List, Optional, Dict, Any, Type
from character.character import Character
from core.logger import get_emulation_logger
from core.effect.stat_modifier import AttackBoostEffect, HealthBoostEffect
from core.effect.resonance import CreepingGrassEffect, SteadfastStoneEffect, SwiftWindEffect
from core.event import CharacterSwitchEvent, EventBus
from core.tool import GetCurrentTime

class Team:
    """
    队伍管理类，负责管理角色切换、元素共鸣及实体生命周期。
    """
    def __init__(self, characters: List[Character]):
        self.team: List[Character] = characters
        self.current_character: Optional[Character] = characters[0] if characters else None
        
        # 状态属性
        self.active_objects: List[Any] = []
        self.active_resonances: Dict[str, bool] = {}
        self.element_counts: Dict[str, int] = {}
        
        # 切换逻辑
        self.swap_cd: int = 60
        self.swap_cd_timer: int = 0
        
        if self.current_character:
            self.current_character.on_field = True
            
        self._update_element_counts()
        self._apply_resonance_effects()

    def get_character_by_name(self, name: str) -> Optional[Character]:
        """根据名称获取队伍中的角色实例。"""
        for char in self.team:
            if char.name == name:
                return char
        return None

    def _update_element_counts(self) -> None:
        """更新队伍中各元素的角色数量。"""
        self.element_counts = {}
        for char in self.team:
            element = char.element
            self.element_counts[element] = self.element_counts.get(element, 0) + 1

    def _apply_resonance_effects(self) -> None:
        """根据队伍构成应用元素共鸣效果。"""
        # 清理失效共鸣
        for resonance in list(self.active_resonances.keys()):
            if not self._check_resonance_condition(resonance):
                self._remove_resonance(resonance)

        # 检查并应用标准共鸣
        self._check_and_apply_resonance('热诚之火', '火', AttackBoostEffect, 25)
        self._check_and_apply_resonance('愈疗之水', '水', HealthBoostEffect, 25)
        self._check_and_apply_resonance('迅捷之风', '风', SwiftWindEffect)
        self._check_and_apply_resonance('蔓生之草', '草', CreepingGrassEffect)
        self._check_and_apply_resonance('坚定之岩', '岩', SteadfastStoneEffect)
        
        self._handle_special_resonance()

    def _check_and_apply_resonance(self, name: str, element: str, effect_cls: Type, *args) -> None:
        """
        通用共鸣应用逻辑。
        条件：同元素角色 >= 2 且队伍满 4 人。
        """
        if self.element_counts.get(element, 0) >= 2 and len(self.team) >= 4:
            if name not in self.active_resonances:
                for char in self.team:
                    if args:
                        effect = effect_cls(char, char, name, *args, float('inf'))
                    else:
                        effect = effect_cls(char)
                    effect.apply()
                self.active_resonances[name] = True

    def _handle_special_resonance(self) -> None:
        """处理雷、冰等特殊共鸣实体的逻辑。"""
        # 雷元素共鸣
        if self.element_counts.get('雷', 0) >= 2 and len(self.team) >= 4:
            if '强能之雷' not in self.active_resonances:
                from core.entities.elemental_entities import LightningBladeObject
                LightningBladeObject().apply()
                self.active_resonances['强能之雷'] = True

        # 冰元素共鸣
        if self.element_counts.get('冰', 0) >= 2 and len(self.team) >= 4:
            if '粉碎之冰' not in self.active_resonances:
                from core.entities.combat_entities import ShatteredIceObject
                ShatteredIceObject().apply()
                self.active_resonances['粉碎之冰'] = True

    def _check_resonance_condition(self, resonance_name: str) -> bool:
        """验证特定共鸣是否仍满足触发条件。"""
        mapping = {
            '热诚之火': '火', '愈疗之水': '水', '强能之雷': '雷', 
            '粉碎之冰': '冰', '迅捷之风': '风', '蔓生之草': '草', '坚定之岩': '岩'
        }
        element = mapping.get(resonance_name)
        return self.element_counts.get(element, 0) >= 2 if element else False

    def _remove_resonance(self, resonance_name: str) -> None:
        """移除指定的共鸣效果及其关联实体。"""
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
    
    def swap(self, action: tuple) -> bool:
        """
        执行角色切换或角色动作。
        action 格式: (char_name, method, params)
        """
        char_name, method, params = action
        if self.current_character is None:
            return False

        if char_name == self.current_character.name:
            return self._execute_action(self.current_character, method, params)
        else:
            if self.swap_cd_timer == 0:
                target_char = self.get_character_by_name(char_name)
                if target_char:
                    self._perform_switch(target_char)
                    return self._execute_action(self.current_character, method, params)
            elif self.swap_cd_timer % 30 == 0:
                get_emulation_logger().log('WARN', f"切换角色 CD 中: {self.swap_cd_timer}")
        return False

    def _perform_switch(self, new_char: Character) -> None:
        """执行底层切换逻辑并发布事件。"""
        EventBus.publish(CharacterSwitchEvent(self.current_character, new_char, frame=GetCurrentTime()))
        if self.current_character:
            self.current_character.on_field = False
        new_char.on_field = True
        self.current_character = new_char
        self.swap_cd_timer = self.swap_cd

    def _execute_action(self, char: Character, method: str, params: Any) -> bool:
        """反射调用角色的动作方法。"""
        if hasattr(char, method):
            attr = getattr(char, method)
            if params is not None:
                attr(params)
            else:
                attr()
            return True
        return False

    def update(self, target: Any) -> None:
        """每帧更新队伍及活跃实体。"""
        for character in self.team:
            character.update(target)
        self.update_objects(target)
        if self.swap_cd_timer > 0:
            self.swap_cd_timer -= 1

    def update_objects(self, target: Any) -> None:
        """更新并清理活跃的召唤物/实体。"""
        removed = [obj for obj in self.active_objects if not obj.is_active]
        for obj in self.active_objects:
            if obj.is_active:
                obj.update(target)
        for obj in removed:
            self.remove_object(obj)

    def add_object(self, obj: Any) -> None:
        """向队伍添加活跃实体（如召唤物）。"""
        if obj not in self.active_objects:
            self.active_objects.append(obj)

    def remove_object(self, obj: Any) -> None:
        """从队伍中移除活跃实体。"""
        if obj in self.active_objects:
            self.active_objects.remove(obj)
            
    def reset(self) -> None:
        """重置队伍状态。"""
        self.active_objects.clear()
        self.active_resonances.clear()
        self.swap_cd_timer = 0
        if self.current_character:
            self.current_character.on_field = False
        if self.team:
            self.current_character = self.team[0]
            self.current_character.on_field = True