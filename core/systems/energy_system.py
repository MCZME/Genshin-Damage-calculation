from core.systems.utils import AttributeCalculator
from core.systems.base_system import GameSystem
from core.context import EventEngine
from core.event import EventType, GameEvent, EnergyChargeEvent
from core.logger import get_emulation_logger
from core.tool import GetCurrentTime

class EnergySystem(GameSystem):
    def register_events(self, engine: EventEngine):
        engine.subscribe(EventType.BEFORE_ENERGY_CHANGE, self)

    def handle_event(self, event: GameEvent):
        if event.event_type == EventType.BEFORE_ENERGY_CHANGE:
            self._handle_energy_change(event)

    def _handle_energy_change(self, event: GameEvent):
        amount = event.data['amount']
        
        # 获取 team (通过 context)
        team_obj = self.context.team if self.context else None
        if not team_obj:
            return

        source_character = event.data.get('character')
        if event.data['is_alone']:
            character = event.data['character']
            self._apply_energy(character, amount, event.data['is_fixed'], event.data['is_alone'], team_obj, source_character)
        else:
            for character in team_obj.team:
                self._apply_energy(character, amount, event.data['is_fixed'], event.data['is_alone'], team_obj, source_character)

    def _apply_energy(self, character, amount, is_fixed, is_alone, team_obj, source_character):
        if is_fixed:
            emergy_value = min(amount[1], 
                                   character.elemental_energy.elemental_energy[1] -
                                   character.elemental_energy.current_energy)
            character.elemental_energy.current_energy += emergy_value
        else:
            rate = self.get_rate(character, amount[0], team_obj)
            emergy_value = amount[1] * rate[0] * rate[1] * rate[2]
            emergy_value = min(emergy_value, 
                                   character.elemental_energy.elemental_energy[1] -
                                   character.elemental_energy.current_energy)
            character.elemental_energy.current_energy += emergy_value
            
        # 修复作用域错误：使用传入的 source_character
        if is_alone or (not is_alone and character == source_character): 
             get_emulation_logger().log_energy(character, emergy_value)

        e_event = EnergyChargeEvent(character, (amount[0], emergy_value),
                                    GetCurrentTime(),
                                    before=False,
                                    is_fixed=is_fixed,
                                    is_alone=is_alone)
        self.engine.publish(e_event)

    def get_rate(self, character, element, team_obj):
        l = len(team_obj.team)
        if character.on_field:
            team_rate = 1.0
        elif l == 2:
            team_rate = 0.8
        elif l == 3:
            team_rate = 0.7
        else:
            team_rate = 0.6

        if character.elemental_energy.elemental_energy[0] == element:
            element_rate = 1.5
        elif element == '无':
            element_rate = 1.0
        else:
            element_rate = 0.5
        emergy_rate = AttributeCalculator.get_energy_recharge(character)
        
        return (team_rate, element_rate, emergy_rate)
