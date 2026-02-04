from typing import List, Optional, Dict, Any
from character.character import Character, CharacterState
from core.logger import get_emulation_logger
from core.effect.BaseEffect import AttackBoostEffect, CreepingGrassEffect, HealthBoostEffect, SteadfastStoneEffect, SwiftWindEffect
from core.event import CharacterSwitchEvent, EventBus
from core.tool import GetCurrentTime
from core.context import get_context

# 转化字典
action_state = {
    "normal_attack": CharacterState.NORMAL_ATTACK,
    "charged_attack": CharacterState.CHARGED_ATTACK,
    "elemental_skill": CharacterState.SKILL,
    "elemental_burst": CharacterState.BURST,
    "skip": CharacterState.SKIP,
    "plunging_attack": CharacterState.PLUNGING_ATTACK,
    "dash": CharacterState.DASH,
    'jump': CharacterState.JUMP,
}

class Team:
    """
    队伍管理类。
    """
    # -----------------------------------------------------
    # 静态属性 (Deprecated - 为了兼容旧代码，未来应移除)
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
        self.swap_cd_timer = 0  # 实例级的切换冷却计时器
        
        # 初始化当前角色
        self.current_character = characters[0] if characters else None
        if self.current_character:
            self.current_character.on_field = True
            
        # 同步到静态属性 (兼容旧代码)
        Team.team = self.team
        Team.current_character = self.current_character
        Team.active_objects = self.active_objects
        Team.active_resonances = self.active_resonances
        
        self._update_element_counts()
        self._apply_resonance_effects()

    def get_character_by_name(self, name: str) -> Optional[Character]:
        for char in self.team:
            if char.name == name:
                return char
        return None

    def _update_element_counts(self):
        self.element_counts = {}
        for char in self.team:
            element = char.element
            self.element_counts[element] = self.element_counts.get(element, 0) + 1
        # 同步静态
        Team.element_counts = self.element_counts

    def _apply_resonance_effects(self):
        # 清除不再满足条件的共鸣效果
        for resonance in list(self.active_resonances.keys()):
            if not self._check_resonance_condition(resonance):
                self._remove_resonance(resonance)

        # 检查并应用共鸣
        self._check_and_apply_resonance('热诚之火', '火', AttackBoostEffect, 25)
        self._check_and_apply_resonance('愈疗之水', '水', HealthBoostEffect, 25)
        self._check_and_apply_resonance('迅捷之风', '风', SwiftWindEffect)
        self._check_and_apply_resonance('蔓生之草', '草', CreepingGrassEffect)
        self._check_and_apply_resonance('坚定之岩', '岩', SteadfastStoneEffect)
        
        # 特殊共鸣 (雷/冰) 涉及实体生成，需要特殊处理
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
        # 雷元素共鸣
        if self.element_counts.get('雷', 0) >= 2 and len(self.team) >= 4:
            if '强能之雷' not in self.active_resonances:
                from core.entities.elemental_entities import LightningBladeObject
                obj = LightningBladeObject()
                obj.apply()
                self.active_resonances['强能之雷'] = True

        # 冰元素共鸣
        if self.element_counts.get('冰', 0) >= 2 and len(self.team) >= 4:
            if '粉碎之冰' not in self.active_resonances:
                from core.entities.combat_entities import ShatteredIceObject
                obj = ShatteredIceObject()
                obj.apply()
                self.active_resonances['粉碎之冰'] = True

    def _check_resonance_condition(self, resonance_name):
        mapping = {
            '热诚之火': '火', '愈疗之水': '水', '强能之雷': '雷',
            '粉碎之冰': '冰', '迅捷之风': '风', '蔓生之草': '草', '坚定之岩': '岩'
        }
        element = mapping.get(resonance_name)
        if element:
            return self.element_counts.get(element, 0) >= 2 and len(self.team) >= 4
        return False

    def _remove_resonance(self, resonance_name):
        # 移除效果逻辑 (保持原样，稍作简化)
        # ... (由于篇幅限制，这里暂略具体移除逻辑的优化，保持功能一致性)
        if resonance_name in ['热诚之火', '愈疗之水', '迅捷之风', '蔓生之草', '坚定之岩']:
             for char in self.team:
                effects = [e for e in char.active_effects if e.name == resonance_name]
                for effect in effects:
                    effect.remove()
        elif resonance_name == '强能之雷':
            from core.entities.elemental_entities import LightningBladeObject
            for obj in self.active_objects:
                if isinstance(obj, LightningBladeObject):
                    obj.on_finish(None)
        elif resonance_name == '粉碎之冰':
            from core.entities.combat_entities import ShatteredIceObject
            for obj in self.active_objects:
                if isinstance(obj, ShatteredIceObject):
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
        # 兼容逻辑：action 是 (char_name, method, params)
        char_name = action[0]
        
        if char_name == self.current_character.name:
            # 同角色，执行动作
            return self._execute_action(self.current_character, action[1], action[2])
        else:
            # 换人
            if self.swap_cd_timer == 0:
                target_char = self.get_character_by_name(char_name)
                if target_char and self.current_character.state[0] == CharacterState.IDLE:
                    self._perform_switch(target_char)
                    return self._execute_action(self.current_character, action[1], action[2])
            else:
                if self.swap_cd_timer % 30 == 0:
                    get_emulation_logger().log('WARN', f"切换角色CD中 {self.swap_cd_timer}")
        return False

    def _perform_switch(self, new_char):
        event = CharacterSwitchEvent(self.current_character, new_char, frame=GetCurrentTime())
        EventBus.publish(event) # 此时 EventBus 代理到了 Context Engine
        
        old_char = self.current_character
        self.current_character.on_field = False
        new_char.on_field = True
        self.current_character = new_char
        Team.current_character = new_char # 同步静态
        
        self.swap_cd_timer = self.swap_cd
        # 静态 current_frame 用于模拟器的 swap CD 倒计时
        Team.current_frame = self.swap_cd 

    def _execute_action(self, char, method, params):
        # 兼容旧的动作执行逻辑
        # 未来这里将对接 ActionManager
        if (char.state[-1] == CharacterState.IDLE or 
            (char.state[-1] == CharacterState.FALL and method == 'plunging_attack')):
            if hasattr(char, method):
                if params is not None:
                    getattr(char, method)(params)
                else:
                    getattr(char, method)()
                
                # 如果发生了切人，触发切人后事件
                # (原逻辑在这里比较隐晦，放在 swap 里处理)
                return True
        return False

    def update(self, target):
        for character in self.team:
            character.update(target)
        
        self.update_objects(target)

        if self.swap_cd_timer > 0:
            self.swap_cd_timer -= 1
            Team.current_frame = self.swap_cd_timer # 同步

    def update_objects(self, target):
        removed_objects = []
        for obj in self.active_objects:
            obj.update(target)
            if not obj.is_active:
                removed_objects.append(obj)
        for obj in removed_objects:
            self.remove_object(obj)

    @classmethod
    def add_object(cls, obj):
        # 优先添加到 Context 的实例中 (如果有)
        try:
            ctx = get_context()
            if ctx.team:
                ctx.team.active_objects.append(obj)
        except:
            pass
        # 同时也添加到静态列表，保底
        if obj not in cls.active_objects:
            cls.active_objects.append(obj)

    @classmethod
    def remove_object(cls, obj):
        try:
            ctx = get_context()
            if ctx.team and obj in ctx.team.active_objects:
                ctx.team.active_objects.remove(obj)
        except:
            pass
        if obj in cls.active_objects:
            cls.active_objects.remove(obj)
