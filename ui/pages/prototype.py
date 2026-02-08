import json
import os
import random
from nicegui import ui, app
from ui.layout import AppShell
from ui.theme import GenshinTheme

# 核心引擎接入
from core.factory.assembler import create_simulator_from_config
from core.data.repository import MySQLDataRepository
from core.logger import get_emulation_logger

# 仿真会话状态
class PrototypeState:
    def __init__(self):
        self.repo = MySQLDataRepository()
        self.char_map = {}
        self.artifact_sets = []
        self._refresh_char_db()
        self._refresh_artifact_db()
        
        self.selected_entity = None
        self.selected_type = 'dashboard' 
        self.is_simulating = False
        
        # 搜索与过滤状态
        self.char_search_query = ""
        self.char_filter_element = "全部"
        self.char_filter_weapon = "全部"
        
        self.team = []
        self.targets = [
            {"id": "target_A", "name": "遗迹守卫", "level": 90, 
             "position": {"x": 0, "z": 5}, 
             "resists": {"火": 10, "水": 10, "雷": 10, "草": 10, "冰": 10, "岩": 10, "风": 10, "物理": 10}}
        ]
        self.environment = {"location": "深境螺旋 12-3", "weather": "Clear", "buffs": []}
        self.actions = [] 

    def _refresh_char_db(self):
        try:
            char_list = self.repo.get_all_characters()
            self.char_map = {
                c["name"]: {"id": c["id"], "element": c["element"], "type": c["type"]}
                for c in char_list
            }
        except Exception as e:
            get_emulation_logger().log_error(f"角色库加载失败: {e}")
            self.char_map = {}

    def _refresh_artifact_db(self):
        try:
            self.artifact_sets = self.repo.get_all_artifact_sets()
        except Exception as e:
            self.artifact_sets = ["炽烈的炎之魔女", "绝缘之旗印", "翠绿之影"]

    def _create_placeholder_struct(self):
        return {
            "is_placeholder": True,
            "position": {"x": 0, "z": -2},
            "character": {"id": 0, "name": "待选择角色", "element": "物理", "level": 90, "constellation": 0, "talents": [1, 1, 1], "type": "单手剑"},
            "weapon": {"name": "无锋剑", "level": 1, "refinement": 1},
            "artifacts": {
                "flower": {"slot": "生之花", "set_name": "", "main_stat": "生命值", "sub_stats": []},
                "plume": {"slot": "死之羽", "set_name": "", "main_stat": "攻击力", "sub_stats": []},
                "sands": {"slot": "时之沙", "set_name": "", "main_stat": "攻击力%", "sub_stats": []},
                "goblet": {"slot": "空之杯", "set_name": "", "main_stat": "火元素伤害加成", "sub_stats": []},
                "circlet": {"slot": "理之冠", "set_name": "", "main_stat": "暴击率", "sub_stats": []},
            }
        }

    def export_config(self) -> dict:
        return {
            "context_config": {
                "team": [c for c in self.team if not c.get("is_placeholder")],
                "targets": self.targets,
                "environment": self.environment
            },
            "sequence_config": self.actions
        }

    async def run_simulation(self):
        if self.is_simulating: return
        try:
            self.is_simulating = True
            ui.notify("启动仿真中...", type='info', spinner=True)
            simulator = create_simulator_from_config(self.export_config(), self.repo)
            await simulator.run()
            ui.notify(f"仿真完成 (Frame: {simulator.ctx.current_frame})", type='positive')
        except Exception as e:
            ui.notify(f"故障: {e}", type='negative')
        finally:
            self.is_simulating = False

    def save_to_file(self, filename: str = "simulation_draft.json"):
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(self.export_config(), f, ensure_ascii=False, indent=4)
            ui.notify(f"配置已保存至 {filename}", type='positive')
        except Exception as e:
            ui.notify(f"保存失败: {e}", type='negative')

    def load_from_file(self, filename: str = "simulation_draft.json"):
        if not os.path.exists(filename):
            ui.notify(f"未找到文件 {filename}", type='warning')
            return
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
            ctx = data.get("context_config", {})
            if "team" in ctx: self.team = ctx["team"]
            if "targets" in ctx: self.targets = ctx["targets"]
            if "environment" in ctx: self.environment = ctx["environment"]
            self.actions = data.get("sequence_config", [])
            self.selected_entity = None
            self.selected_type = 'dashboard'
            ui.notify(f"已从 {filename} 恢复配置", type='positive')
        except Exception as e:
            ui.notify(f"加载失败: {e}", type='negative')

