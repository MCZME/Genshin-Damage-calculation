from core.systems.base_system import GameSystem
from core.event import GameEvent, EventType
from core.systems.utils import AttributeCalculator
from core.logger import get_emulation_logger

class EnergySystem(GameSystem):
    """
    能量系统：处理微粒/球获取及固定数值恢复。
    """
    def register_events(self, engine):
        engine.subscribe(EventType.BEFORE_ENERGY_CHANGE, self)

    def handle_event(self, event: GameEvent):
        if event.event_type == EventType.BEFORE_ENERGY_CHANGE:
            self._handle_energy_change(event)

    def _handle_energy_change(self, event: GameEvent):
        data = event.data
        character = data['character']
        amount = data['amount']
        is_fixed = data.get('is_fixed', False)
        is_alone = data.get('is_alone', False)
        
        team_obj = getattr(self.context, 'team', None)
        source_character = data.get('source_character', character)

        self._apply_energy(character, amount, is_fixed, is_alone, team_obj, source_character)

    def _apply_energy(self, character, amount, is_fixed, is_alone, team_obj, source_character):
        if is_fixed:
            # amount 可能是 tuple ('火', 5.0) 或直接是 float 5.0
            val = amount[1] if isinstance(amount, tuple) else amount
            energy_value = min(val, 
                               character.elemental_energy.elemental_energy[1] - 
                               character.elemental_energy.current_energy)
            character.elemental_energy.current_energy += energy_value
            get_emulation_logger().log_energy(character, energy_value, source_type="固定值")
        else:
            # 这里的 amount 必须是 tuple (element, count)
            rate = self.get_rate(character, amount[0], team_obj)
            energy_value = amount[1] * rate
            character.elemental_energy.current_energy += energy_value
            get_emulation_logger().log_energy(character, energy_value, source_type=f"{amount[0]}元素微粒")

    def get_rate(self, character, particle_element, team_obj):
        """计算微粒获取系数"""
        # 基础系数表 (同元素/异元素/无元素 x 站场/后台)
        is_same = (particle_element == character.elemental_energy.elemental_energy[0])
        is_neutral = (particle_element == '无')
        on_field = getattr(character, 'on_field', True)

        # 简化版系数
        if is_neutral:
            base = 2.0 if on_field else 1.2
        elif is_same:
            base = 3.0 if on_field else 1.8
        else:
            base = 1.0 if on_field else 0.6

        # 充能效率加成
        energy_rate = AttributeCalculator.get_energy_recharge(character)
        return base * energy_rate