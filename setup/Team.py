from character.character import Character


# 队伍系统
class Team:

    team = []
    current_character = None

    def __init__(self, team: list[Character] = None):
        if team is not None:
            self.team = team
            self.current_character = team[0]
    
    def clear(self):
        self.team.clear()
        self.current_character = None

    def update(self):
        for character in self.team:
            character.update()