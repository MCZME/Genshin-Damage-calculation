from setup.BaseEventHandler import NightsoulBurstEventHandler
from setup.DamageCalculation import DamageCalculateEventHandler
from setup.Event import EventBus, EventType
from setup.HealingCalculation import HealingCalculateEventHandler

# 初始化
def init():
    
    EventBus.subscribe(EventType.BEFORE_DAMAGE,DamageCalculateEventHandler())
    EventBus.subscribe(EventType.BEFORE_DAMAGE,NightsoulBurstEventHandler())
    EventBus.subscribe(EventType.BEFORE_HEAL,HealingCalculateEventHandler())
# todo:
if __name__ == '__main__':
    init()