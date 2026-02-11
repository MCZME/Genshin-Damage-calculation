import flet as ft
import multiprocessing
import os
import sys

# --- 必须在任何业务导入之前初始化配置 ---
from core.config import Config

# 确保能找到 config.json
config_path = os.path.join(os.path.dirname(__file__), "config.json")
Config(config_path)

# --- 现在可以安全导入其他模块 ---
from core.logger import logger_init
from core.registry import initialize_registry
from ui.app import main as flet_main

def init_all():
    """初始化后端引擎"""
    logger_init()
    initialize_registry()

if __name__ == "__main__":
    # Windows 平台支持
    multiprocessing.freeze_support()
    
    # 初始化后端
    init_all()
    
    # 建立双向通信队列
    # 1. main_to_branch: 发送初始化配置或指令
    # 2. branch_to_main: 发送选中的节点配置回主界面
    main_to_branch = multiprocessing.Queue()
    branch_to_main = multiprocessing.Queue()
    
    print("🚀 Starting Genshin Simulation Workbench V3.0...")
    
    # 启动主 UI，注入两个队列
    ft.run(
        lambda page: flet_main(page, main_to_branch, branch_to_main), 
        port=8550, 
        view=ft.AppView.FLET_APP
    )
