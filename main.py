from nicegui import ui
from core.config import Config
from core.logger import logger_init
import os

# --- 初始化 ---
def init_all():
    Config()
    logger_init()

@ui.page('/')
def index_page():
    with ui.column().classes('w-full items-center p-8'):
        ui.label('原神伤害计算器 (V2)').classes('text-4xl font-bold text-primary mb-4')
        ui.markdown('基于 **NiceGUI** 与 **V2 场景引擎** 的现代化重构版。').classes('text-lg text-gray-600')
        
        with ui.row().classes('mt-8 gap-4'):
            ui.button('模拟配置', on_click=lambda: ui.navigate.to('/config'), icon='settings').props('elevated')
            ui.button('结果分析', on_click=lambda: ui.navigate.to('/analysis'), icon='analytics', color='secondary').props('elevated')

# 导入页面 (触发路由注册)
from ui.pages import config as _config_page
# import ui.pages.analysis as _analysis_page # 后续实现

if __name__ in {"__main__", "__mp_main__"}:
    init_all()
    ui.run(
        title='Genshin Damage Calc V2',
        port=8080,
        dark=False,
        favicon='🚀'
    )