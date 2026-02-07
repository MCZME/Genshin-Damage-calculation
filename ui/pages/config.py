from nicegui import ui
from core.registry import CharacterClassMap, initialize_registry

# 确保注册表已初始化
initialize_registry()

@ui.page('/config')
def config_page():
    with ui.column().classes('w-full p-8'):
        ui.label('模拟环境配置').classes('text-3xl font-bold mb-6')
        
        with ui.stepper().props('vertical').classes('w-full') as stepper:
            # Step 1: 队伍配置
            with ui.step('1. 队伍配置'):
                with ui.card().classes('p-4'):
                    ui.label('角色选择').classes('text-xl font-medium')
                    # 动态从 Registry 获取已注册角色
                    char_names = list(CharacterClassMap.keys())
                    with ui.row().classes('items-center gap-4'):
                        ui.select(options=char_names, label='选择角色', value=char_names[0] if char_names else None).classes('w-64')
                        ui.number(label='等级', value=90, min=1, max=90).classes('w-24')
                        ui.select(options=[0,1,2,3,4,5,6], label='命座', value=0).classes('w-24')
                
                with ui.stepper_navigation():
                    ui.button('下一步', on_click=stepper.next)

            # Step 2: 目标与动作
            with ui.step('2. 目标与动作'):
                ui.label('此处将集成动作序列编辑器...').classes('italic text-gray-400')
                with ui.stepper_navigation():
                    ui.button('上一步', on_click=stepper.previous).props('flat')
                    ui.button('开始模拟', on_click=lambda: ui.notify('模拟启动中...'))

        ui.button('返回主页', on_click=lambda: ui.navigate.to('/'), icon='home').classes('mt-8')
