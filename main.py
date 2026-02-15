import multiprocessing
import flet as ft

# 核心导入移至顶部
from core.logger import logger_init, get_ui_logger, manage_log_files
from core.registry import initialize_registry
from ui.app import main as flet_main

def init_all():
    """初始化全局系统。"""
    # 1. 注册核心组件
    initialize_registry()
    
    # 2. 初始化日志
    logger_init()
    
    # 3. 日志管理：清理/压缩旧日志
    # manage_log_files(max_files=30)
    
    get_ui_logger().log_info("系统初始化完成")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    # 执行初始化
    init_all()

    # 建立双向通信队列
    # 1. main_to_branch: 发送初始化配置或指令
    # 2. branch_to_main: 发送选中的节点配置回主界面
    main_to_branch = multiprocessing.Queue()
    branch_to_main = multiprocessing.Queue()
    
    # 启动主 UI，注入两个队列
    ft.run(
        lambda page: flet_main(page, main_to_branch, branch_to_main), 
        port=8550, 
        view=ft.AppView.FLET_APP
    )
