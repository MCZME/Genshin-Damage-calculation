from core.BaseEventHandler import (ElementalEnergyEventHandler, FrameEndEventHandler, 
                                    NightsoulBurstEventHandler, ReactionsEventHandler)
from core.calculation.DamageCalculation import DamageCalculateEventHandler
from core.Config import Config
from core.ElementalReaction import ElementalReactionHandler
from core.Event import EventBus, EventType
from core.calculation.HealingCalculation import HealingCalculateEventHandler, HurtEventHandler
from core.Logger import logger_init, manage_log_files
from core.calculation.ShieldCalculation import ShieldCalculationEventHandler
from ui.main_window import MainWindow
from PySide6.QtWidgets import QApplication

# 初始化
def init():
    Config()
    EventBus.subscribe(EventType.BEFORE_DAMAGE,DamageCalculateEventHandler())
    EventBus.subscribe(EventType.BEFORE_DAMAGE,NightsoulBurstEventHandler())
    EventBus.subscribe(EventType.BEFORE_HEAL,HealingCalculateEventHandler())
    EventBus.subscribe(EventType.BEFORE_HURT,HurtEventHandler())
    EventBus.subscribe(EventType.BEFORE_SHIELD_CREATION,ShieldCalculationEventHandler())
    EventBus.subscribe(EventType.BEFORE_ELEMENTAL_REACTION,ElementalReactionHandler())
    EventBus.subscribe(EventType.BEFORE_ENERGY_CHANGE, ElementalEnergyEventHandler())
    # 剧变反应
    EventBus.subscribe(EventType.BEFORE_OVERLOAD,ReactionsEventHandler())
    EventBus.subscribe(EventType.BEFORE_SWIRL,ReactionsEventHandler())
    EventBus.subscribe(EventType.BEFORE_SUPERCONDUCT,ReactionsEventHandler())
    EventBus.subscribe(EventType.BEFORE_ELECTRO_CHARGED,ReactionsEventHandler())
    # 增幅反应
    EventBus.subscribe(EventType.BEFORE_VAPORIZE,ReactionsEventHandler())
    EventBus.subscribe(EventType.BEFORE_MELT,ReactionsEventHandler())

    EventBus.subscribe(EventType.FRAME_END, FrameEndEventHandler())
    logger_init()

# todo:
# 1. 
# 2. 元素反应系统
# 3. 
# 4. 
# 5. 元素共鸣系统
# 6. 
if __name__ == '__main__':
    init()
    
    # 初始化UI
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()

    Config.save()
    # manage_log_files()
