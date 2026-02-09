import json
import os
import random
from nicegui import ui, app
from ui.layout import AppShell
from ui.theme import GenshinTheme
from ui.pages.prototype_state import PrototypeState
from ui.pages.prototype_parts import render_character_editor, open_substat_editor

state = PrototypeState()

@ui.page('/prototype')
def prototype_page():
    shell = AppShell()

    # 容器引用
    left_container = None
    middle_container = None
    right_container = None

    # --- 映射表：用于 UI 显示 ---
    ACTION_DISPLAY_MAP = {
        'normal_attack': '普攻',
        'elemental_skill': '战技',
        'elemental_burst': '爆发',
        'switch': '切人',
        'dash': '冲刺',
        'jump': '跳跃'
    }

    # --- 1. 辅助方法定义 ---
    def refresh_ui():
        """全局视图刷新逻辑"""
        draw_header_content.refresh()
            
        # 根据阶段分发渲染
        if state.phase == 'strategic':
            render_strategic_layout()
        elif state.phase == 'tactical':
            render_tactical_layout()
        else:
            if middle_container:
                middle_container.clear()
                with middle_container:
                    ui.label('复盘模式开发中...').classes('text-white opacity-20 p-12')

    def change_phase(new_phase):
        state.phase = new_phase
        # 切换阶段时重置选择状态
        state.selected_entity = None
        state.selected_type = 'dashboard'
        state.selected_action_idx = None
        refresh_ui()

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
        if state.selected_entity == char: select_entity(None, 'dashboard')
        else: refresh_ui()

    def add_action(char_name, element, action_key):
        """[V2.3] 添加动作，集成元数据感知逻辑"""
        from core.registry import CharacterClassMap
        
        # 1. 尝试获取默认意图参数
        intent_params = {}
        char_cls = CharacterClassMap.get(char_name)
        if char_cls:
            try:
                # 实例化临时对象以查阅 metadata
                temp_char = char_cls(level=90, skill_params=[1,1,1])
                metadata = temp_char.get_action_metadata().get(action_key, {})
                for p_def in metadata.get("params", []):
                    intent_params[p_def["key"]] = p_def.get("default")
            except Exception: pass

        # 2. 追加动作块
        state.actions.append({
            'char_name': char_name,
            'element': element,
            'action_key': action_key,
            'params': {**intent_params, 'comment': ''}
        })
        state.selected_action_idx = len(state.actions) - 1
        refresh_ui()

    # --- 2. 模式渲染引擎 ---
    def render_strategic_layout():
        render_strategic_left()
        render_strategic_middle()
        render_strategic_right()

    def render_strategic_left():
        if not left_container: return
        left_container.clear()
        with left_container:
            with ui.column().classes('w-full gap-4'):
                ui.label('TEAM (我方)').classes('text-[10px] font-black opacity-30 tracking-[0.2em]')
                for char in state.team:
                    c = char['character']
                    is_sel = (state.selected_entity == char)
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
                    is_sel = (state.selected_entity == target)
                    with ui.element('div').classes(f'p-4 rounded-xl border {"border-red-500/50 bg-red-500/10" if is_sel else "border-transparent bg-white/5"} cursor-pointer hover:bg-white/10 transition-all') \
                        .on('click', lambda t=target: select_entity(t, 'target')):
                        with ui.row().classes('items-center gap-3'):
                            ui.element('div').classes('w-2 h-2 rounded-full bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]')
                            ui.label(target['name']).classes('text-xs font-bold')

    def render_strategic_middle():
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
                render_character_editor(state, state.selected_entity, refresh_ui, select_entity)

    def render_strategic_right():
        if not right_container: return
        right_container.clear()
        with right_container:
            with ui.column().classes('w-full h-full flex flex-col items-center justify-start gap-4 p-4'):
                ui.label('TACTICAL MAP').classes('text-[10px] font-black opacity-30 tracking-[0.4em] self-start mb-2')
                
                map_size = 20
                with ui.element('div').classes('relative w-full aspect-square bg-white/5 rounded-xl border border-white/10 overflow-hidden'):
                    ui.element('div').classes('absolute top-1/2 left-0 w-full h-[1px] bg-white/10')
                    ui.element('div').classes('absolute left-1/2 top-0 h-full w-[1px] bg-white/10')
                    
                    for char in state.team:
                        pos = char.get('position', {'x': 0, 'z': 0})
                        l_pct, t_pct = (pos['x'] + 10) / 20 * 100, (10 - pos['z']) / 20 * 100
                        is_sel = (state.selected_entity == char)
                        color = GenshinTheme.ELEMENTS.get(char['character']['element'], {}).get('primary', '#fff')
                        with ui.element('div').style(f'position: absolute; left: {l_pct}%; top: {t_pct}%; transform: translate(-50%, -50%);'):
                            if is_sel: ui.element('div').classes('absolute w-8 h-8 rounded-full border border-white animate-ping opacity-50').style(f'border-color: {color}; transform: translate(-25%, -25%)')
                            ui.element('div').classes('w-3 h-3 rounded-full shadow-[0_0_10px_rgba(0,0,0,0.5)] cursor-pointer hover:scale-150 transition-all').style(f'background-color: {color}').on('click', lambda c=char: select_entity(c, 'character'))

                    for target in state.targets:
                        pos = target.get('position', {'x': 0, 'z': 0})
                        l_pct, t_pct = (pos['x'] + 10) / 20 * 100, (10 - pos['z']) / 20 * 100
                        is_sel = (state.selected_entity == target)
                        with ui.element('div').style(f'position: absolute; left: {l_pct}%; top: {t_pct}%; transform: translate(-50%, -50%);'):
                            if is_sel: ui.element('div').classes('absolute w-8 h-8 rounded-full border border-red-500 animate-ping opacity-50').style('transform: translate(-25%, -25%)')
                            ui.element('div').classes('w-3 h-3 rounded-full bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.5)] cursor-pointer').on('click', lambda t=target: select_entity(t, 'target'))

                if state.selected_entity:
                    pos = state.selected_entity.get('position', {'x': 0, 'z': 0})
                    ui.label('POSITION (Meters)').classes('text-[9px] font-black opacity-40 mt-4 self-start')
                    with ui.row().classes('w-full gap-2'):
                        ui.number('X', value=pos['x'], step=0.5, on_change=lambda e: (pos.update({'x': e.value}), refresh_ui())).props('dark dense outlined').classes('flex-grow')
                        ui.number('Z', value=pos['z'], step=0.5, on_change=lambda e: (pos.update({'z': e.value}), refresh_ui())).props('dark dense outlined').classes('flex-grow')

    def render_tactical_layout():
        render_tactical_left()
        render_tactical_middle()
        render_tactical_right()

    def render_tactical_left():
        if not left_container: return
        left_container.clear()
        with left_container:
            ui.label('ACTION LIBRARY').classes('text-[10px] font-black opacity-30 tracking-[0.2em] mb-6')
            for char in state.team:
                if char.get('is_placeholder'): continue
                c = char['character']
                color = GenshinTheme.ELEMENTS.get(c['element'], {}).get('primary', '#fff')
                with ui.column().classes('w-full p-4 rounded-2xl bg-white/5 border border-white/5 mb-4'):
                    with ui.row().classes('items-center gap-2 mb-3'):
                        ui.element('div').classes('w-1.5 h-1.5 rounded-full').style(f'background-color: {color}')
                        ui.label(c['name']).classes('text-[10px] font-black uppercase tracking-widest opacity-60')
                    
                    with ui.grid(columns=2).classes('w-full gap-2'):
                        actions = [
                            ('normal_attack', '普攻'), 
                            ('elemental_skill', '战技'), 
                            ('elemental_burst', '爆发'), 
                            ('switch', '切人')
                        ]
                        for key, label in actions:
                            ui.button(label, on_click=lambda k=key, name=c['name'], el=c['element']: add_action(name, el, k)) \
                                .props('flat dense color=white').classes('text-[9px] border border-white/5 rounded-lg py-1 hover:bg-white/10')

    def render_tactical_middle():
        if not middle_container: return
        middle_container.clear()
        with middle_container:
            ui.label('ACTION SEQUENCE').classes('text-[10px] font-black opacity-30 tracking-[0.4em] mb-8')
            with ui.row().classes('w-full flex-wrap gap-3'):
                if not state.actions:
                    ui.label('尚未添加任何动作指令').classes('text-xs opacity-20 italic p-12 w-full text-center border-2 border-dashed border-white/5 rounded-3xl')
                
                for i, action in enumerate(state.actions):
                    is_sel = (state.selected_action_idx == i)
                    color = GenshinTheme.ELEMENTS.get(action['element'], {}).get('primary', '#fff')
                    display_name = ACTION_DISPLAY_MAP.get(action['action_key'], action['action_key'])
                    
                    with ui.element('div').classes(f'p-3 pr-4 rounded-xl border flex items-center gap-3 cursor-pointer transition-all hover:scale-105 {"border-[var(--md-primary)] bg-white/10 shadow-[0_0_20px_rgba(255,255,255,0.05)]" if is_sel else "border-white/5 bg-white/5"}') \
                        .on('click', lambda idx=i: (setattr(state, 'selected_action_idx', idx), refresh_ui())):
                        ui.element('div').classes('w-1 h-6 rounded-full').style(f'background-color: {color}')
                        with ui.column().classes('gap-0'):
                            ui.label(action['char_name']).classes('text-[9px] font-bold opacity-40 uppercase')
                            ui.label(display_name).classes('text-xs font-black')
                        
                        # 改进删除逻辑
                        def remove_at(idx):
                            state.actions.pop(idx)
                            if state.selected_action_idx == idx:
                                state.selected_action_idx = None
                            elif state.selected_action_idx is not None and state.selected_action_idx > idx:
                                state.selected_action_idx -= 1
                            refresh_ui()
                            
                        ui.button(icon='close', on_click=lambda idx=i: remove_at(idx)).props('flat round size=xs color=red').classes('ml-2 opacity-0 hover:opacity-100')

    def render_tactical_right():
        """[V2.3] 动态参数检查器 - 根据 Backend 元数据生成 UI"""
        if not right_container: return
        right_container.clear()
        with right_container:
            if state.selected_action_idx is not None:
                from core.registry import CharacterClassMap
                action = state.actions[state.selected_action_idx]
                display_name = ACTION_DISPLAY_MAP.get(action['action_key'], action['action_key'])
                
                ui.label(f'INSPECTOR / {action["char_name"]} - {display_name}').classes('text-[10px] font-black opacity-30 tracking-[0.3em] mb-8')
                
                with ui.column().classes('w-full gap-6'):
                    with ui.element('div').classes('genshin-card genshin-glass p-6 border border-white/10'):
                        ui.label('INTENT PARAMETERS (意图参数)').classes('text-[9px] font-black opacity-40 mb-4')
                        
                        # 1. 尝试获取元数据
                        char_cls = CharacterClassMap.get(action["char_name"])
                        metadata = {}
                        if char_cls:
                            try:
                                temp_char = char_cls(level=90, skill_params=[1,1,1])
                                metadata = temp_char.get_action_metadata().get(action["action_key"], {})
                            except Exception: pass

                        # 2. 动态生成参数控件
                        params_list = metadata.get("params", [])
                        if not params_list:
                            ui.label('此动作无逻辑参数').classes('text-[10px] opacity-20 italic')
                        else:
                            for p_def in params_list:
                                key, label, p_type = p_def["key"], p_def["label"], p_def.get("type", "text")
                                if p_type == "select":
                                    ui.select(options=p_def.get("options", []), label=label, value=action['params'].get(key), 
                                              on_change=lambda e, k=key: (action['params'].update({k: e.value}), refresh_ui())) \
                                        .props('dark outlined dense').classes('w-full mb-2')
                                elif p_type in ["int", "float"]:
                                    ui.number(label=label, value=action['params'].get(key), 
                                              on_change=lambda e, k=key: (action['params'].update({k: e.value}), refresh_ui())) \
                                        .props('dark dense outlined').classes('w-full mb-2')
                                else:
                                    ui.input(label=label, value=action['params'].get(key), 
                                             on_change=lambda e, k=key: (action['params'].update({k: e.value}), refresh_ui())) \
                                        .props('dark outlined dense').classes('w-full mb-2')

                        # 3. 通用备注
                        ui.label('NOTES').classes('text-[9px] font-black opacity-40 mt-6 mb-2')
                        ui.input('动作意图备注', value=action['params'].get('comment', ''), 
                                 on_change=lambda e: action['params'].update({'comment': e.value})).props('dark outlined dense').classes('w-full')
                    
                    ui.button('删除此动作', icon='delete', on_click=lambda: remove_selected_action()) \
                        .props('flat color=red').classes('w-full opacity-40 hover:opacity-100 text-[10px] font-black tracking-widest')
            else:
                ui.label('未选中动作').classes('text-xs opacity-20 italic text-center w-full mt-24')

    def remove_selected_action():
        if state.selected_action_idx is not None:
            state.actions.pop(state.selected_action_idx)
            state.selected_action_idx = None
            refresh_ui()

    # --- 3. UI 布局与组件实例化 ---
    # --- 顶层布局定义 (必须直接作为页面子元素) ---
    with ui.header().classes('genshin-glass border-b border-white/5 items-center justify-between px-8 py-3'):
        @ui.refreshable
        def draw_header_content():
            shell.header_content(state.phase, on_phase_change=change_phase)
        draw_header_content()

    with ui.row().classes('w-full h-[calc(100vh-250px)] no-wrap gap-4 p-4'):
        with shell.left_column():
            left_container = ui.column().classes('h-full w-full')
        with shell.middle_column():
            middle_container = ui.column().classes('w-full p-12 max-w-7xl mx-auto')
        with shell.right_column():
            right_container = ui.column().classes('w-full h-full')

    with ui.footer().classes('bg-transparent px-4 pb-4 pt-0 h-24'):
        with ui.row().classes('w-full genshin-glass genshin-pane px-10 h-full items-center justify-between shadow-[0_-10px_40px_rgba(0,0,0,0.4)]'):
            with ui.row().classes('items-center gap-8'):
                ui.button('开始仿真', icon='bolt', on_click=state.run_simulation, color='primary') \
                    .classes('px-12 py-2 rounded-full font-black shadow-2xl shadow-primary/40 text-sm') \
                    .props('no-caps elevated')
                
                with ui.column().classes('gap-0'):
                    ui.label('SYSTEM STATUS').classes('text-[9px] font-black tracking-[0.2em] text-primary opacity-80')
                    @ui.refreshable
                    def status_label():
                        ui.label('READY TO EXECUTE' if not state.is_simulating else 'SIMULATING...').classes('text-[11px] font-bold tracking-[0.1em] text-white/40')
                    status_label()
            
            with ui.row().classes('items-center gap-4'):
                ui.button('保存配置', icon='save', on_click=state.save_to_file).props('flat color=white').classes('opacity-60 text-[11px] font-bold tracking-widest')
                ui.button('加载配置', icon='folder_open', on_click=lambda: (state.load_from_file(), refresh_ui())).props('flat color=white').classes('opacity-60 text-[11px] font-bold tracking-widest')
                
                with ui.row().classes('gap-8 opacity-20 ml-8 border-l border-white/10 pl-8'):
                    with ui.column().classes('items-end gap-0'):
                        ui.label('DATABASE').classes('text-[8px] font-black tracking-widest')
                        ui.label('CONNECTED').classes('text-[10px] font-bold text-green-500')
                    with ui.column().classes('items-end gap-0'):
                        ui.label('ENGINE').classes('text-[8px] font-black tracking-widest')
                        ui.label('V2.2.0-STABLE').classes('text-[10px] font-bold')

    # 初始刷新启动 UI 渲染
    refresh_ui()

    ui.add_head_html('<style>.nicegui-content { padding: 0 !important; overflow: hidden; }</style>')
