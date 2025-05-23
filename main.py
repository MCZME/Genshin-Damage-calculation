from core.BaseEventHandler import (ElementalEnergyEventHandler, FrameEndEventHandler, 
                                    NightsoulBurstEventHandler, ReactionsEventHandler)
from core.calculation.DamageCalculation import DamageCalculateEventHandler
from core.Config import Config
from core.elementalReaction.ElementalReaction import ElementalReactionHandler
from core.Event import EventBus, EventType
from core.calculation.HealingCalculation import HealingCalculateEventHandler, HurtEventHandler
from core.Logger import logger_init, manage_log_files
from core.calculation.ShieldCalculation import ShieldCalculationEventHandler
from ui.main_window import MainWindow
from PySide6.QtWidgets import QApplication

def init():
    Config()
    logger_init()

# 初始化
def sim_init():
    init()
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
    EventBus.subscribe(EventType.BEFORE_FREEZE,ReactionsEventHandler())
    EventBus.subscribe(EventType.BEFORE_SHATTER,ReactionsEventHandler())
    EventBus.subscribe(EventType.BEFORE_BURNING,ReactionsEventHandler())
    EventBus.subscribe(EventType.BEFORE_BLOOM,ReactionsEventHandler())
    EventBus.subscribe(EventType.BEFORE_HYPERBLOOM,ReactionsEventHandler())
    EventBus.subscribe(EventType.BEFORE_BURGEON,ReactionsEventHandler())
    EventBus.subscribe(EventType.BEFORE_CRYSTALLIZE,ReactionsEventHandler())
    # 激化反应
    EventBus.subscribe(EventType.BEFORE_QUICKEN,ReactionsEventHandler())
    EventBus.subscribe(EventType.BEFORE_AGGRAVATE,ReactionsEventHandler())
    EventBus.subscribe(EventType.BEFORE_SPREAD,ReactionsEventHandler())
    # 增幅反应
    EventBus.subscribe(EventType.BEFORE_VAPORIZE,ReactionsEventHandler())
    EventBus.subscribe(EventType.BEFORE_MELT,ReactionsEventHandler())

    EventBus.subscribe(EventType.FRAME_END, FrameEndEventHandler())
    

# todo:
# 1. 
# 3. 
# 4. 
# 6. 
if __name__ == '__main__':
    sim_init()
    
    # 初始化UI
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()

    Config.save()
    manage_log_files()
