from character.character import Character,CharacterState

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
        if action[0] == self.current_character.name:
            if self.current_character.state == CharacterState.IDLE:
                if hasattr(self.current_character, action[1]):
                    getattr(self.current_character, action[1])()
                    return True
        else:
            if self.current_frame == 0:
                for character in self.team:
                    if character.name == action[0]:
                        self.current_character = character
                        self.current_frame = self.SwapCd
                        if hasattr(self.current_character, action[1]):
                            getattr(self.current_character, action[1])()
                            return True
        return False


    def update(self,target):
        for character in self.team:
            character.update(target)
        if self.current_frame > 0:
            self.current_frame -= 1