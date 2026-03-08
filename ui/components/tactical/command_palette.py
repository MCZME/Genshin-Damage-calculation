import flet as ft
from collections.abc import Callable
from ui.components.tactical.tactical_action_btn import TacticalActionBtn
from ui.components.tactical.tactical_member_slot import TacticalMemberSlot

class CommandPalette:
    """
    指令调色盘：展示当前队伍成员及其可选招式
    """
    def __init__(self, team_data: list, on_action_add: Callable):
        self.team_data = team_data
        self.on_action_add = on_action_add

    @ft.component
    def build(self):
        active_index, set_active_index = ft.use_state(0)
        
        # 1. 获取当前选中的成员
        member = self.team_data[active_index]
        is_empty = member.get("id") is None

        # 2. 招式指令库逻辑
        if is_empty:
            command_library = ft.Column([
                ft.Text("尚未配置角色", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE_24),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=5)
        else:
            # 简单的招式列表（这里可以进一步根据角色元数据动态生成）
            # 目前采用标准招式集
            moves = [
                ("normal_attack", "普通攻击"),
                ("elemental_skill", "元素战技"),
                ("elemental_burst", "元素爆发"),
                ("charged_attack", "重击"),
                ("dash", "冲刺"),
                ("skip", "等待")
            ]
            
            rows = []
            for i in range(0, len(moves), 3):
                row_moves = moves[i:i+3]
                rows.append(ft.Row([
                    TacticalActionBtn(
                        m[0], m[1], 
                        member.get("element", "Neutral"),
                        on_click=lambda k: self.on_action_add(member['id'], k)
                    ) for m in row_moves
                ], spacing=10))
            
            command_library = ft.Column(rows, spacing=10)

        # 3. 布局组装
        return ft.Container(
            content=ft.Row([
                # 左侧：成员选择
                ft.Row([
                    TacticalMemberSlot(
                        i, self.team_data[i],
                        is_selected=(i == active_index),
                        on_click=set_active_index
                    ) for i in range(4)
                ], spacing=10),
                
                ft.VerticalDivider(width=1, color=ft.Colors.WHITE_10),
                
                # 右侧：指令区域
                ft.Container(
                    content=command_library,
                    padding=ft.padding.only(left=10)
                )
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=15,
            bgcolor=ft.Colors.BLACK_12,
            border_radius=12
        )
