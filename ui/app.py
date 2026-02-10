import flet as ft
from ui.state import AppState
from ui.layout import AppLayout

def main(page: ft.Page):
    # 1. 初始化应用状态
    state = AppState(page)
    
    # 2. 窗口初始配置 (部分将由 AppLayout.setup_page 覆盖)
    page.window_width = 1500
    page.window_height = 950
    page.window_min_width = 1200
    page.window_min_height = 800
    
    # 3. 实例化 MD3 Panes 布局
    # 将 state 传入布局，以便子组件可以访问数据
    layout = AppLayout(page, state)
    
    # 4. 挂载布局
    page.add(layout.build())
    
    # 5. 初始数据刷新
    # 确保左侧实体池等组件显示 state 中的初始数据
    # layout.entity_pool.update_team(state.team)
    
    page.update()

if __name__ == "__main__":
    # 调试模式启动
    ft.app(target=main)
