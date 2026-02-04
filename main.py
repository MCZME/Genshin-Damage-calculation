from core.Event import EventType
from core.BaseEventHandler import FrameEndEventHandler
from core.Config import Config
from core.context import create_context, get_context
from core.Logger import logger_init, manage_log_files
from ui.main_window import MainWindow
from PySide6.QtWidgets import QApplication

def init():
    Config()
    logger_init()

# 初始化
def sim_init():
    init()
    # 创建并初始化模拟上下文 (这会自动装配所有核心子系统)
    ctx = create_context()
    
    # 暂时保留 FrameEndEventHandler 用于 UI 更新
    ctx.event_engine.subscribe(EventType.FRAME_END, FrameEndEventHandler())
 # 这种写法不对，还是用 EventBus 代理或者直接指定
    

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