state = PrototypeState()

@ui.page('/prototype')
def prototype_page():
    shell = AppShell()
    shell.header()

    left_drawer_container = None
    middle_container = None
    right_canvas_container = None

    def refresh_ui():
        render_left_column()
        render_middle()
        render_right_column()

    def select_entity(entity, e_type):
        state.selected_entity = entity
        state.selected_type = e_type
        if e_type == 'character' and entity:
            GenshinTheme.set_element(entity['character']['element'])
        else:
            GenshinTheme.set_element('Neutral')
        refresh_ui()

    def add_character():
        new_char = state._create_placeholder_struct()
        state.team.append(new_char)
        select_entity(new_char, 'character')

    def remove_character(char):
        state.team.remove(char)
        if state.selected_entity == char:
            select_entity(None, 'dashboard')
        else:
            refresh_ui()

    def open_substat_editor(artifact_data):
        with ui.dialog() as dialog, ui.card().classes('min-w-[450px] genshin-glass border border-white/10 p-6'):
            ui.label(f"{artifact_data['slot']} 副词条详情").classes('text-xs font-black opacity-60 mb-4')
            container = ui.column().classes('w-full gap-2')
            def draw_rows():
                container.clear()
                with container:
                    for i, sub in enumerate(artifact_data['sub_stats']):
                        with ui.row().classes('w-full items-center gap-2'):
                            ui.select(['暴击率', '暴击伤害', '攻击力%', '攻击力', '生命值%', '生命值', '防御力%', '防御力', '元素精通', '元素充能'],
                                      value=sub['name'], on_change=lambda e, s=sub: s.update({'name': e.value})).props('dark dense outlined').classes('flex-grow')
                            ui.number(value=sub['value'], format='%.1f', on_change=lambda e, s=sub: s.update({'value': e.value})).props('dark dense outlined').classes('w-20')
                            ui.button(icon='delete', on_click=lambda idx=i: (artifact_data['sub_stats'].pop(idx), draw_rows())).props('flat round size=sm color=red')
                    if len(artifact_data['sub_stats']) < 4:
                        ui.button('添加词条', icon='add', on_click=lambda: (artifact_data['sub_stats'].append({'name': '暴击率', 'value': 0.0}), draw_rows())).props('flat dense').classes('w-full mt-2 opacity-40')
            draw_rows()
            ui.button('确定', on_click=lambda: (dialog.close(), refresh_ui())).props('flat color=primary').classes('w-full mt-4')
        dialog.open()

    def render_left_column():
        if not left_drawer_container: return
        left_drawer_container.clear()
        with left_drawer_container:
            with ui.column().classes('w-full gap-4'):
                ui.label('TEAM (我方)').classes('text-[10px] font-black opacity-30 tracking-[0.2em]')
                for char in state.team:
                    c = char['character']
                    is_sel = state.selected_entity == char
                    with ui.element('div').classes(f'p-4 rounded-xl border {"border-[var(--md-primary)] bg-white/10" if is_sel else "border-transparent bg-white/5"} cursor-pointer group transition-all'):
                        with ui.row().classes('items-center justify-between w-full'):
                            with ui.row().classes('items-center gap-3').on('click', lambda ch=char: select_entity(ch, 'character')):
                                color = GenshinTheme.ELEMENTS.get(c['element'], {}).get('primary', '#fff')
                                ui.element('div').classes('w-2 h-2 rounded-full').style(f'background-color: {color}; box-shadow: 0 0 8px {color}')
                                ui.label(c['name']).classes('text-xs font-bold')
                            ui.button(icon='close', on_click=lambda ch=char: remove_character(ch)).props('flat round size=xs color=red').classes('opacity-0 group-hover:opacity-40')
                if len(state.team) < 4:
                    ui.button(icon='add', on_click=add_character).props('flat round color=white').classes('opacity-20 self-center')

                ui.label('TARGETS (敌方)').classes('text-[10px] font-black opacity-30 tracking-[0.2em] mt-6')
                for target in state.targets:
                    is_sel = state.selected_entity == target
                    with ui.element('div').classes(f'p-4 rounded-xl border {"border-red-500/50 bg-red-500/10" if is_sel else "border-transparent bg-white/5"} cursor-pointer hover:bg-white/10 transition-all') \
                        .on('click', lambda t=target: select_entity(t, 'target')):
                        with ui.row().classes('items-center gap-3'):
                            ui.element('div').classes('w-2 h-2 rounded-full bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]')
                            ui.label(target['name']).classes('text-xs font-bold')

    def render_middle():
        if not middle_container: return
        middle_container.clear()
        with middle_container:
            if state.selected_type == 'dashboard' or not state.selected_entity:
                ui.label('战斗仿真全局预览').classes('text-[10px] font-black opacity-30 tracking-[0.4em] mb-12')
                with ui.row().classes('w-full gap-6 mb-12'):
                    if not state.team:
                        ui.label('队伍中还没有成员').classes('opacity-20 text-xs italic')
                    for char in state.team:
                        c = char['character']
                        color = GenshinTheme.ELEMENTS.get(c['element'], {}).get('primary', '#fff')
                        with ui.element('div').classes('genshin-card genshin-glass p-8 flex-grow border border-white/5 relative cursor-pointer').on('click', lambda ch=char: select_entity(ch, 'character')):
                            ui.element('div').classes('absolute left-0 top-0 bottom-0 w-1').style(f'background-color: {color}')
                            ui.label(c['name']).classes('text-3xl font-black')
                            ui.label(f"等级 {c['level']} / {c['type']}").classes('text-[10px] opacity-40 mt-2')

            elif state.selected_type == 'target':
                t = state.selected_entity
                ui.label(f'目标配置 / {t["name"]}').classes('text-[10px] font-black opacity-30 tracking-[0.4em] mb-8')
                with ui.element('div').classes('genshin-card genshin-glass p-8 w-full border border-white/10'):
                    with ui.row().classes('items-center gap-6 mb-8'):
                        ui.input('名称', value=t['name'], on_change=lambda e: t.update({'name': e.value})).props('dark dense outlined').classes('text-lg font-bold')
                        ui.number('等级', value=t['level'], on_change=lambda e: t.update({'level': int(e.value)})).props('dark dense outlined').classes('w-32')
                    ui.label('元素抗性 (%)').classes('text-[10px] font-black opacity-30 mb-4')
                    with ui.grid(columns=4).classes('w-full gap-4'):
                        for res_key, res_val in t['resists'].items():
                            color = GenshinTheme.ELEMENTS.get(res_key, {}).get('primary', '#fff')
                            ui.number(f"{res_key}", value=res_val, on_change=lambda e, k=res_key: t['resists'].update({k: e.value})).props('dark dense outlined').classes('w-full').style(f'--q-primary: {color}')

            elif state.selected_type == 'character':
                char_data = state.selected_entity
                if char_data.get('is_placeholder'):
                    with ui.column().classes('w-full gap-6'):
                        ui.label('选择角色库').classes('text-[10px] font-black opacity-30 tracking-[0.4em]')
                        with ui.row().classes('w-full items-center gap-4'):
                            ui.input(placeholder='搜索...', value=state.char_search_query, on_change=lambda e: (setattr(state, 'char_search_query', e.value), draw_grid())).props('rounded outlined dense dark').classes('w-64')
                        with ui.row().classes('w-full gap-2'):
                            for el in ["全部", "火", "水", "草", "雷", "风", "冰", "岩", "物理"]:
                                is_act = state.char_filter_element == el
                                color = GenshinTheme.ELEMENTS.get(el, {}).get('primary', '#fff') if el != "全部" else '#fff'
                                ui.button(el, on_click=lambda e=el: (setattr(state, 'char_filter_element', e), draw_grid())).props('flat dense').classes(f'text-[10px] px-4 rounded-full border border-white/5 {"bg-white/10" if is_act else ""}').style(f'color: {color if is_act or el=="全部" else "rgba(255,255,255,0.4)"}')
                        with ui.row().classes('w-full gap-2'):
                            for wt in ["全部", "单手剑", "双手剑", "长柄武器", "弓", "法器"]:
                                is_act = state.char_filter_weapon == wt
                                ui.button(wt, on_click=lambda w=wt: (setattr(state, 'char_filter_weapon', w), draw_grid())).props('flat dense').classes(f'text-[10px] px-4 rounded-full border border-white/5 {"bg-white/10" if is_act else ""}').style(f'opacity: {1.0 if is_act else 0.4}')
                        grid_cont = ui.column().classes('w-full mt-8')
                        def draw_grid():
                            grid_cont.clear()
                            with grid_cont:
                                filtered = {n: i for n, i in state.char_map.items() 
                                            if (state.char_filter_element == "全部" or i['element'] == state.char_filter_element)
                                            and (state.char_filter_weapon == "全部" or i['type'] == state.char_filter_weapon)
                                            and (not state.char_search_query or state.char_search_query.lower() in n.lower())}
                                with ui.grid(columns=4).classes('w-full gap-6'):
                                    for name, info in filtered.items():
                                        color = GenshinTheme.ELEMENTS.get(info['element'], {}).get('primary', '#fff')
                                        with ui.element('div').classes('genshin-card genshin-glass p-6 border border-white/10 cursor-pointer hover:scale-105 transition-all flex flex-col items-center gap-2') \
                                            .on('click', lambda n=name, i=info: (
                                                char_data.update({'is_placeholder': False, 'character': {**char_data['character'], 'id': i['id'], 'name': n, 'element': i['element'], 'type': i['type']}}),
                                                char_data['weapon'].update({'name': state.repo.get_weapons_by_type(i['type'])[0] if state.repo.get_weapons_by_type(i['type']) else "无锋剑"}),
                                                select_entity(char_data, 'character')
                                            )):
                                            ui.element('div').classes('w-2 h-2 rounded-full').style(f'background-color: {color}; box-shadow: 0 0 10px {color}')
                                            ui.label(name).classes('text-sm font-bold')
                                            ui.label(info['type']).classes('text-[8px] opacity-20 uppercase font-black')
                        draw_grid()
                    return

                c, w = char_data['character'], char_data['weapon']
                with ui.row().classes('items-center gap-4 mb-8'):
                    ui.button(icon='arrow_back', on_click=lambda: select_entity(None, 'dashboard')).props('flat round color=white')
                    ui.label(f'编辑器 / {c["name"]}').classes('text-xl font-black tracking-widest')
                with ui.row().classes('w-full gap-6 items-stretch'):
                    with ui.element('div').classes('genshin-card genshin-glass p-8 border border-white/10 flex-grow'):
                        ui.label('基础').classes('text-[10px] font-black opacity-30 mb-6')
                        with ui.row().classes('w-full gap-4'):
                            ui.number('等级', value=c['level'], on_change=lambda e: (c.update({'level': int(e.value or 0)}), refresh_ui())).props('dark outlined dense').classes('flex-grow')
                            ui.select([0,1,2,3,4,5,6], label='命座', value=c['constellation'], on_change=lambda e: (c.update({'constellation': e.value}), refresh_ui())).props('dark outlined dense').classes('w-full')
                        ui.label('天赋等级').classes('text-[10px] font-black opacity-30 mt-6 mb-2')
                        with ui.row().classes('w-full gap-2'):
                            for i in range(3):
                                ui.number(value=c['talents'][i], on_change=lambda e, idx=i: (c['talents'].__setitem__(idx, int(e.value or 0)), refresh_ui())).props('dark outlined dense').classes('w-12')
                    with ui.element('div').classes('genshin-card genshin-glass p-8 border border-white/10 flex-grow'):
                        ui.label(f'武器 ({c["type"]})').classes('text-[10px] font-black opacity-30 mb-6')
                        w_opts = state.repo.get_weapons_by_type(c['type'])
                        ui.select(w_opts, value=w['name'] if w['name'] in w_opts else None, with_input=True, on_change=lambda e: (w.update({'name': e.value}), refresh_ui())).props('dark outlined dense use-input hide-selected').classes('w-full mb-4')
                        with ui.row().classes('w-full gap-4'):
                            ui.number('等级', value=w['level'], on_change=lambda e: (w.update({'level': int(e.value or 0)}), refresh_ui())).props('dark outlined dense').classes('flex-grow')
                            ui.select([1,2,3,4,5], label='精炼', value=w['refinement'], on_change=lambda e: (w.update({'refinement': e.value}), refresh_ui())).props('dark outlined dense').classes('flex-grow')
                with ui.element('div').classes('genshin-card genshin-glass w-full p-8 border border-white/10 mt-6'):
                    ui.label('圣遗物').classes('text-[10px] font-black opacity-30 mb-8')
                    with ui.grid(columns=5).classes('w-full gap-4'):
                        for k, arti in char_data['artifacts'].items():
                            with ui.column().classes('p-4 bg-white/5 rounded-xl border border-white/5 h-full justify-between'):
                                with ui.column().classes('w-full gap-1'):
                                    ui.label(arti['slot']).classes('text-[9px] font-black opacity-40')
                                    ui.select(state.artifact_sets, value=arti['set_name'] if arti['set_name'] in state.artifact_sets else None, with_input=True, on_change=lambda e, a=arti: (a.update({'set_name': e.value}), refresh_ui())).props('dark borderless dense use-input hide-selected').classes('text-xs font-bold w-full')
                                    ui.input('主词条', value=arti['main_stat'], on_change=lambda e, a=arti: a.update({'main_stat': e.value})).props('dark borderless dense').classes('text-[10px] opacity-60')
                                with ui.column().classes('w-full gap-1 mt-4'):
                                    ui.label('副词条').classes('text-[8px] opacity-20 uppercase')
                                    for sub in arti['sub_stats'][:4]:
                                        ui.label(f"{sub['name']} {sub['value']}").classes('text-[9px] opacity-50 truncate')
                                    ui.button(icon='edit', on_click=lambda a=arti: open_substat_editor(a)).props('flat round size=xs').classes('self-end mt-2')

    def render_right_column():
        if not right_canvas_container: return
        right_canvas_container.clear()
        with right_canvas_container:
            with ui.column().classes('w-full h-full flex flex-col items-center justify-start gap-4 p-4'):
                ui.label('TACTICAL MAP').classes('text-[10px] font-black opacity-30 tracking-[0.4em] self-start mb-2')
                
                map_size = 20 # meters
                with ui.element('div').classes('relative w-full aspect-square bg-white/5 rounded-xl border border-white/10 overflow-hidden'):
                    ui.element('div').classes('absolute top-1/2 left-0 w-full h-[1px] bg-white/10')
                    ui.element('div').classes('absolute left-1/2 top-0 h-full w-[1px] bg-white/10')
                    
                    all_units = []
                    for char in state.team:
                        all_units.append({'data': char, 'type': 'character', 'color': GenshinTheme.ELEMENTS.get(char['character']['element'], {}).get('primary', '#fff')})
                    for t in state.targets:
                        all_units.append({'data': t, 'type': 'target', 'color': '#ef4444'})

                    for unit in all_units:
                        pos = unit['data'].get('position', {'x': 0, 'z': 0})
                        left_pct = (pos['x'] + 10) / 20 * 100
                        top_pct = (10 - pos['z']) / 20 * 100
                        is_sel = state.selected_entity == unit['data']
                        
                        with ui.element('div').style(f'position: absolute; left: {left_pct}%; top: {top_pct}%; transform: translate(-50%, -50%);'):
                            if is_sel:
                                ui.element('div').classes('absolute w-8 h-8 rounded-full border border-white animate-ping opacity-50').style(f'border-color: {unit["color"]}; transform: translate(-25%, -25%)')
                            ui.element('div').classes(f'w-3 h-3 rounded-full shadow-[0_0_10px_rgba(0,0,0,0.5)] cursor-pointer hover:scale-150 transition-all') \
                                .style(f'background-color: {unit["color"]}') \
                                .on('click', lambda u=unit['data'], t=unit['type']: select_entity(u, t))
                            if is_sel:
                                ui.label(unit['data'].get('character', unit['data']).get('name')).classes('absolute text-[8px] font-bold whitespace-nowrap -bottom-4 left-1/2 -translate-x-1/2 bg-black/50 px-1 rounded')

                if state.selected_entity:
                    pos = state.selected_entity.get('position', {'x': 0, 'z': 0})
                    ui.label('POSITION (Meters)').classes('text-[9px] font-black opacity-40 mt-4 self-start')
                    with ui.row().classes('w-full gap-2'):
                        ui.number('X', value=pos['x'], step=0.5, on_change=lambda e: (pos.update({'x': e.value}), refresh_ui())).props('dark dense outlined').classes('flex-grow')
                        ui.number('Z', value=pos['z'], step=0.5, on_change=lambda e: (pos.update({'z': e.value}), refresh_ui())).props('dark dense outlined').classes('flex-grow')

    # 渲染主内容
    with ui.row().classes('w-full h-[calc(100vh-250px)] no-wrap gap-4 p-4'):
        with shell.left_column():
            left_drawer_container = ui.column().classes('h-full w-full')
            render_left_column()
        with shell.middle_column():
            middle_container = ui.column().classes('w-full p-12 max-w-7xl mx-auto')
            render_middle()
        with shell.right_column():
            right_canvas_container = ui.column().classes('w-full h-full')
            render_right_column()

    # [NEW] 底部动作控制台
    with ui.footer().classes('bg-transparent px-4 pb-4 pt-0 h-24'):
        with ui.row().classes('w-full genshin-glass genshin-pane px-10 h-full items-center justify-between shadow-[0_-10px_40px_rgba(0,0,0,0.4)]'):
            with ui.row().classes('items-center gap-8'):
                # 仿真控制
                ui.button('开始仿真', icon='bolt', on_click=state.run_simulation, color='primary') \
                    .classes('px-12 py-2 rounded-full font-black shadow-2xl shadow-primary/40 text-sm') \
                    .props('no-caps elevated')
                
                with ui.column().classes('gap-0'):
                    ui.label('SYSTEM STATUS').classes('text-[9px] font-black tracking-[0.2em] text-primary opacity-80')
                    ui.label('READY TO EXECUTE' if not state.is_simulating else 'SIMULATING...').classes('text-[11px] font-bold tracking-[0.1em] text-white/40')
            
            with ui.row().classes('items-center gap-4'):
                ui.button('保存配置', icon='save', on_click=state.save_to_file).props('flat color=white').classes('opacity-60 text-[11px] font-bold tracking-widest')
                ui.button('加载配置', icon='folder_open', on_click=lambda: (state.load_from_file(), refresh_ui())).props('flat color=white').classes('opacity-60 text-[11px] font-bold tracking-widest')
                
                # 系统元数据
                with ui.row().classes('gap-8 opacity-20 ml-8 border-l border-white/10 pl-8'):
                    with ui.column().classes('items-end gap-0'):
                        ui.label('DATABASE').classes('text-[8px] font-black tracking-widest')
                        ui.label('CONNECTED').classes('text-[10px] font-bold text-green-500')
                    with ui.column().classes('items-end gap-0'):
                        ui.label('ENGINE').classes('text-[8px] font-black tracking-widest')
                        ui.label('V2.2.0-STABLE').classes('text-[10px] font-bold')

    ui.add_head_html('<style>.nicegui-content { padding: 0 !important; overflow: hidden; }</style>')