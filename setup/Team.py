from character.character import Character,CharacterState
from setup.BaseClass import SkillSate
from setup.Event import CharacterSwitchEvent, EventBus

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

    def __init__(self, team: list[Character] = None):
        if team is not None:
            self.team = team
            self.current_character = team[0]
    
    def clear(self):
        self.team.clear()
        self.current_character = None
    
    def swqp(self,action):
        if action[0] == self.current_character.name: # 如果是当前角色，则执行动作
            if self.current_character.state == CharacterState.IDLE:
                if hasattr(self.current_character, action[1]):
                    if action[2] is not None:
                        getattr(self.current_character, action[1])(action[2])
                    else:
                        getattr(self.current_character, action[1])()
                    return True
        else: # 如果不是当前角色，则切换角色
            if self.current_frame == 0:
                for character in self.team:
                    if character.name == action[0]:
                        # 获取当前技能类型（SKILL或BURST）
                        if self.current_character.state == CharacterState.SKILL:
                            current_skill = self.current_character.Skill
                        elif self.current_character.state == CharacterState.BURST:
                            current_skill = self.current_character.Burst
                        else:
                            current_skill = None
                        
                        if (self.current_character.state == CharacterState.IDLE or 
                           (current_skill is not None and current_skill.state == SkillSate.OffField)):
                            
                            # 执行切换
                            character_switch_event = CharacterSwitchEvent(self.current_character, character)
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
                print("切换角色CD中  {}".format(self.current_frame))
        return False


    def update(self,target):
        for character in self.team:
            character.update(target)
        if self.current_frame > 0:
            self.current_frame -= 1