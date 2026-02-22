import flet as ft
import asyncio
from typing import Dict, Any, List
from ui.theme import GenshinTheme
from ui.reboot.state import StrategicState
from ui.reboot.tactical_state import TacticalState, ActionUnit
from ui.reboot.components.action_card import ActionCard
from ui.state import AppState

class TacticalView(ft.Container):
    """
    战术视图重构版 - 极致精简版。
    专注序列编排与动作特定参数配置，移除不可知数据与冗余操作。
    """
    def __init__(self, app_state: AppState = None):
        super().__init__()
        self.app_state = app_state or AppState()
        self.strat_state = self.app_state.strategic_state
        self.state = self.app_state.tactical_state
        self.expand = True
        self.bgcolor = GenshinTheme.BACKGROUND
        self.padding = 0 
        
        # 内部状态：当前正在为哪个角色选招
        self.active_member_index = 0
        
        # 缓存当前队伍所有角色的元数据
        self.team_metadata: Dict[int, Dict[str, Any]] = {} # char_id -> metadata
        self._discover_team_metadata()
        
        self._build_ui()

    def did_mount(self):
        pass

    def _discover_team_metadata(self):
        """通过注册表反射发现队伍中所有角色的动作 Schema"""
        from core.registry import CharacterClassMap, initialize_registry
        
        # 确保注册表已初始化
        initialize_registry()
        
        self.team_metadata = {}
        for member in self.strat_state.team_data:
            char_id = member.get("id")
            char_name = member.get("name")
            if char_id is not None and char_name in CharacterClassMap:
                cls = CharacterClassMap[char_name]
                if hasattr(cls, "get_action_metadata"):
                    self.team_metadata[char_id] = cls.get_action_metadata()
                else:
                    self.team_metadata[char_id] = self._get_default_metadata()
            elif char_id is not None:
                # 已配置但未实现的角色，赋予基础模型
                self.team_metadata[char_id] = self._get_default_metadata()

    def _get_default_metadata(self) -> Dict[str, Any]:
        """为未显式定义元数据的角色提供标准动作模板"""
        return {
            "normal_attack": {"label": "普通攻击", "params": [{"key": "count", "label": "连招次数", "type": "int", "min": 1, "max": 5, "default": 1}]},
            "elemental_skill": {"label": "元素战技", "params": []},
            "elemental_burst": {"label": "元素爆发", "params": []},
            "charged_attack": {"label": "重击", "params": []},
            "dash": {"label": "冲刺", "params": []},
            "skip": {"label": "等待", "params": [{"key": "frames", "label": "帧数", "type": "int", "default": 60}]}
        }


    def _build_ui(self):
        # 1. 顶部操作栏
        self.header = ft.Row([
            ft.Text("战术动作编排", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ft.Row([
                ft.TextButton("清空序列", icon=ft.Icons.DELETE_SWEEP, icon_color=ft.Colors.RED_400, on_click=lambda _: self._handle_clear_all()),
            ], spacing=10)

        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        # 2. 左侧成员侧边栏 (镜像战略页)
        self.sidebar_slots = [self._build_member_slot(i) for i in range(4)]
        self.sidebar = ft.Column(self.sidebar_slots, width=180, expand=True, spacing=10)

        # 3. 动态工作台内容
        self.workbench_content = ft.Column(
            controls=self._build_workbench_controls(),
            expand=True,
        )

        # 组装主布局
        self.main_layout = ft.Container(
            content=ft.Column([
                self.header,
                ft.Row([
                    ft.Container(content=self.sidebar, width=160),
                    ft.VerticalDivider(width=1, color=ft.Colors.with_opacity(0.1, GenshinTheme.ON_SURFACE)),
                    ft.Container(content=self.workbench_content, expand=True)
                ], expand=True)
            ], spacing=10),
            padding=15,
            expand=True
        )
        self.content = self.main_layout

    def _build_workbench_controls(self):
        # --- A. 上半区：执行序列轴 (支持拖拽排序) ---
        
        # 1. 构造带连线的动作单元
        sequence_items = []
        for i, unit in enumerate(self.state.sequence):
            # 动作胶囊
            card = ActionCard(
                index=i,
                char_name=self._get_char_name(unit.char_id),
                action_name=unit.action_type,
                element=self._get_char_element(unit.char_id),
                is_selected=(i == self.state.selected_index),
                on_click=self._handle_click_action,
                on_delete=self._handle_delete_action
            )
            card.key = unit.uid # ReorderableListView 必须有唯一 key
            
            sequence_items.append(card)
            
            # 在动作之间加上箭头 (独立节点，利于排字流转折)
            is_last = (i == len(self.state.sequence) - 1)
            if not is_last:
                sequence_items.append(
                    ft.Icon(ft.Icons.CHEVRON_RIGHT, size=14, color=ft.Colors.WHITE_10, key=f"arrow_{unit.uid}")
                )

        sequence_axis = ft.Column([
            ft.Row([
                ft.Text("执行序列流", size=16, weight=ft.FontWeight.BOLD, opacity=0.8),
                ft.Text(f"({len(self.state.sequence)} Actions | 瀑布流排版)", size=11, color=GenshinTheme.TEXT_SECONDARY),
            ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            
            ft.Container(
                content=ft.Row(
                    controls=sequence_items,
                    spacing=8,
                    run_spacing=8,
                    wrap=True,
                ),
                padding=ft.Padding(0, 5, 0, 10),
                expand=True
            )
        ], spacing=10, expand=True, scroll=ft.ScrollMode.HIDDEN)


        # --- B. 下半区：指令与参数工作台 ---
        active_member = self.strat_state.team_data[self.active_member_index]
        elem_color = GenshinTheme.get_element_color(active_member.get("element", "Neutral"))
        selected_unit = self.state.selected_action
        
        # B1. 左侧：招式指令库
        is_empty = active_member.get("id") is None
        if is_empty:
            command_library = ft.Column([
                ft.Text("尚未配置角色", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE_24),
                ft.Text("请先到战略视图中为该槽位配置角色。", size=12, color=GenshinTheme.TEXT_SECONDARY)
            ], expand=True, spacing=10, alignment=ft.MainAxisAlignment.CENTER)
        else:
            # 角色 Banner
            banner = ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Text(active_member.get("name", "?")[0], size=14, weight=ft.FontWeight.W_900),
                        width=32, height=32, bgcolor=ft.Colors.with_opacity(0.3, elem_color),
                        border_radius=16, alignment=ft.Alignment.CENTER,
                        border=ft.Border.all(1, ft.Colors.with_opacity(0.5, elem_color))
                    ),
                    ft.Column([
                        ft.Text(active_member.get('name', '未选定'), size=14, weight=ft.FontWeight.W_900),
                        ft.Text(f"{active_member.get('element', 'Neutral')} 元素角色", size=9, opacity=0.6),
                    ], spacing=-2)
                ], spacing=10),
                padding=ft.Padding(12, 10, 12, 10),
                bgcolor=ft.Colors.with_opacity(0.12, elem_color),
                border_radius=12,
                border=ft.Border.all(1, ft.Colors.with_opacity(0.1, elem_color))
            )

            # 根据元数据动态生成指令按钮
            metadata = self.team_metadata.get(active_member.get("id"), self._get_default_metadata())
            
            action_buttons = []
            # 建立标准顺序：普攻 -> 重击 -> 战技 -> 爆发 -> 冲刺 -> 等待
            order = ["normal_attack", "charged_attack", "elemental_skill", "elemental_burst", "dash", "skip"]
            
            # 按顺序组织按钮
            rows = []
            current_row = []
            
            for key in order:
                if key in metadata:
                    info = metadata[key]
                    btn = self._build_action_btn(key, info.get("label", key), active_member)
                    current_row.append(btn)
                    
                    if len(current_row) == 2:
                        rows.append(ft.Row(current_row, spacing=15))
                        current_row = []
            
            if current_row:
                rows.append(ft.Row(current_row, spacing=15))

            command_library = ft.Column([
                banner,
                ft.Text("招式指令选单", size=12, weight=ft.FontWeight.W_600, opacity=0.4, margin=ft.margin.only(top=5)),
                *rows,
                ft.Container(height=5),
                ft.Text("点击招式即向序列末尾追加动作", size=10, color=GenshinTheme.TEXT_SECONDARY, italic=True)
            ], spacing=10)


        # B2. 右侧：参数编辑面板 (模仿场景页布局)
        display_label = ""
        if selected_unit:
            metadata = self.team_metadata.get(selected_unit.char_id, {})
            action_info = metadata.get(selected_unit.action_type, {})
            display_label = f"{self._get_char_name(selected_unit.char_id)}: {action_info.get('label', selected_unit.action_type)}"

        inspector_content = ft.Column([
            ft.Text("动作参数编辑", size=14, weight=ft.FontWeight.BOLD, opacity=0.6),
            ft.Column([
                # 状态提示与位移操作
                ft.Row([
                    ft.Text("请点击序列流中的动作" if not selected_unit else f"正在编辑: {display_label}", 
                            size=12, italic=True, color=GenshinTheme.TEXT_SECONDARY, expand=True),
                    
                    # 移动按钮 (左/右)
                    ft.IconButton(
                        icon=ft.Icons.CHEVRON_LEFT, 
                        icon_size=18, width=30, height=30,
                        tooltip="将当前动作向左移",
                        disabled=not selected_unit or self.state.selected_index <= 0,
                        on_click=lambda _: self._handle_move_action(-1)
                    ),
                    ft.IconButton(
                        icon=ft.Icons.CHEVRON_RIGHT, 
                        icon_size=18, width=30, height=30,
                        tooltip="将当前动作向右移",
                        disabled=not selected_unit or self.state.selected_index >= len(self.state.sequence) - 1,
                        on_click=lambda _: self._handle_move_action(1)
                    )
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                
                # 动态参数录入 (Inspector)
                *(self._build_params_inspector(selected_unit) if selected_unit else [])
            ], spacing=15, expand=True)
        ], spacing=10)


        params_panel = ft.Container(
            content=inspector_content,
            padding=ft.Padding(20, 15, 20, 15),
            bgcolor=ft.Colors.with_opacity(0.02, ft.Colors.WHITE),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.05, ft.Colors.WHITE)),
            border_radius=12,
        )

        mid_section = ft.Column([
            command_library,
            ft.Divider(height=1, color=ft.Colors.WHITE_10),
            params_panel
        ], width=240, spacing=15)

        right_flow = ft.Container(
            content=sequence_axis,
            expand=True,
            padding=ft.Padding(15, 0, 0, 0),
        )
        return [
            ft.Row([
                mid_section,
                ft.VerticalDivider(width=1, color=ft.Colors.WHITE_10),
                right_flow
            ], expand=True, vertical_alignment=ft.CrossAxisAlignment.START)
        ]

    def _build_params_inspector(self, unit: ActionUnit):
        """核心逻辑：根据元数据动态渲染配置控件"""
        metadata = self.team_metadata.get(unit.char_id, self._get_default_metadata())
        action_info = metadata.get(unit.action_type, {})
        params_schema = action_info.get("params", [])
        
        controls = []
        for p in params_schema:
            p_key = p['key']
            p_label = p['label']
            p_type = p.get('type', 'int')
            current_val = unit.params.get(p_key, p.get('default'))
            
            if p_type == 'int':
                # 如果有范围且范围较小，使用滑块
                if 'min' in p and 'max' in p and (p['max'] - p['min']) <= 10:
                    controls.append(ft.Column([
                        ft.Row([
                            ft.Text(p_label, size=11, color=GenshinTheme.TEXT_SECONDARY),
                            ft.Text(str(current_val), size=11, weight=ft.FontWeight.BOLD, color=GenshinTheme.PRIMARY)
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Slider(
                            min=p['min'], max=p['max'], divisions=p['max']-p['min'],
                            value=current_val,
                            on_change=lambda e, k=p_key: self._handle_param_change(k, int(e.control.value))
                        )
                    ], spacing=0))
                else:
                    # 传统的输入框
                    controls.append(ft.TextField(
                        label=p_label, value=str(current_val),
                        dense=True, text_size=12, border_color=ft.Colors.WHITE_10,
                        on_change=lambda e, k=p_key: self._handle_param_change(k, e.control.value)
                    ))
            elif p_type == 'select':
                options = p.get('options', {})
                controls.append(ft.Dropdown(
                    label=p_label, value=current_val,
                    options=[ft.dropdown.Option(k, text=v) for k, v in options.items()],
                    dense=True, text_size=12, border_color=ft.Colors.WHITE_10,
                    on_select=lambda e, k=p_key: self._handle_param_change(k, e.control.value)
                ))
            elif p_type == 'bool':
                controls.append(ft.Switch(
                    label=p_label, value=bool(current_val),
                    on_change=lambda e, k=p_key: self._handle_param_change(k, e.control.value)
                ))
        
        return controls


    def _build_member_slot(self, index: int):
        member = self.strat_state.team_data[index]
        is_empty = member.get("id") is None
        is_active = (index == self.active_member_index)
        elem_color = GenshinTheme.get_element_color(member.get("element", "Neutral"))

        if is_empty:
            return ft.Container(
                content=ft.Text("未配置角色", size=11, color=ft.Colors.WHITE_24),
                height=60, alignment=ft.Alignment.CENTER,
                bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.WHITE),
                border_radius=12, border=ft.Border.all(1, ft.Colors.with_opacity(0.12, ft.Colors.WHITE))
            )

        bg_opacity = 0.28 if is_active else 0.10
        avatar = ft.Container(
            content=ft.Text(member.get("name", "?")[0], size=15, weight=ft.FontWeight.W_900, color=ft.Colors.WHITE),
            width=36, height=36, bgcolor=ft.Colors.with_opacity(0.3, elem_color),
            border_radius=18, alignment=ft.Alignment.CENTER,
            border=ft.Border.all(1.5, ft.Colors.with_opacity(0.6 if is_active else 0.25, elem_color))
        )

        return ft.Container(
            content=ft.Row([
                avatar,
                ft.Column([
                    ft.Text(member.get("name", "未选定"), size=13, weight=ft.FontWeight.W_900 if is_active else ft.FontWeight.BOLD),
                    ft.Text(member.get("element", "Neutral"), size=10, opacity=0.5),
                ], spacing=1, expand=True)
            ], spacing=9, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding(11, 11, 11, 11),
            height=60, border_radius=12,
            bgcolor=ft.Colors.with_opacity(bg_opacity, elem_color),
            border=ft.Border.all(2 if is_active else 1, ft.Colors.with_opacity(0.65 if is_active else 0.12, elem_color)),
            on_click=lambda _: self._handle_member_select(index),
            offset=ft.Offset(0.04, 0) if is_active else ft.Offset(0, 0),
            animate=ft.Animation(300, ft.AnimationCurve.DECELERATE),
            animate_offset=ft.Animation(300, ft.AnimationCurve.EASE_OUT_BACK),
        )

    def _build_action_btn(self, action_key: str, label: str, member: dict):
        elem_color = GenshinTheme.get_element_color(member.get("element", "Neutral"))
        
        # 简化显示标签 (例如: 普通攻击 -> 普攻)
        short_label = label.replace("普通攻击", "普攻").replace("元素战技", "战技").replace("元素爆发", "爆发")
        
        c = ft.Container(
            content=ft.Text(short_label, size=12, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER),
            width=100, height=45,
            bgcolor=ft.Colors.with_opacity(0.1, elem_color),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.4, elem_color)),
            border_radius=8,
            alignment=ft.Alignment.CENTER,
            on_click=lambda _: self._handle_add_action(member['id'], action_key),
            tooltip=label
        )
        c.mouse_cursor = ft.MouseCursor.CLICK
        return c


    # --- 逻辑处理 ---
    def _handle_member_select(self, index):
        self.active_member_index = index
        # 切换成员时由于角色可能变动，重新同步一次元数据（确保最新）
        self._discover_team_metadata()
        self._refresh_all()

    def _handle_add_action(self, char_id, action_type):
        new_unit = ActionUnit(char_id, action_type)
        self.state.add_action(new_unit)
        self.state.selected_index = len(self.state.sequence) - 1 # 自动选中新加的
        self._refresh_all()

    def _handle_delete_action(self, index):
        self.state.remove_action(index)
        if self.state.selected_index >= len(self.state.sequence):
            self.state.selected_index = len(self.state.sequence) - 1
        self._refresh_all()

    def _handle_click_action(self, index):
        self.state.selected_index = index
        # 同步切换左侧角色面板（焦点与上下文一致性）
        unit = self.state.sequence[index]
        for i, m in enumerate(self.strat_state.team_data):
            if m.get("id") == unit.char_id:
                self.active_member_index = i
                break
        self._refresh_all()

    def _handle_move_action(self, direction):
        if self.state.selected_index < 0: return
        old_idx = self.state.selected_index
        new_idx = old_idx + direction
        
        if 0 <= new_idx < len(self.state.sequence):
            # 将该动作从列表中移出并重新插入
            self.state.move_action(old_idx, new_idx)
            self.state.selected_index = new_idx
            self._refresh_all()

    def _handle_param_change(self, key, val):
        if self.state.selected_action:
            self.state.selected_action.params[key] = val
            # 涉及数值变动时，刷新 Inspector 顶部的实时数值显示
            self._refresh_inspector_only()

    def _refresh_inspector_only(self):
        """只刷新参数面板，防止整个轴抖动"""
        try:
            self.workbench_content.controls = self._build_workbench_controls()
            self.update()
        except: pass

    def _handle_clear_all(self):
        self.state.sequence.clear()
        self.state.selected_index = -1
        self._refresh_all()

    def _refresh_all(self):
        self.workbench_content.controls = self._build_workbench_controls()
        self.sidebar.controls = [self._build_member_slot(i) for i in range(4)]
        self.update()

    def _get_char_element(self, char_id):
        for m in self.strat_state.team_data:
            if m.get("id") == char_id:
                return m.get("element", "Neutral")
        return "Neutral"

    def _get_char_name(self, char_id):
        """将 ID 转换为可读的角色名称"""
        for m in self.strat_state.team_data:
            if m.get("id") == char_id:
                return m.get("name", "Unknown")
        return "Unknown"

