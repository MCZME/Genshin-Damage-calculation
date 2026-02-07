from nicegui import ui
import asyncio
from core.registry import CharacterClassMap, initialize_registry
from core.context import create_context
from core.simulator import Simulator
from core.factory.team_factory import TeamFactory
from core.factory.action_parser import ActionParser
from core.data.repository import MySQLDataRepository
from core.persistence.database import ResultDatabase

# 确保注册表已初始化
initialize_registry()

async def start_simulation(char_name: str, level: int):
    """启动 V2 仿真流程"""
    ui.notify(f'开始模拟: {char_name} (Lv.{level})')
    
    # 1. 准备环境
    ctx = create_context()
    db = ResultDatabase("simulation_results.db")
    await db.initialize()
    await db.start_session()
    
    try:
        # 2. 构造模拟数据 (此处暂为硬编码，后续由 UI 收集)
        repo = MySQLDataRepository()
        team_factory = TeamFactory(repo)
        
        team_data = [{
            "character": {"id": 11, "name": char_name, "level": level, "talents": "9/9/9"},
            "weapon": {"name": "「渔获」", "level": 90, "refinement": 5},
            "artifacts": []
        }]
        
        # 简单动作序列：爆发 + 等待
        actions_raw = [
            {"character": char_name, "action": "元素爆发", "params": {}},
            {"character": char_name, "action": "跳过", "params": {"时间": 60}}
        ]
        
        actions = ActionParser().parse_sequence(actions_raw)
        team = team_factory.create_team(team_data)
        ctx.team = team
        
        # 3. 运行仿真
        sim = Simulator(ctx, actions, persistence_db=db)
        await sim.run()
        
        await db.stop_session()
        ui.notify('模拟完成！正在进入分析界面...', type='positive')
        await asyncio.sleep(1)
        ui.navigate.to('/analysis')
        
    except Exception as e:
        ui.notify(f'模拟失败: {str(e)}', type='negative')
        await db.stop_session()

@ui.page('/config')
def config_page():
    # 使用状态存储 UI 变量
    state = {'char': '香菱', 'lv': 90}

    with ui.column().classes('w-full p-8'):
        ui.label('模拟环境配置').classes('text-3xl font-bold mb-6')
        
        with ui.stepper().props('vertical').classes('w-full') as stepper:
            # Step 1: 队伍配置
            with ui.step('1. 队伍配置'):
                with ui.card().classes('p-4'):
                    ui.label('角色选择').classes('text-xl font-medium')
                    char_names = list(CharacterClassMap.keys())
                    with ui.row().classes('items-center gap-4'):
                        ui.select(options=char_names, label='选择角色').classes('w-64').bind_value(state, 'char')
                        ui.number(label='等级', min=1, max=90).classes('w-24').bind_value(state, 'lv')
                
                with ui.stepper_navigation():
                    ui.button('下一步', on_click=stepper.next)

            # Step 2: 目标与动作
            with ui.step('2. 目标与动作'):
                ui.label('已预设动作序列: [元素爆发] -> [等待 1秒]').classes('italic text-blue-500')
                with ui.stepper_navigation():
                    ui.button('上步', on_click=stepper.previous).props('flat')
                    ui.button('开始模拟', on_click=lambda: start_simulation(state['char'], state['lv']))

        ui.button('返回主页', on_click=lambda: ui.navigate.to('/'), icon='home').classes('mt-8')
