import flet as ft
from ui.state import AppState
from core.batch.models import SimulationNode, ModifierRule, ModifierMode

class MutationInspector(ft.Container):
    """
    节点变异检视器。
    用于编辑 SimulationNode 的 ModifierRule。
    """
    def __init__(self, state: AppState):
        super().__init__(expand=True)
        self.state = state
        self._build_ui()

    def _build_ui(self):
        self.node_info = ft.Column([
            ft.Text("请选择宇宙节点", italic=True, opacity=0.4)
        ])
        
        self.rules_list = ft.Column(spacing=10)
        
        self.content = ft.Column([
            ft.Text("NODE PROPERTIES", size=10, weight="bold", opacity=0.4),
            self.node_info,
            ft.Divider(height=30, color="#222222"),
            ft.Text("MODIFIER RULES", size=10, weight="bold", opacity=0.4),
            self.rules_list,
            ft.ElevatedButton(
                "添加修改规则", 
                icon=ft.Icons.PLAYLIST_ADD, 
                on_click=self._add_rule_clicked,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                width=310
            )
        ], scroll=ft.ScrollMode.AUTO)

    def refresh(self):
        """同步 state.selected_node 状态并刷新 UI"""
        self.rules_list.controls.clear()
        self.node_info.controls.clear()
        
        node = self.state.selected_node
        if not node:
            self.node_info.controls.append(ft.Text("请选择宇宙节点", italic=True, opacity=0.4))
        else:
            # 基础信息展示
            self.node_info.controls.extend([
                ft.Text(node.name or ("基准宇宙" if node.id == "root" else "分支变体"), weight="bold", size=16),
                ft.Text(f"ID: {node.id}", size=10, color=ft.Colors.WHITE38),
            ])
            
            # 规则显示
            if node.rule:
                self.rules_list.controls.append(self._build_rule_tile(node.rule))
            else:
                self.rules_list.controls.append(
                    ft.Container(
                        content=ft.Text("该节点暂无修改规则 (继承父级状态)", size=12, italic=True, opacity=0.3),
                        padding=ft.Padding(15, 10, 15, 10),
                        bgcolor="#1a1a1a",
                        border_radius=8
                    )
                )
        
        try:
            self.update()
        except Exception:
            pass

    def _build_rule_tile(self, rule: ModifierRule):
        """构建规则卡片"""
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Row([
                        ft.Icon(ft.Icons.RULE, size=16, color=ft.Colors.BLUE_700),
                        ft.Text(rule.label or "未命名规则", weight="bold", size=13),
                    ], spacing=10),
                    ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_size=16, on_click=lambda _: self._delete_rule())
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Text(f"Path: {' > '.join(map(str, rule.target_path))}", size=10, color=ft.Colors.WHITE38),
                ft.Text(f"Mode: {rule.mode.value} | Values: {rule.values}", size=11, weight="bold"),
            ], spacing=5),
            padding=15,
            bgcolor="#1a1a1a",
            border=ft.Border(left=ft.BorderSide(3, ft.Colors.BLUE_700)),
            border_radius=8
        )

    def _add_rule_clicked(self, e):
        """点击添加规则的处理逻辑 (临时 Demo 版)"""
        if not self.state.selected_node: return
        
        # 模拟：创建一个修改角色等级的规则
        rule = ModifierRule(
            target_path=["team", 0, "character", "level"],
            mode=ModifierMode.REPLACE,
            values=[90],
            label="覆盖角色等级"
        )
        self.state.selected_node.rule = rule
        self.refresh()

    def _delete_rule(self):
        """删除当前节点的规则"""
        if self.state.selected_node:
            self.state.selected_node.rule = None
            self.refresh()
