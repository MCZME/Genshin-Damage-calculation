from character.character import Character, CharacterState
from core.Effect.BaseEffect import AttackBoostEffect, HealthBoostEffect
from core.Event import CharacterSwitchEvent, EventBus
from core.Logger import get_emulation_logger
from core.Tool import GetCurrentTime

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

# 队伍系统
class Team:
    team = []
    current_character = None
    current_frame = 0
    SwapCd = 60
    element_counts = {}
    active_resonances = {}
    active_objects = []

    def __init__(self, team: list[Character] = None):
        if team is not None:
            Team.team = team
            Team.current_character = Character()
            Team.current_character.on_field = True
            self._update_element_counts()
            self._apply_resonance_effects()

    def _update_element_counts(self):
        Team.element_counts = {}
        for char in Team.team:
            element = char.element
            Team.element_counts[element] = Team.element_counts.get(element, 0) + 1

    def _apply_resonance_effects(self):
        # 清除不再满足条件的共鸣效果
        for resonance in list(Team.active_resonances.keys()):
            if not self._check_resonance_condition(resonance):
                self._remove_resonance(resonance)

        # 火元素共鸣（热诚之火）
        if Team.element_counts.get('火', 0) >= 2 and len(Team.team) >= 4:
            if '热诚之火' not in Team.active_resonances:
                for char in Team.team:
                    effect = AttackBoostEffect(char, "热诚之火", 25, float('inf'))
                    effect.apply()
                Team.active_resonances['热诚之火'] = True

        # 水元素共鸣（愈疗之水）
        if Team.element_counts.get('水', 0) >= 2 and len(Team.team) >= 4:
            if '愈疗之水' not in Team.active_resonances:
                for char in Team.team:
                    effect = HealthBoostEffect(char, "愈疗之水", 25, float('inf'))
                    effect.apply()
                Team.active_resonances['愈疗之水'] = True

        # 雷元素共鸣（强能之雷）
        if Team.element_counts.get('雷', 0) >= 2 and len(Team.team) >= 4:
            if '强能之雷' not in Team.active_resonances:
                from core.BaseObject import LightningBladeObject
                LightningBladeobject = LightningBladeObject()
                LightningBladeobject.apply()
                Team.active_resonances['强能之雷'] = True
        
    def _check_resonance_condition(self, resonance_name):
        # 各共鸣的触发条件检查
        if resonance_name == '热诚之火':
            return Team.element_counts.get('火', 0) >= 2 and len(Team.team) >= 4
        elif resonance_name == '愈疗之水':
            return Team.element_counts.get('水', 0) >= 2 and len(Team.team) >= 4
        elif resonance_name == '强能之雷':
            return Team.element_counts.get('雷', 0) >= 2 and len(Team.team) >= 4
        return False

    def _remove_resonance(self, resonance_name):
        if resonance_name == '热诚之火':
            for char in Team.team:
                effects = [e for e in char.active_effects if e.name == "热诚之火"]
                for effect in effects:
                    effect.remove()
        elif resonance_name == '愈疗之水':
            for char in Team.team:
                effects = [e for e in char.active_effects if e.name == "愈疗之水"]
                for effect in effects:
                    effect.remove()
        elif resonance_name == '强能之雷':
            for obj in Team.active_objects:
                from core.BaseObject import LightningBladeObject
                if isinstance(obj, LightningBladeObject):
                    obj.remove()
        Team.active_resonances.pop(resonance_name, None)
    
    def clear(self):
        Team.team.clear()
        Team.active_objects.clear()
        Team.active_resonances.clear()
        Team.current_character = None
        Team.current_frame = 0
    
    def swap(self,action):
        if action[0] == Team.current_character.name: # 如果是当前角色，则执行动作
            if (Team.current_character.state[-1] == CharacterState.IDLE or 
                (Team.current_character.state[-1] == CharacterState.FALL and action[1] == 'plunging_attack')):
                if hasattr(Team.current_character, action[1]):
                    if action[2] is not None:
                        getattr(Team.current_character, action[1])(action[2])
                    else:
                        getattr(Team.current_character, action[1])()
                    return True
            return False  # 状态不允许执行新动作
        else: # 如果不是当前角色，则切换角色
            if Team.current_frame == 0:
                for character in Team.team:
                    if character.name == action[0]:
                        if (Team.current_character.state[0] == CharacterState.IDLE):
                            
                            # 执行切换
                            character_switch_event = CharacterSwitchEvent(Team.current_character, character,frame=GetCurrentTime())
                            EventBus.publish(character_switch_event)
                            old_character = Team.current_character
                            Team.current_character.on_field = False
                            character.on_field = True
                            Team.current_character = character
                            Team.current_frame = self.SwapCd
                            
                            # 执行新角色动作
                            if hasattr(Team.current_character, action[1]):
                                if action[2] is not None:
                                    getattr(Team.current_character, action[1])(action[2])
                                else:
                                    getattr(Team.current_character, action[1])()
                                character_switch_event = CharacterSwitchEvent(old_character, Team.current_character,frame=GetCurrentTime(),before=False)
                                EventBus.publish(character_switch_event)
                                return True
            else:
                if Team.current_frame %30 == 0:
                    print("切换角色CD中  {}".format(Team.current_frame))
        return False

    def update(self,target):
        for character in Team.team:
            character.update(target)
        
        self.update_objects()

        if Team.current_frame > 0:
            Team.current_frame -= 1

    def update_objects(self):
        removed_objects = []
        for object in Team.active_objects:
            object.update()
            if not object.is_active:
                removed_objects.append(object)
        for object in removed_objects:
            Team.active_objects.remove(object)

    @classmethod
    def add_object(self,object):
        Team.active_objects.append(object)

    @classmethod
    def remove_object(self,object):
        Team.active_objects.remove(object)