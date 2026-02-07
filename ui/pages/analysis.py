from nicegui import ui
import os
from core.persistence.database import ResultDatabase

# 数据库实例 (单例模式供页面共享)
db = ResultDatabase("simulation_results.db")

class AnalysisState:
    def __init__(self):
        self.frame_id = 0
        self.max_frames = 0
        self.current_data = None

state = AnalysisState()

@ui.page('/analysis')
async def analysis_page():
    # 1. 检查数据库是否存在
    if not os.path.exists(db.db_path):
        with ui.column().classes('w-full items-center p-20'):
            ui.icon('warning', size='100px', color='warning')
            ui.label('未发现模拟结果数据库').classes('text-2xl font-bold mt-4')
            ui.label('请先前往“模拟配置”页面运行一次仿真。').classes('text-gray-500')
            ui.button('前往配置', on_click=lambda: ui.navigate.to('/config')).classes('mt-8')
        return

    # 2. 获取总帧数 (初始化状态)
    # 此处简化：假设我们先获取最大 frame_id
    import aiosqlite
    async with aiosqlite.connect(db.db_path) as conn:
        async with conn.execute("SELECT MAX(frame_id) FROM frames") as cursor:
            row = await cursor.fetchone()
            state.max_frames = row[0] if row and row[0] is not None else 0

    async def update_view(e=None):
        """核心回溯逻辑：当滑块变动时触发"""
        target_id = int(slider.value)
        data = await db.get_frame(target_id)
        if data:
            state.current_data = data
            frame_label.set_text(f"当前显示: 第 {target_id} 帧")
            # 动态渲染实体状态
            render_entities(data["entities"])

    def render_entities(entities):
        """渲染实体列表面板"""
        container.clear()
        with container:
            for ent in entities:
                with ui.card().classes('w-full p-4 mb-4'):
                    with ui.row().classes('w-full justify-between items-center'):
                        ui.label(ent["name"]).classes('text-xl font-bold text-primary')
                        ui.badge(ent["faction"], color='orange' if ent["faction"] == "ENEMY" else 'blue')
                    
                    with ui.row().classes('gap-8 mt-2'):
                        ui.label(f"位置: {ent['pos']}").classes('text-sm text-gray-600')
                        if "hp" in ent:
                            ui.label(f"生命值: {ent['hp']}").classes('text-sm font-medium text-red-500')
                    
                    # 渲染元素附着 (Aura)
                    auras = ent.get("auras", {})
                    if auras.get("regular") or auras.get("frozen") or auras.get("quicken"):
                        ui.separator().classes('my-2')
                        with ui.row().classes('gap-2 items-center'):
                            ui.label('元素附着:').classes('text-xs font-bold')
                            for a in auras.get("regular", []):
                                ui.chip(f"{a['element']} ({a['value']})", color='green', icon='water_drop')
                            if auras.get("frozen"):
                                ui.chip(f"冻结 ({auras['frozen']['value']})", color='cyan')

    with ui.column().classes('w-full p-8'):
        ui.label('结果分析与每一帧回溯').classes('text-3xl font-bold')
        
        # 控制栏
        with ui.row().classes('w-full items-center gap-4 bg-gray-50 p-4 rounded-lg shadow-sm'):
            ui.label('时间轴:').classes('font-bold')
            slider = ui.slider(min=0, max=state.max_frames, value=0, on_change=update_view).classes('flex-grow')
            frame_label = ui.label('当前显示: 第 0 帧').classes('w-32 font-mono')
            ui.button(icon='refresh', on_click=lambda: ui.navigate.to('/analysis')).props('flat')

        # 内容展示区
        container = ui.column().classes('w-full mt-8')
        
        # 初始加载
        ui.timer(0.1, update_view, once=True)

    ui.button('返回主页', on_click=lambda: ui.navigate.to('/'), icon='home').classes('fixed bottom-8 right-8')
