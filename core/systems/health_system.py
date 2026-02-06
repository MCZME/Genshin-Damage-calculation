from typing import Union, Tuple
from core.systems.utils import AttributeCalculator
from core.systems.base_system import GameSystem
from core.context import EventEngine
from core.event import EventType, GameEvent, HealEvent, HurtEvent
from core.action.healing import Healing
from core.logger import get_emulation_logger

# ---------------------------------------------------------
# Healing Calculation Helper
# ---------------------------------------------------------
class Calculation:
    def __init__(self, source, target, healing: Healing):
        self.source = source
        self.target = target
        self.healing = healing

    def get_attack(self):
        """获取攻击力"""
        entity = self.source if self.healing.multiplier_provider == '来源' else self.target
        return AttributeCalculator.get_attack(entity)

    def get_hp(self):
        """获取生命值"""
        entity = self.source if self.healing.multiplier_provider == '来源' else self.target
        return AttributeCalculator.get_hp(entity)

    def get_defense(self):
        """获取防御力"""
        entity = self.source if self.healing.multiplier_provider == '来源' else self.target
        return AttributeCalculator.get_defense(entity)

    def get_multiplier(self) -> Union[float, Tuple[float, float]]:
        """获取倍率"""
        return self.healing.base_multiplier

    def get_healing_bonus(self):
        """获取治疗加成"""
        return self.source.attributePanel['治疗加成'] / 100

    def get_healed_bonus(self):
        """获取受治疗加成"""
        return self.target.attributePanel['受治疗加成'] / 100

    def calculate_by_attack(self):
        """基于攻击力的治疗计算"""
        m = self.get_multiplier()
        if isinstance(m, tuple):
            value = (m[0]/100)*self.get_attack() + m[1]
        else:
            value = (m/100) * self.get_attack()
        value = value * (1 + self.get_healing_bonus()) * (1 + self.get_healed_bonus())
        self.healing.final_value = value

    def calculate_by_hp(self):
        """基于生命值的治疗计算"""
        m = self.get_multiplier()
        if isinstance(m, tuple):
            value = (m[0]/100)*self.get_hp() + m[1]
        else:
            value = (m/100) * self.get_hp()
        value = value * (1 + self.get_healing_bonus()) * (1 + self.get_healed_bonus())
        self.healing.final_value = value

    def calculate_by_defense(self):
        """基于防御力的治疗计算"""
        m = self.get_multiplier()
        if isinstance(m, tuple):
            value = (m[0]/100)*self.get_defense() + m[1]
        else:
            value = (m/100) * self.get_defense()
        value = value * (1 + self.get_healing_bonus()) * (1 + self.get_healed_bonus())
        self.healing.final_value = value

# ---------------------------------------------------------
# Health System
# ---------------------------------------------------------
class HealthSystem(GameSystem):
    def register_events(self, engine: EventEngine):
        engine.subscribe(EventType.BEFORE_HEAL, self)
        engine.subscribe(EventType.BEFORE_HURT, self)

    def handle_event(self, event: GameEvent):
        if event.event_type == EventType.BEFORE_HEAL:
            self._handle_heal(event)
        elif event.event_type == EventType.BEFORE_HURT:
            self._handle_hurt(event)

    def _handle_heal(self, event: HealEvent):
        if not hasattr(event.data['character'], 'attributePanel'):
            return
            
        calculation = Calculation(
            source=event.data['character'],
            target=event.data['target'],
            healing=event.data['healing']
        )
        
        base_value = event.data['healing'].base_value
        if base_value == '攻击力':
            calculation.calculate_by_attack()
        elif base_value == '生命值':
            calculation.calculate_by_hp()
        elif base_value == '防御力':
            calculation.calculate_by_defense()
        
        # 执行治疗
        event.data['target'].heal(event.data['healing'].final_value)

        get_emulation_logger().log_heal(
            event.data["character"], 
            event.data["target"], 
            event.data["healing"]
        )
        
        # 发布治疗后事件
        after_event = HealEvent(
            source=event.data['character'],
            target=event.data['target'],
            healing=event.data['healing'],
            frame=event.frame,
            before=False
        )
        self.engine.publish(after_event)

    def _handle_hurt(self, event: GameEvent):
        # 执行扣血
        event.data['target'].hurt(event.data['amount'])
        get_emulation_logger().log('HURT', f"💔 {event.data['target'].name} 受到 {event.data['amount']:.2f} 点伤害")

        after_event = HurtEvent(
            event.data['character'], 
            event.data['target'], 
            event.data['amount'], 
            event.frame, 
            before=False
        )
        self.engine.publish(after_event)
