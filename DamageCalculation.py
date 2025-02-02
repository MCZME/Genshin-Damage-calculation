import DataRequest as dr

class Calculation:
    def __init__(self):

        pass

    def attack(self):
        pass

    def damageMultipiler(self):
        pass

    def damageBonus(self):
        pass

    def criticalBracket(self):
        pass

    def defense(self):
        pass

    def resistance(self):
        pass

    def reaction(self):
        pass

    def calculation(self):
        damage = self.attack() * self.damageMultipiler() * (1 + self.damageBonus()) * (1 + self.criticalBracket()) * self.defense() * self.resistance() * self.reaction()
        return damage

