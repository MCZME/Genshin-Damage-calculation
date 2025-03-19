from character.character import Character, CharacterState
from setup.BaseEffect import AttackBoostEffect, HealthBoostEffect
from setup.BaseClass import SkillSate
from setup.Event import CharacterSwitchEvent, EventBus
from setup.Tool import GetCurrentTime

# 转化字典
action_state = {
    "normal_attack": CharacterState.NORMAL_ATTACK,
    "heavy_attack": CharacterState.HEAVY_ATTACK,
    "elemental_skill": CharacterState.SKILL,
    "elemental_burst": CharacterState.BURST
}

# 队伍系统
class Team:
    team = []
    current_character = None
    current_frame = 0
    SwapCd = 60
    element_counts = {}
    active_resonances = {}

    def __init__(self, team: list[Character] = None):
        if team is not None:
            self.team = team
            self.current_character = team[0]
            self.current_character.on_field = True
            self._update_element_counts()
            self._apply_resonance_effects()

    def _update_element_counts(self):
        self.element_counts = {}
        for char in self.team:
            element = char.element
            self.element_counts[element] = self.element_counts.get(element, 0) + 1

    def _apply_resonance_effects(self):
        # 清除不再满足条件的共鸣效果
        for resonance in list(self.active_resonances.keys()):
            if not self._check_resonance_condition(resonance):
                self._remove_resonance(resonance)

        # 火元素共鸣（热诚之火）
        if self.element_counts.get('火', 0) >= 2 and len(self.team) >= 4:
            if '热诚之火' not in self.active_resonances:
                for char in self.team:
                    effect = AttackBoostEffect(char, "热诚之火", 25, float('inf'))
                    effect.apply()
                self.active_resonances['热诚之火'] = True

        # 水元素共鸣（愈疗之水）
        if self.element_counts.get('水', 0) >= 2 and len(self.team) >= 4:
            if '愈疗之水' not in self.active_resonances:
                for char in self.team:
                    effect = HealthBoostEffect(char, "愈疗之水", 25, float('inf'))
                    effect.apply()
                self.active_resonances['愈疗之水'] = True

        # 其他元素共鸣占位结构...
        
    def _check_resonance_condition(self, resonance_name):
        # 各共鸣的触发条件检查
        if resonance_name == '热诚之火':
            return self.element_counts.get('火', 0) >= 2 and len(self.team) >= 4
        elif resonance_name == '愈疗之水':
            return self.element_counts.get('水', 0) >= 2 and len(self.team) >= 4
        # 其他共鸣条件检查...
        return False

    def _remove_resonance(self, resonance_name):
        if resonance_name == '热诚之火':
            for char in self.team:
                effects = [e for e in char.active_effects if e.name == "热诚之火"]
                for effect in effects:
                    effect.remove()
        elif resonance_name == '愈疗之水':
            for char in self.team:
                effects = [e for e in char.active_effects if e.name == "愈疗之水"]
                for effect in effects:
                    effect.remove()
        self.active_resonances.pop(resonance_name, None)
    
    def clear(self):
        self.team.clear()
        self.current_character = None
    
    def swap(self,action):
         # 获取当前技能类型（SKILL或BURST）
        if self.current_character.state[-1] == CharacterState.SKILL:
            current_skill = self.current_character.Skill
        elif self.current_character.state[-1] == CharacterState.BURST:
            current_skill = self.current_character.Burst
        else:
            current_skill = None

        if action[0] == self.current_character.name: # 如果是当前角色，则执行动作
            if (self.current_character.state[-1] == CharacterState.IDLE or 
                (current_skill is not None and current_skill.state == SkillSate.OffField)):
                if hasattr(self.current_character, action[1]):
                    if action[2] is not None:
                        getattr(self.current_character, action[1])(action[2])
                    else:
                        getattr(self.current_character, action[1])()
                    return True
            return False  # 状态不允许执行新动作
        else: # 如果不是当前角色，则切换角色
            if self.current_frame == 0:
                for character in self.team:
                    if character.name == action[0]:
                        if (self.current_character.state[0] == CharacterState.IDLE or 
                           (current_skill is not None and current_skill.state == SkillSate.OffField)):
                            
                            # 执行切换
                            character_switch_event = CharacterSwitchEvent(self.current_character, character,frame=GetCurrentTime())
                            self.current_character.on_field = False
                            character.on_field = True
                            self.current_character = character
                            self.current_frame = self.SwapCd
                            EventBus.publish(character_switch_event)
                            
                            # 执行新角色动作
                            if hasattr(self.current_character, action[1]):
                                if action[2] is not None:
                                    getattr(self.current_character, action[1])(action[2])
                                else:
                                    getattr(self.current_character, action[1])()
                                return True
            else:
                if self.current_frame %30 == 0:
                    print("切换角色CD中  {}".format(self.current_frame))
        return False

    def update(self,target):
        for character in self.team:
            character.update(target)
        if self.current_frame > 0:
            self.current_frame -= 1
