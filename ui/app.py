import flet as ft
import threading
import time
from ui.states.app_state import AppState
from ui.layout import AppLayout
from ui.services.persistence_manager import PersistenceManager
from core.logger import get_ui_logger



def main(page: ft.Page, main_to_branch, branch_to_main):
    # 1. 初始化应用状态
    state = AppState()
    state.register_page(page)
    state.main_to_branch = main_to_branch
    state.branch_to_main = branch_to_main

    # 1.1 初始化持久化服务
    persistence = PersistenceManager(page, state)
    # 将服务注入 Page，方便 View 一键调用
    setattr(page, "persistence", persistence)

    get_ui_logger().log_info("Genshin Workbench main window initialized.")


    # 2. 监听来自分支宇宙的“回传”指令
    def result_listener():
        while True:
            try:
                if not branch_to_main.empty():
                    msg = branch_to_main.get()
                    if msg.get("type") == "APPLY_CONFIG":
                        get_ui_logger().log_info(
                            "Received APPLY_CONFIG command from Batch Editor."
                        )
                        # 分支宇宙要求将某个节点的配置应用到主工作台
                        config = msg.get("config")
                        # 这里调用 state 的加载逻辑
                        page.run_task(state.apply_external_config, config)
            except Exception as e:
                get_ui_logger().log_error(f"Result listener error: {e}")
            time.sleep(0.5)

    threading.Thread(target=result_listener, daemon=True).start()

    # 3. 窗口初始配置
    page.window.width = 1500
    page.window.height = 950
    page.window.min_width = 1200
    page.window.min_height = 800

    # 4. 实例化布局
    layout = AppLayout(page, state, persistence)
    # 将布局实例挂载到 Page 方便访问，但渲染使用声明式方式
    setattr(page, "app_layout", layout)
    
    # 建立声明式渲染根节点 (将 layout_vm 作为参数传入以确保响应式追踪)
    page.render(lambda: layout.build(state.layout_vm))
