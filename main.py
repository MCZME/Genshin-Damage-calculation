


from setup.DamageCalculation import DamageCalculateEventHandler
from setup.Event import EventBus, EventType

# 初始化
def init():
    
    EventBus.subscribe(EventType.BEFORE_DAMAGE,DamageCalculateEventHandler())

# todo:
# 马薇卡 元素战技和元素爆发
if __name__ == '__main__':
    init()