from typing import Any


class ElementalEnergy:
    def __init__(self, character: Any, ee: tuple[str, int] = ("无", 0)):
        self.character = character
        self.elemental_energy = ee
        self.current_energy = ee[1]

    def is_energy_full(self) -> bool:
        return self.current_energy >= self.elemental_energy[1]

    def clear_energy(self):
        self.current_energy = 0
