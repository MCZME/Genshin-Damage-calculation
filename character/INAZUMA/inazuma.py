from character.character import Character


class Inazuma(Character):
    def __init__(self, id=1, level=1, skill_params=..., constellation=0):
        super().__init__(id, level, skill_params, constellation)
        self.association = "稻妻"