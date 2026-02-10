from core.config import Config
# 1. 核心配置初始化 (必须最先执行)
Config()

import flet as ft
from core.logger import logger_init
from core.registry import initialize_registry
from ui.app import main as flet_main

def init_all():
    """初始化后端引擎"""
    logger_init()
    initialize_registry()

if __name__ == "__main__":
    # --- 仅在主进程中执行 ---
    
    # 2. 后端引擎初始化
    init_all()
    
    # 3. 启动 Flet UI (Workbench V3.0)
    print("🚀 Starting Genshin Simulation Workbench V3.0 (Main Process)...")
    ft.run(flet_main)

elif __name__ == "__mp_main__":
    # --- 在子进程中执行 ---
    # 子进程不需要启动 UI，其初始化逻辑已在 core/batch/runner.py 的 simulation_worker 中独立处理
    pass