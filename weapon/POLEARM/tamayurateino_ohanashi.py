from core.action.damage import DamageType
from core.tool import summon_energy
from weapon.weapon import Weapon
from core.event import EventBus, EventType, EventHandler
from core.effect.stat_modifier import AttackBoostEffect
from core.registry import register_weapon

@register_weapon("且住亭御咄", "长柄武器")
class TamayurateinoOhanashi(Weapon, EventHandler):
    ID = 161
    def __init__(self, character, level=1, lv=1):
        super().__init__(character, TamayurateinoOhanashi.ID, level, lv)
        self.attack_boost = [20,25,30,35,40]

        EventBus.subscribe(EventType.BEFORE_SKILL, self)

    def handle_event(self, event):
        if event.data["character"] == self.character:
            effect = AttackBoostEffect(
                character=self.character,
                current_character=self.character,
                name="且住亭御咄", 
                bonus=self.attack_boost[self.lv-1],
                duration=10*60
            )
            effect.apply()
