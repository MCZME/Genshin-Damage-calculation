import flet as ft
from typing import Dict, Any, List
from ui.states.tactical_state import TacticalState
from ui.theme import GenshinTheme
from ui.states.app_state import AppState
from ui.components.tactical.action_card import ActionCard
from ui.components.tactical.tactical_action_btn import TacticalActionBtn
from ui.components.tactical.tactical_member_slot import TacticalMemberSlot
from ui.services.ui_formatter import UIFormatter
from core.data_models.action_data_model import ActionDataModel
from core.registry import CharacterClassMap, initialize_registry

class TacticalView:
    """
    战术视图重构版 (MVVM V5.0)
    已恢复原始代码中的 Schema 驱动型参数编辑器逻辑。
    """
    def __init__(self, state: AppState):
        self.app_state = state
        self.library_vm = state.library_vm
        # 确保注册表已初始化
        initialize_registry()

    def _get_default_metadata(self) -> Dict[str, Any]:
        """兜底默认元数据"""
        return {
            "normal_attack": {"label": "普通攻击", "params": [{"key": "count", "label": "连招次数", "type": "int", "min": 1, "max": 5, "default": 1}]},
            "elemental_skill": {"label": "元素战技", "params": []},
            "elemental_burst": {"label": "元素爆发", "params": []},
            "charged_attack": {"label": "重击", "params": []},
            "dash": {"label": "冲刺", "params": []},
            "skip": {"label": "等待", "params": [{"key": "frames", "label": "帧数", "type": "int", "default": 60}]}
        }

    def _get_char_metadata(self, char_name: str) -> Dict[str, Any]:
        """获取指定角色的动作元数据"""
        if char_name in CharacterClassMap:
            cls = CharacterClassMap[char_name]
            if hasattr(cls, "get_action_metadata"):
                return cls.get_action_metadata()
        return self._get_default_metadata()

    @ft.component
    def build(self, state: TacticalState):
        # 1. 局部 UI 状态管理
        active_member_index, set_active_member_index = ft.use_state(0)
        
        # 2. 获取数据 (直接从传入的 state 中解构 VM 以激活响应式)
        vm = state.page_vm
        sequence_vms = vm.sequence_vms
        selected_index = vm.selected_index
        team_data = self.app_state.strategic_state.team_data

        # 3. 辅助方法
        def get_char_name(char_id):
            for m in team_data:
                if m.get("id") == char_id: return m.get("name", "Unknown")
            return "Unknown"

        def get_char_element(char_id):
            for m in team_data:
                if m.get("id") == char_id: return m.get("element", "Neutral")
            return "Neutral"

        # 4. 布局组件构建
        header = ft.Row([
            ft.Text("战术动作编排", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ft.Row([
                ft.TextButton("清空序列", icon=ft.Icons.DELETE_SWEEP, icon_color=ft.Colors.RED_400, on_click=lambda _: [vm.clear_sequence(), state.notify()]),
            ], spacing=10)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        sidebar = ft.Column([
            TacticalMemberSlot(
                i, team_data[i], 
                is_selected=(i == active_member_index),
                on_click=set_active_member_index
            ) for i in range(4)
        ], width=180, expand=True, spacing=10)

        sequence_items = []
        for i, action_vm in enumerate(sequence_vms):
            sequence_items.append(
                ActionCard(
                    vm=action_vm,
                    index=i,
                    char_name=get_char_name(action_vm.char_id),
                    element=get_char_element(action_vm.char_id),
                    is_selected=(i == selected_index),
                    on_click=lambda idx: [vm.select_action(idx), state.notify()],
                    on_delete=lambda idx: [vm.remove_action(idx), state.notify()]
                )
            )
            if i < len(sequence_vms) - 1:
                sequence_items.append(ft.Icon(ft.Icons.CHEVRON_RIGHT, size=14, color=ft.Colors.WHITE_10))

        sequence_axis = ft.Column([
            ft.Row([
                ft.Text("执行序列流", size=16, weight=ft.FontWeight.BOLD, opacity=0.8),
                ft.Text(f"({len(sequence_vms)} Actions)", size=11, color=GenshinTheme.TEXT_SECONDARY),
            ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Container(
                content=ft.Row(sequence_items, spacing=8, run_spacing=8, wrap=True),
                padding=ft.Padding(0, 5, 0, 10), expand=True
            )
        ], spacing=10, expand=True, scroll=ft.ScrollMode.HIDDEN)

        # 4.4 指令库与编辑器
        active_member = team_data[active_member_index]
        selected_action_vm = sequence_vms[selected_index] if 0 <= selected_index < len(sequence_vms) else None
        
        # 4.4.1 指令库构建
        if active_member.get("id") is None:
            command_library = ft.Column([
                ft.Text("尚未配置角色", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE_24),
                ft.Text("请先到战略视图中配置角色。", size=12, color=GenshinTheme.TEXT_SECONDARY)
            ], expand=True, spacing=10, alignment=ft.MainAxisAlignment.CENTER)
        else:
            char_meta = self._get_char_metadata(active_member.get("name"))
            order = ["normal_attack", "charged_attack", "elemental_skill", "elemental_burst", "dash", "skip"]
            
            rows = []
            current_row = []
            for key in order:
                if key in char_meta:
                    info = char_meta[key]
                    # 准备默认参数
                    default_params = {p['key']: p.get('default') for p in info.get('params', []) if 'default' in p}
                    
                    btn = TacticalActionBtn(
                        key, info.get("label", key), active_member.get("element", "Neutral"),
                        on_click=lambda k, dp=default_params: [
                            vm.add_action(ActionDataModel.create(active_member['id'], k, params=dp.copy())), 
                            state.notify()
                        ]
                    )
                    current_row.append(btn)
                    if len(current_row) == 2:
                        rows.append(ft.Row(current_row, spacing=15))
                        current_row = []
            if current_row: rows.append(ft.Row(current_row, spacing=15))

            command_library = ft.Column([
                ft.Text("招式指令选单", size=12, weight=ft.FontWeight.W_600, opacity=0.4),
                *rows,
                ft.Text("点击招式向序列末尾追加动作", size=10, color=GenshinTheme.TEXT_SECONDARY, italic=True)
            ], spacing=10)

        # 4.4.2 参数编辑器 (恢复 Schema 驱动逻辑)
        inspector_controls = []
        if selected_action_vm:
            # 获取当前选中动作所属角色的元数据
            sel_char_name = get_char_name(selected_action_vm.char_id)
            sel_char_meta = self._get_char_metadata(sel_char_name)
            action_info = sel_char_meta.get(selected_action_vm.action_key, {})
            params_schema = action_info.get("params", [])

            for p in params_schema:
                p_key = p['key']
                p_label = p['label']
                p_type = p.get('type', 'int')
                # 优先从 VM 获取当前值，没有则用 schema 默认值
                current_val = selected_action_vm.params.get(p_key, p.get('default'))
                
                if p_type == 'int':
                    # 如果范围较小，使用 Slider
                    if 'min' in p and 'max' in p and (p['max'] - p['min']) <= 10:
                        inspector_controls.append(ft.Column([
                            ft.Row([
                                ft.Text(p_label, size=11, color=GenshinTheme.TEXT_SECONDARY),
                                ft.Text(str(current_val), size=11, weight=ft.FontWeight.BOLD, color=GenshinTheme.PRIMARY)
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Slider(
                                min=p['min'], max=p['max'], divisions=p['max']-p['min'],
                                value=float(current_val),
                                on_change=lambda e, k=p_key: [selected_action_vm.set_param(k, int(e.control.value)), state.notify()]
                            )
                        ], spacing=0))
                    else:
                        inspector_controls.append(ft.TextField(
                            label=p_label, value=str(current_val),
                            dense=True, text_size=12, border_color=ft.Colors.WHITE_10,
                            on_change=lambda e, k=p_key: [selected_action_vm.set_param(k, e.control.value), state.notify()]
                        ))
                elif p_type == 'select':
                    options = p.get('options', {})
                    inspector_controls.append(ft.Dropdown(
                        label=p_label, value=str(current_val),
                        options=[ft.dropdown.Option(str(opt_k), text=str(opt_v)) for opt_k, opt_v in options.items()],
                        dense=True, text_size=12, border_color=ft.Colors.WHITE_10,
                        on_change=lambda e, k=p_key: [selected_action_vm.set_param(k, e.control.value), state.notify()]
                    ))
                elif p_type == 'bool':
                    inspector_controls.append(ft.Switch(
                        label=p_label, value=bool(current_val),
                        on_change=lambda e, k=p_key: [selected_action_vm.set_param(k, e.control.value), state.notify()]
                    ))

            if not inspector_controls:
                inspector_controls.append(ft.Text("此动作无额外参数", size=12, italic=True, color=ft.Colors.WHITE_24))

            params_panel = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("动作参数编辑", size=14, weight=ft.FontWeight.BOLD, opacity=0.6, expand=True),
                        ft.IconButton(ft.Icons.CHEVRON_LEFT, icon_size=16, on_click=lambda _: [vm.move_action(selected_index, selected_index-1), state.notify()], disabled=selected_index<=0),
                        ft.IconButton(ft.Icons.CHEVRON_RIGHT, icon_size=16, on_click=lambda _: [vm.move_action(selected_index, selected_index+1), state.notify()], disabled=selected_index>=len(sequence_vms)-1),
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Column(inspector_controls, spacing=10)
                ], spacing=10),
                padding=15, bgcolor=ft.Colors.with_opacity(0.02, ft.Colors.WHITE), border_radius=12
            )
        else:
            params_panel = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.TOUCH_APP_OUTLINED, size=32, color=ft.Colors.WHITE_10),
                    ft.Text("请在右侧选择一个动作进行编辑", size=12, color=ft.Colors.WHITE_24, text_align=ft.TextAlign.CENTER)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                padding=30, alignment=ft.Alignment.CENTER, 
                bgcolor=ft.Colors.with_opacity(0.01, ft.Colors.WHITE), border_radius=12
            )

        mid_section = ft.Column([command_library, ft.Divider(height=1, color=ft.Colors.WHITE_10), params_panel], width=240, spacing=15)

        # 5. 组装最终布局
        return ft.Container(
            content=ft.Column([
                header,
                ft.Row([
                    ft.Container(content=sidebar, width=160),
                    ft.VerticalDivider(width=1, color=ft.Colors.with_opacity(0.1, GenshinTheme.ON_SURFACE)),
                    ft.Row([
                        mid_section,
                        ft.VerticalDivider(width=1, color=ft.Colors.WHITE_10),
                        sequence_axis
                    ], expand=True, vertical_alignment=ft.CrossAxisAlignment.START)
                ], expand=True)
            ], spacing=10),
            padding=15, expand=True, bgcolor=GenshinTheme.BACKGROUND
        )
