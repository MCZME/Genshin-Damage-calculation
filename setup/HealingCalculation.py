from enum import Enum, auto
from character.character import Character
from setup.Event import EventBus, EventHandler, EventType, HealEvent

class HealingType(Enum):
    NORMAL = auto()      # 普通治疗
    SKILL = auto()       # 技能治疗
    BURST = auto()       # 爆发治疗
    PASSIVE = auto()     # 被动治疗

class Healing:
    def __init__(self, base_Multipiler, healing_type: HealingType):
        self.base_Multipiler = base_Multipiler   # 基础倍率
        self.healing_type = healing_type   # 治疗类型
        self.final_value = 0               # 最终治疗量
        self.base_value = '攻击力'

    def set_source(self, source: Character):
        self.source = source

    def set_target(self, target: Character):
        self.target = target

class Calculation:
    def __init__(self, source: Character, target: Character, healing: Healing):
        self.source = source
        self.target = target
        self.healing = healing

    def get_attack(self):
        """获取攻击力"""
        attribute = self.source.attributePanel
        atk0 = attribute['攻击力']
        atk1 = atk0 * attribute['攻击力%'] / 100 + attribute['固定攻击力']
        return atk0 + atk1

    def get_hp(self):
        """获取生命值"""
        attribute = self.source.attributePanel
        hp0 = attribute['生命值']
        hp1 = hp0 * attribute['生命值%'] / 100 + attribute['固定生命值']
        return hp0 + hp1

    def get_Multipiler(self):
        """获取倍率"""
        return self.healing.base_Multipiler/100

    def get_healing_bonus(self):
        """获取治疗加成"""
        return self.source.attributePanel['治疗加成'] / 100

    def get_healed_bonus(self):
        """获取受治疗加成"""
        return self.target.attributePanel['受治疗加成'] / 100

    def calculate_by_attack(self):
        """基于攻击力的治疗计算"""
        value = self.get_attack() * self.get_Multipiler() * (1 + self.get_healing_bonus()) * (1 + self.get_healed_bonus())
        self.healing.final_value = value

    def calculate_by_hp(self):
        """基于生命值的治疗计算"""
        value = self.get_hp() * self.get_Multipiler() * (1 + self.get_healing_bonus()) * (1 + self.get_healed_bonus())
        self.healing.final_value = value

class HealingCalculateEventHandler(EventHandler):
    def handle_event(self, event: HealEvent):
        if event.event_type == EventType.BEFORE_HEAL:
            # 确保目标对象存在
            if not hasattr(event.data['source'], 'attributePanel'):
                return
                
            calculation = Calculation(
                source=event.data['source'],
                target=event.data['target'],
                healing=event.data['healing']
            )
            if event.data['healing'].base_value == '攻击力':
                calculation.calculate_by_attack()
            elif event.data['healing'].base_value == '生命值':
                calculation.calculate_by_hp()
            
            event.data['target'].heal(event.data['healing'].final_value)
            
            # 发布治疗后事件
            after_event = HealEvent(
                source=event.data['source'],
                target=event.data['target'],
                healing=event.data['healing'],
                frame=event.frame,
                before=False
            )
            EventBus().publish(after_event)
