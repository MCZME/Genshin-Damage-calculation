from setup.BaseEventHandler import ElementalEnergyEventHandler, FrameEndEventHandler, NightsoulBurstEventHandler
from setup.Config import Config
from setup.DamageCalculation import DamageCalculateEventHandler
from setup.ElementalReaction import ElementalReactionHandler
from setup.Event import EventBus, EventType
from setup.HealingCalculation import HealingCalculateEventHandler
from setup.Logger import logger_init, manage_log_files
from setup.ShieldCalculation import ShieldCalculationEventHandler
from ui.main_window import MainWindow
from PySide6.QtWidgets import QApplication

# 初始化
def init():
    Config()
    EventBus.subscribe(EventType.BEFORE_DAMAGE,DamageCalculateEventHandler())
    EventBus.subscribe(EventType.BEFORE_DAMAGE,NightsoulBurstEventHandler())
    EventBus.subscribe(EventType.BEFORE_HEAL,HealingCalculateEventHandler())
    EventBus.subscribe(EventType.BEFORE_SHIELD_CREATION,ShieldCalculationEventHandler())
    EventBus.subscribe(EventType.BEFORE_ELEMENTAL_REACTION,ElementalReactionHandler())
    EventBus.subscribe(EventType.BEFORE_ENERGY_CHANGE, ElementalEnergyEventHandler())
    EventBus.subscribe(EventType.FRAME_END, FrameEndEventHandler())
    logger_init()

# todo:
# 1. 暴击率系统
# 2. 元素反应系统
# 3. 
# 4. 
# 5. 元素共鸣系统
# 6. 护盾系统
# 7. 冲刺
# 8. 数据处理
# 9. 茜特菈莉
if __name__ == '__main__':
    init()
    
    # 初始化UI
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()

    Config.save()
    # manage_log_files()
