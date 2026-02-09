from core.config import Config
# 必须在导入任何业务模块（如 ui.pages）之前初始化配置
Config()

from nicegui import ui
from core.logger import logger_init
from core.registry import initialize_registry
import os

# --- 初始化 ---
def init_all():
    logger_init()
    initialize_registry()

@ui.page('/')
def index_page():
    with ui.column().classes('w-full items-center p-8'):
        ui.label('原神伤害计算器 (V2)').classes('text-4xl font-bold text-primary mb-4')
        ui.markdown('基于 **NiceGUI** 与 **V2 场景引擎** 的现代化重构版。').classes('text-lg text-gray-600')
        
        with ui.row().classes('mt-8 gap-4'):
            ui.button('进入仿真工作台', on_click=lambda: ui.navigate.to('/prototype'), icon='rocket').props('elevated size=lg')

# 导入页面 (触发路由注册)
from ui.pages import prototype as _prototype_page

if __name__ in {"__main__", "__mp_main__"}:
    init_all()
    ui.run(
        title='Genshin Damage Calc V2',
        port=8080,
        dark=False,
        favicon='🚀'
    )