import flet as ft
import threading
import time
from ui.theme import GenshinTheme
from ui.views.universe_view import UniverseView
from ui.state import AppState

def start_universe_process(main_to_branch, branch_to_main):
    """分支宇宙进程入口"""
    def main(page: ft.Page):
        page.title = "批处理编辑器"
        # 应用全局主题设置
        GenshinTheme.apply_page_settings(page)
        
        # 1. 在子进程中创建一个独立的状态
        local_state = AppState()
        local_state.register_page(page)
        local_state.main_to_branch = main_to_branch
        local_state.branch_to_main = branch_to_main
        
        # 加载视图
        view = UniverseView(local_state)
        page.add(view)

        # 2. 监听来自主进程的初始化或同步信号
        def main_listener():
            while True:
                try:
                    if not main_to_branch.empty():
                        msg = main_to_branch.get()
                        if msg.get("type") == "INIT_UNIVERSE":
                            # 接收到主进程发送的基准配置
                            config = msg.get("config")
                            # 将其存为本进程状态的 root_config
                            local_state.root_config = config
                            local_state.universe_root.name = "工作台基准"
                            page.run_task(view.refresh)
                except:
                    pass
                time.sleep(0.5)

        threading.Thread(target=main_listener, daemon=True).start()
        
        # 3. 初始刷新延迟 (确保窗口完全挂载)
        async def initial_refresh():
            await asyncio.sleep(0.2)
            view.refresh()
        
        import asyncio
        page.run_task(initial_refresh)
        
        page.update()

    ft.run(main)
