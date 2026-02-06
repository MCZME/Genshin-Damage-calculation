from core.config import Config
from core.context import create_context
from core.logger import logger_init, manage_log_files
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
