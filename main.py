from setup.BaseEventHandler import NightsoulBurstEventHandler
from setup.DamageCalculation import DamageCalculateEventHandler
from setup.ElementalReaction import ElementalReactionHandler
from setup.Event import EventBus, EventType
from setup.HealingCalculation import HealingCalculateEventHandler

# 初始化
def init():
    
    EventBus.subscribe(EventType.BEFORE_DAMAGE,DamageCalculateEventHandler())
    EventBus.subscribe(EventType.BEFORE_DAMAGE,NightsoulBurstEventHandler())
    EventBus.subscribe(EventType.BEFORE_HEAL,HealingCalculateEventHandler())
    EventBus.subscribe(EventType.BEFORE_ELEMENTAL_REACTION,ElementalReactionHandler())

# todo:
# 1. 暴击率系统
# 2. 元素反应系统
# 3. 技能冷却系统
# 4. 元素能量系统
# 5. 元素共鸣系统
# 6. 护盾系统
# 7. 班尼特
# 8. 夏沃蕾
if __name__ == '__main__':
    init()