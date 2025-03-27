from character.NATLAN.natlan import Natlan


class CITLALI(Natlan):
    ID = 93
    def __init__(self, level, skill_params, constellation=0):
        super().__init__(self.ID, level, skill_params, constellation)

    def _init_character(self):
        super()._init_character()
        

citlali_table = {
    'id':CITLALI.ID,
    'name':'茜特菈莉',
}