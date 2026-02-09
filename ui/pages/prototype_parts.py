from nicegui import ui
from ui.theme import GenshinTheme

def open_substat_editor(artifact_data, on_refresh):
    """弹出圣遗物副词条编辑器"""
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
        ui.button('确定', on_click=lambda: (dialog.close(), on_refresh())).props('flat color=primary').classes('w-full mt-4')
    dialog.open()

def render_character_editor(state, char_data, on_refresh, on_select):
    """渲染角色深度编辑器"""
    if char_data.get('is_placeholder'):
        with ui.column().classes('w-full gap-6'):
            ui.label('选择角色库').classes('text-[10px] font-black opacity-30 tracking-[0.4em]')
            with ui.row().classes('w-full items-center gap-4'):
                ui.input(placeholder='搜索...', value=state.char_search_query, 
                         on_change=lambda e: (setattr(state, 'char_search_query', e.value), on_refresh())).props('rounded outlined dense dark').classes('w-64')
            
            with ui.row().classes('w-full gap-2'):
                for el in ["全部", "火", "水", "草", "雷", "风", "冰", "岩", "物理"]:
                    is_act = (state.char_filter_element == el)
                    color = GenshinTheme.ELEMENTS.get(el, {}).get('primary', '#fff') if el != "全部" else '#fff'
                    ui.button(el, on_click=lambda e=el: (setattr(state, 'char_filter_element', e), on_refresh())).props('flat dense').classes(f'text-[10px] px-4 rounded-full border border-white/5 {"bg-white/10" if is_act else ""}').style(f'color: {color if is_act or el=="全部" else "rgba(255,255,255,0.4)"}')
            
            filtered = {n: i for n, i in state.char_map.items() 
                        if (state.char_filter_element == "全部" or i['element'] == state.char_filter_element)
                        and (state.char_filter_weapon == "全部" or i['type'] == state.char_filter_weapon)
                        and (not state.char_search_query or state.char_search_query.lower() in n.lower())}
            
            with ui.grid(columns=4).classes('w-full gap-6 mt-8'):
                from core.registry import CharacterClassMap
                for name, info in filtered.items():
                    is_implemented = name in CharacterClassMap
                    color = GenshinTheme.ELEMENTS.get(info['element'], {}).get('primary', '#fff')
                    
                    with ui.element('div').classes(f'genshin-card genshin-glass p-6 border border-white/10 cursor-pointer hover:scale-105 transition-all flex flex-col items-center gap-2 {"" if is_implemented else "opacity-40 grayscale"}') \
                        .on('click', lambda n=name, i=info, impl=is_implemented: (
                            (char_data.update({'is_placeholder': False, 'character': {**char_data['character'], 'id': i['id'], 'name': n, 'element': i['element'], 'type': i['type']}}),
                             char_data['weapon'].update({'name': state.repo.get_weapons_by_type(i['type'])[0] if state.repo.get_weapons_by_type(i['type']) else "无锋剑"}),
                             on_select(char_data, 'character')) if impl else ui.notify(f"角色 {n} 尚未在 V2 引擎中实现", type='warning')
                        )):
                        ui.element('div').classes('w-2 h-2 rounded-full').style(f'background-color: {color}; box-shadow: 0 0 10px {color}')
                        ui.label(name).classes('text-sm font-bold')
                        ui.label(info['type'] + ("" if is_implemented else " [未实现]")).classes('text-[8px] opacity-20 uppercase font-black')
        return

    c, w = char_data['character'], char_data['weapon']
    with ui.row().classes('items-center gap-4 mb-8'):
        ui.button(icon='arrow_back', on_click=lambda: on_select(None, 'dashboard')).props('flat round color=white')
        ui.label(f'编辑器 / {c["name"]}').classes('text-xl font-black tracking-widest')
    
    with ui.row().classes('w-full gap-6 items-stretch'):
        with ui.element('div').classes('genshin-card genshin-glass p-8 border border-white/10 flex-grow'):
            ui.label('基础').classes('text-[10px] font-black opacity-30 mb-6')
            with ui.row().classes('w-full gap-4'):
                ui.number('等级', value=c['level'], on_change=lambda e: (c.update({'level': int(e.value or 0)}), on_refresh())).props('dark outlined dense').classes('flex-grow')
                ui.select([0,1,2,3,4,5,6], label='命座', value=c['constellation'], on_change=lambda e: (c.update({'constellation': e.value}), on_refresh())).props('dark outlined dense').classes('w-full')
            ui.label('天赋等级').classes('text-[10px] font-black opacity-30 mt-6 mb-2')
            with ui.row().classes('w-full gap-2'):
                for i in range(3):
                    ui.number(value=c['talents'][i], on_change=lambda e, idx=i: (c['talents'].__setitem__(idx, int(e.value or 0)), on_refresh())).props('dark outlined dense').classes('w-12')
        
        with ui.element('div').classes('genshin-card genshin-glass p-8 border border-white/10 flex-grow'):
            ui.label(f'武器 ({c["type"]})').classes('text-[10px] font-black opacity-30 mb-6')
            w_opts = state.repo.get_weapons_by_type(c['type'])
            ui.select(w_opts, value=w['name'] if w['name'] in w_opts else None, with_input=True, on_change=lambda e: (w.update({'name': e.value}), on_refresh())).props('dark outlined dense use-input hide-selected').classes('w-full mb-4')
            with ui.row().classes('w-full gap-4'):
                ui.number('等级', value=w['level'], on_change=lambda e: (w.update({'level': int(e.value or 0)}), on_refresh())).props('dark outlined dense').classes('flex-grow')
                ui.select([1,2,3,4,5], label='精炼', value=w['refinement'], on_change=lambda e: (w.update({'refinement': e.value}), on_refresh())).props('dark outlined dense').classes('flex-grow')
    
    with ui.element('div').classes('genshin-card genshin-glass w-full p-8 border border-white/10 mt-6'):
        ui.label('圣遗物').classes('text-[10px] font-black opacity-30 mb-8')
        with ui.grid(columns=5).classes('w-full gap-4'):
            for k, arti in char_data['artifacts'].items():
                with ui.column().classes('p-4 bg-white/5 rounded-xl border border-white/5 h-full justify-between'):
                    with ui.column().classes('w-full gap-1'):
                        ui.label(arti['slot']).classes('text-[9px] font-black opacity-40')
                        ui.select(state.artifact_sets, value=arti['set_name'] if arti['set_name'] in state.artifact_sets else None, with_input=True, on_change=lambda e, a=arti: (a.update({'set_name': e.value}), on_refresh())).props('dark borderless dense use-input hide-selected').classes('text-xs font-bold w-full')
                        ui.input('主词条', value=arti['main_stat'], on_change=lambda e, a=arti: a.update({'main_stat': e.value})).props('dark borderless dense').classes('text-[10px] opacity-60')
                    
                    with ui.column().classes('w-full gap-1 mt-4'):
                        ui.label('副词条').classes('text-[8px] opacity-20 uppercase')
                        for sub in arti['sub_stats'][:4]:
                            ui.label(f"{sub['name']} {sub['value']}").classes('text-[9px] opacity-50 truncate')
                        ui.button(icon='edit', on_click=lambda a=arti: open_substat_editor(a, on_refresh)).props('flat round size=xs').classes('self-end mt-2')
