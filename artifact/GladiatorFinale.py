from .artifact import Artifact

class GladiatorFinale(Artifact):
    def __init__(self):
        super().__init__('角斗士的终幕礼')

    def tow_SetEffect(self,character):
        attributePanel = character.attributePanel
        attributePanel['攻击力%'] += 18

    def four_SetEffect(self,character):
        ...