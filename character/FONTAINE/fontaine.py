from character.character import Character

class Fontaine(Character):

    def __init__(self, id: int = 1, level: int = 1, skill_params: list = None, constellation: int = 0, base_data: dict = None):
        super().__init__(id, level, skill_params, constellation, base_data)
        self.association = "枫丹"

    def _setup_character_components(self):
        super()._setup_character_components()
        self.arkhe = '荒性'

    def _setup_effects(self):
        super()._setup_effects()