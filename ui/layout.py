from nicegui import ui
from contextlib import contextmanager
from ui.theme import GenshinTheme

class AppShell:
    """
    V2.2 MD3 Panes 架构
    面板化布局，强调层级与独立容器感
    """
    def __init__(self, title: str = "GENSHIN WORKBENCH"):
        self.title = title
        GenshinTheme.apply()

    def header(self, current_phase: str = 'strategic', on_phase_change=None):
        """全宽玻璃状态栏 (MD3 Top App Bar)"""
        with ui.header().classes('genshin-glass border-b border-white/5 items-center justify-between px-8 py-3'):
            self.header_content(current_phase, on_phase_change)

    def header_content(self, current_phase: str = 'strategic', on_phase_change=None):
        """渲染顶栏内部内容"""
        with ui.row().classes('items-center gap-6'):
            # 品牌区
            with ui.row().classes('items-center gap-3'):
                with ui.element('div').classes('w-1 h-5 bg-[var(--md-primary)] rounded-full'): pass
                ui.label(self.title).classes('text-xs font-bold tracking-[0.3em] uppercase opacity-90')
            
            # 阶段切换器 (Segmented Control)
            with ui.row().classes('bg-white/5 p-1 rounded-full border border-white/5'):
                phases = [
                    ('strategic', '战略', 'settings'),
                    ('tactical', '战术', 'timeline'),
                    ('review', '复盘', 'analytics'),
                ]
                for phase_id, label, icon in phases:
                    is_active = current_phase == phase_id
                    color = 'primary' if is_active else 'white'
                    btn = ui.button(label, icon=icon).props(f'flat rounded size=sm color={color}').classes(f'px-6 text-[10px] font-black tracking-widest {"" if is_active else "opacity-30"}')
                    if on_phase_change:
                        btn.on('click', lambda p=phase_id: on_phase_change(p))

        with ui.row().classes('gap-3'):
            ui.button(icon='notifications').props('flat round size=sm color=white').classes('opacity-50')
            ui.button(icon='more_vert').props('flat round size=sm color=white').classes('opacity-50')

    def footer(self):
        """厚重的悬浮控制岛 (MD3 Prominent Bottom Bar)"""
        with ui.footer().classes('bg-transparent px-4 pb-4 pt-0 h-24'):
            with ui.row().classes('w-full genshin-glass genshin-pane px-10 h-full items-center justify-between shadow-[0_-10px_40px_rgba(0,0,0,0.4)]'):
                with ui.row().classes('items-center gap-8'):
                    # 仿真控制 - 按钮加大
                    ui.button('开始仿真', icon='bolt', color='primary').classes('px-12 py-2 rounded-full font-black shadow-2xl shadow-primary/40 text-sm').props('no-caps elevated')
                    
                    with ui.column().classes('gap-0'):
                        ui.label('SYSTEM STATUS').classes('text-[9px] font-black tracking-[0.2em] text-primary opacity-80')
                        ui.label('READY TO EXECUTE').classes('text-[11px] font-bold tracking-[0.1em] text-white/40')
                
                with ui.row().classes('gap-8 opacity-40'):
                    with ui.column().classes('items-end gap-0'):
                        ui.label('DATABASE').classes('text-[8px] font-black tracking-widest')
                        ui.label('CONNECTED').classes('text-[10px] font-bold text-green-500')
                    
                    with ui.column().classes('items-end gap-0'):
                        ui.label('ENGINE').classes('text-[8px] font-black tracking-widest')
                        ui.label('V2.2.0-STABLE').classes('text-[10px] font-bold')

    @contextmanager
    def left_column(self):
        """独立面板: 实体池"""
        with ui.column().classes('w-[300px] h-full genshin-glass genshin-pane p-6 shrink-0'):
            ui.label('ENTITY POOL').classes('text-[10px] font-black tracking-[0.3em] opacity-30 mb-8')
            yield

    @contextmanager
    def middle_column(self):
        """独立面板: 工作区"""
        with ui.column().classes('flex-grow h-full genshin-glass genshin-pane p-8 overflow-y-auto'):
            yield

    @contextmanager
    def right_column(self):
        """独立面板: 战术雷达"""
        with ui.column().classes('w-[380px] h-full genshin-glass genshin-pane p-6 shrink-0'):
            ui.label('TACTICAL RADAR').classes('text-[10px] font-black tracking-[0.3em] opacity-30 mb-8')
            yield
