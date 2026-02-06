from core.action.damage import DamageType
from core.tool import summon_energy
from weapon.weapon import Weapon
from core.event import EventBus, EventType, EventHandler
from core.effect.stat_modifier import AttackBoostEffect
from core.registry import register_weapon

@register_weapon("香韵奏者", "长柄武器")
class SymphonistOfScents(Weapon, EventHandler):
    ID = 217
    def __init__(self, character, level=1, lv=1):
        super().__init__(character, SymphonistOfScents.ID, level, lv)
        self.atk_boost_1 = [12,15,18,21,24]
        self.atk_boost_2 = [32,40,48,56,64]
        self.is_applied = False

    def skill(self):
        self.character.attribute_panel["攻击力%"] += self.atk_boost_1[self.lv-1]

        EventBus.subscribe(EventType.AFTER_HEAL, self)

    def handle_event(self, event):
        if event.data["healing"].source is not self.character:
            return
        
        AttackBoostEffect(
            character=self.character,
            current_character=event.data["healing"].source,
            name="香韵奏者",
            bonus=self.atk_boost_2[self.lv-1],
            duration=3*60
        ).apply()
        AttackBoostEffect(
            character=self.character,
            current_character=event.data["healing"].target,
            name="香韵奏者",
            bonus=self.atk_boost_2[self.lv-1],
            duration=3*60
        ).apply()

    def update(self, target):
        if not self.is_applied and not self.character.on_field:
            self.character.attribute_panel["攻击力%"] += self.atk_boost_1[self.lv-1]
            self.is_applied = True
        elif self.is_applied and self.character.on_field:
            self.character.attribute_panel["攻击力%"] -= self.atk_boost_1[self.lv-1]
            self.is_applied = False
