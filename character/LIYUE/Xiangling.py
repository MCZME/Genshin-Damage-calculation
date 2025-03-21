from character.character import Character
from setup.BaseClass import NormalAttackSkill


class XianLing(Character):
    ID = 11
    def __init__(self,lv,skill_params,constellation=0):
        super().__init__(lv,skill_params,constellation)
        self.association = "璃月"

    def _init_character(self):
        super()._init_character()
        self.NormalAttack = NormalAttackSkill(self.skill_params[0])
        self.NormalAttack.segment_frames = [12,16,26,39,52]
        self.NormalAttack.damageMultipiler = {
            1:[42.05, 45.48, 48.9, 53.79, 57.21, 61.12, 66.5, 71.88, 77.26, 83.13, 89.85, 97.76, 105.67, 113.58, 122.2, ],
            2:[42.14, 45.57, 49, 53.9, 57.33, 61.25, 66.64, 72.03, 77.42, 83.3, 90.04, 97.96, 105.88, 113.81, 122.45, ],
            3:[26.06 + 26.06, 28.18 + 28.18, 30.3 + 30.3, 33.33 + 33.33, 35.45 + 35.45, 37.87 + 37.87, 41.21 + 41.21, 44.54 + 44.54, 47.87 + 47.87, 51.51 + 51.51, 55.68 + 55.68, 60.58 + 60.58, 65.48 + 65.48, 70.37 + 70.37, 75.72 + 75.72, ],
            4:[14.1*4, 15.25*4, 16.4*4, 18.04*4, 19.19*4, 20.5*4, 22.3*4, 24.11*4, 25.91*4, 27.88*4, 30.13*4, 32.79*4, 35.44*4, 38.09*4, 40.98*4, ],
            5:[71.04, 76.82, 82.6, 90.86, 96.64, 103.25, 112.34, 121.42, 130.51, 140.42, 151.78, 165.13, 178.49, 191.85, 206.42, ],
        }