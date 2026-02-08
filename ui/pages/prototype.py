from nicegui import ui
from ui.layout import AppShell
from ui.theme import GenshinTheme

# 模拟状态
class PrototypeState:
    def __init__(self):
        self.selected_entity = None
        self.team = [
            {"name": "胡桃", "element": "Pyro", "level": 90, "weapon": "护摩之杖"},
            {"name": "行秋", "element": "Hydro", "level": 80, "weapon": "祭礼剑"},
            {"name": "纳西妲", "element": "Dendro", "level": 90, "weapon": "千夜浮梦"},
        ]

state = PrototypeState()

@ui.page('/prototype')
def prototype_page():
    shell = AppShell()
    shell.header()
    shell.footer()

    # 主布局容器：h-[calc(100vh-160px)] 兼顾厚重的 Footer 和紧凑的面板间距
    with ui.row().classes('w-full h-[calc(100vh-160px)] no-wrap gap-4 p-4'):
        
        # --- 左栏: 实体池 ---
        with shell.left_column():
            with ui.column().classes('gap-3 w-full'):
                for char in state.team:
                    # MD3 风格选择项
                    is_selected = state.selected_entity == char
                    bg_class = 'bg-[var(--md-primary-container)]' if is_selected else 'bg-white/5'
                    border_class = 'border-[var(--md-primary)]' if is_selected else 'border-transparent'
                    
                    with ui.element('div').classes(f'genshin-card p-4 {bg_class} border {border_class} cursor-pointer hover:bg-white/10 transition-all') \
                        .on('click', lambda c=char: select_char(c)):
                        with ui.row().classes('items-center gap-4'):
                            color = GenshinTheme.ELEMENTS.get(char['element'], {}).get('primary', '#fff')
                            ui.element('div').classes('w-3 h-3 rounded-full').style(f'background-color: {color}; box-shadow: 0 0 8px {color}')
                            ui.label(char['name']).classes('text-xs font-bold tracking-widest')
                
                ui.button('ADD ENTITY', icon='add').props('flat size=sm color=white').classes('w-full border border-dashed border-white/10 rounded-xl mt-4 opacity-40')

        # --- 中栏: 工作区 ---
        with shell.middle_column():
            container = ui.column().classes('w-full p-12 max-w-5xl mx-auto')
            
            def render_content():
                container.clear()
                with container:
                    if not state.selected_entity:
                        # 全景概览
                        ui.label('STRATEGIC OVERVIEW').classes('text-[10px] font-black tracking-[0.4em] opacity-30 mb-12')
                        with ui.row().classes('w-full gap-6'):
                            for char in state.team:
                                with ui.element('div').classes('genshin-card genshin-glass flex-grow p-8 border border-white/5 relative group'):
                                    ui.element('div').classes('absolute top-0 right-0 w-8 h-8 border-t border-r border-white/20 rounded-tr-3xl')
                                    
                                    ui.label(char['name']).classes('text-3xl font-black mb-1 tracking-tighter')
                                    ui.label(char['element'].upper()).classes('text-[10px] font-bold opacity-40 tracking-widest mb-6')
                                    
                                    with ui.row().classes('items-center gap-2'):
                                        ui.icon('bolt', size='16px', color='white').classes('opacity-20')
                                        ui.label(char['weapon']).classes('text-xs opacity-60')
                                    
                                    ui.button('EDIT', on_click=lambda c=char: select_char(c)).props('flat rounded size=sm color=white').classes('mt-8 opacity-0 group-hover:opacity-100 transition-opacity')
                    else:
                        # 编辑模式 (MD3 Form)
                        char = state.selected_entity
                        GenshinTheme.set_element(char['element'])
                        
                        with ui.row().classes('items-center gap-4 mb-10'):
                            ui.button(icon='arrow_back', on_click=lambda: select_char(None)).props('flat round color=white')
                            ui.label(f'CONFIGURATION / {char["name"]}').classes('text-xl font-black tracking-widest')
                        
                        with ui.element('div').classes('genshin-card genshin-glass w-full p-10 border border-white/10'):
                            with ui.row().classes('w-full gap-16'):
                                with ui.column().classes('gap-8 flex-grow'):
                                    ui.label('BASE ATTRIBUTES').classes('text-[10px] font-black opacity-30 tracking-[0.3em]')
                                    ui.number(label='LEVEL', value=char['level']).props('outlined dark').classes('w-full')
                                    ui.select(options=['C0', 'C1', 'C2', 'C6'], label='CONSTELLATION', value='C1').props('outlined dark').classes('w-full')
                                
                                with ui.column().classes('gap-8 flex-grow'):
                                    ui.label('ARTIFACT STATS').classes('text-[10px] font-black opacity-30 tracking-[0.3em]')
                                    with ui.grid(columns=2).classes('w-full gap-4'):
                                        ui.number(label='CRIT %', value=31.1).props('outlined dark dense').classes('flex-grow')
                                        ui.number(label='CDMG %', value=120.5).props('outlined dark dense').classes('flex-grow')

            def select_char(char):
                state.selected_entity = char
                render_content()

            render_content()

        # --- 右栏: 战术雷达 ---
        with shell.right_column():
            with ui.column().classes('w-full aspect-square rounded-full border border-white/10 relative flex items-center justify-center'):
                ui.element('div').classes('absolute w-full h-full rounded-full bg-gradient-to-tr from-[var(--md-primary)]/10 to-transparent animate-spin-slow')
                ui.html('<div class="absolute inset-12 rounded-full border border-white/5"></div>')
                ui.html('<div class="absolute inset-24 rounded-full border border-white/5"></div>')
                ui.element('div').classes('w-3 h-3 bg-[var(--md-primary)] rounded-full shadow-[0_0_15px_var(--md-primary)] z-10')
            
            with ui.column().classes('mt-12 gap-8 w-full'):
                with ui.column().classes('gap-2'):
                    ui.label('POSITION (M)').classes('text-[10px] font-black opacity-30 tracking-widest')
                    with ui.row().classes('w-full gap-4'):
                        ui.number(label='X', value=1.0).props('outlined dark dense').classes('flex-grow')
                        ui.number(label='Z', value=1.5).props('outlined dark dense').classes('flex-grow')
                
                ui.button('RESET POSITION', icon='refresh').props('flat size=sm color=white').classes('w-full opacity-40')

    ui.add_head_html('<style>@keyframes spin-slow { from { transform: rotate(0deg); } to { transform: rotate(360deg); } } .animate-spin-slow { animation: spin-slow 10s linear infinite; } .nicegui-content { padding: 0 !important; overflow: hidden; }</style>')
