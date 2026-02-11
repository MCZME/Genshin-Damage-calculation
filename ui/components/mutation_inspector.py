import flet as ft
from ui.state import AppState
from core.logger import get_ui_logger
from core.batch.models import SimulationNode, ModifierRule
from ui.theme import GenshinTheme

class MutationInspector(ft.Container):
    """
    节点变异检视器 (V3.3 - 区间生成版)
    """
    def __init__(self, state: AppState):
        super().__init__(
            width=340, 
            bgcolor="rgba(80, 70, 100, 0.6)", 
            blur=ft.Blur(20, 20),
            border_radius=20, 
            border=ft.border.all(2, "rgba(255, 255, 255, 0.15)"),
            padding=20, 
            right=20, 
            top=100, 
            bottom=40,
            animate_offset=ft.Animation(400, ft.AnimationCurve.DECELERATE),
            offset=ft.Offset(1.2, 0)
        )
        self.state = state
        self._build_ui()

    def _build_ui(self):
        # 顶部：名称编辑 + 同步按钮
        self.name_edit = ft.TextField(
            label="节点名称", dense=True, text_size=14,
            bgcolor="transparent", border_color="rgba(255,255,255,0.1)",
            on_change=self._handle_name_change, expand=True
        )
        self.sync_btn = ft.IconButton(
            icon=ft.Icons.SYNC_ALT_ROUNDED, icon_color=GenshinTheme.PRIMARY,
            tooltip="同步到工作台", on_click=self._handle_sync_click
        )
        self.header_row = ft.Row([self.name_edit, self.sync_btn], spacing=10)

        # 规则区域
        self.rules_area = ft.Column(spacing=15, scroll=ft.ScrollMode.AUTO, expand=True)
        
        # 底部：删除按钮
        self.delete_btn = ft.ElevatedButton(
            content=ft.Text("删除此节点", weight=ft.FontWeight.BOLD),
            icon=ft.Icons.DELETE_OUTLINE,
            bgcolor=ft.Colors.RED_900, color=ft.Colors.WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
            width=300,
            on_click=lambda _: self.state.remove_node(self.state.selected_node.id)
        )

        self.content = ft.Column([
            ft.Text("节点配置 (INSPECTOR)", size=10, weight="bold", opacity=0.4, color=GenshinTheme.ON_SURFACE),
            self.header_row,
            ft.Divider(height=1, color="rgba(255,255,255,0.05)"),
            self.rules_area,
            ft.Divider(height=1, color="rgba(255,255,255,0.05)"),
            self.delete_btn
        ], spacing=15)

    def refresh(self):
        node = self.state.selected_node
        if not node:
            self.offset = ft.Offset(1.2, 0); self.update()
            return

        self.offset = ft.Offset(0, 0)
        self.name_edit.value = node.name or ""
        self.name_edit.disabled = node.is_managed
        
        # 受控节点逻辑：禁止同步、删除、改名
        self.delete_btn.visible = (node.id != "root" and not node.is_managed)
        self.sync_btn.visible = (node.id != "root") # 受控节点允许同步到工作台查看

        self.rules_area.controls.clear()
        
        if node.is_managed:
            self.rules_area.controls.append(
                ft.Container(
                    content=ft.Text("该节点由区间生成器管理，规则固定，但可在其后添加新分支", size=11, color=ft.Colors.AMBER_200, italic=True),
                    padding=10, bgcolor="rgba(255, 193, 7, 0.05)", border_radius=8
                )
            )

        if node.rule:
            self.rules_area.controls.append(self._build_rule_tile(node.rule))
            btn_text = "更改变异规则"
        else:
            self.rules_area.controls.append(
                ft.Container(
                    content=ft.Text("基准配置 (无变异)", size=12, italic=True, opacity=0.3, color=GenshinTheme.ON_SURFACE),
                    padding=ft.Padding(0, 10, 0, 10), alignment=ft.alignment.Alignment.CENTER
                )
            )
            btn_text = "添加变异规则"

        # 仅非受控节点、非根节点、且【没有子节点】的节点允许添加规则
        # 理由：父节点的规则会级联影响所有子节点，但在目前的 UI 设计中，
        # 我们鼓励将具体的变异放在叶子节点或独立的层级节点上。
        has_children = len(node.children) > 0
        if node.id != "root" and not node.is_managed and not has_children:
            self.rules_area.controls.append(
                ft.TextButton(
                    content=ft.Text(btn_text, color=GenshinTheme.PRIMARY),
                    icon=ft.Icons.ADD_CIRCLE_OUTLINE if not node.rule else ft.Icons.EDIT_NOTE_ROUNDED,
                    on_click=self._show_add_rule_dialog
                )
            )
        elif has_children and not node.id == "root":
             self.rules_area.controls.append(
                ft.Container(
                    content=ft.Text("该节点作为分支起点，不可直接添加规则", size=11, color=ft.Colors.AMBER_200, italic=True),
                    padding=10, bgcolor="rgba(255, 193, 7, 0.05)", border_radius=8
                )
            )
        
        try: self.update()
        except: pass

    def _build_rule_tile(self, rule: ModifierRule):
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(rule.label or "变异项", weight="bold", size=13, color=GenshinTheme.ON_SURFACE),
                    ft.IconButton(ft.Icons.CLOSE, icon_size=14, on_click=lambda _: self._delete_rule(), visible=not self.state.selected_node.is_managed)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Text(" > ".join(map(str, rule.target_path)), size=10, opacity=0.5, color=GenshinTheme.ON_SURFACE),
                ft.Row([
                    ft.Container(
                        content=ft.Text("VALUE", size=9, weight="bold", color=GenshinTheme.ON_PRIMARY),
                        bgcolor=GenshinTheme.PRIMARY, padding=ft.Padding(6, 2, 6, 2), border_radius=4
                    ),
                    ft.Text(str(rule.value), size=11, weight="bold", color=GenshinTheme.ON_SURFACE, expand=True)
                ], spacing=10)
            ], spacing=8),
            padding=15, bgcolor="rgba(255,255,255,0.03)", border=ft.border.all(1, "rgba(255,255,255,0.1)"), border_radius=12
        )

    def _show_add_rule_dialog(self, e):
        char_options = []
        current_config = self.state.get_selected_node_config()
        if current_config:
            team = current_config.get("context_config", {}).get("team", [])
            for i, member in enumerate(team):
                if member: char_options.append(ft.dropdown.Option(key=str(i), text=f"#{i+1} {member['character']['name']}"))

        targets = {"角色属性": ["等级", "命座", "普攻等级", "战技等级", "爆发等级"], "武器属性": ["等级", "精炼"], "环境": ["天气", "场地状态"]}
        
        char_drop = ft.Dropdown(label="目标位置", options=char_options, value="0" if char_options else None, visible=False)
        category_drop = ft.Dropdown(label="分类", options=[ft.dropdown.Option(k) for k in targets.keys()], on_select=lambda e: self._handle_category_change(e, property_drop, char_drop, targets))
        property_drop = ft.Dropdown(label="属性", disabled=True)
        
        # 模式切换
        is_range = ft.Switch(label="开启区间扫描模式", value=False, on_change=lambda _: self._toggle_mode(is_range, value_input, range_fields))
        value_input = ft.TextField(label="具体数值", hint_text="输入替换值")
        
        # 区间专用字段
        start_f = ft.TextField(label="起始", width=100); end_f = ft.TextField(label="终止", width=100); step_f = ft.TextField(label="步长", width=100)
        range_fields = ft.Row([start_f, end_f, step_f], visible=False, spacing=10)

        def on_confirm(_):
            if not category_drop.value or not property_drop.value: return
            idx = int(char_drop.value) if char_drop.visible else 0
            path = self._map_to_path(category_drop.value, property_drop.value, idx)
            
            if is_range.value:
                # 区间模式：直接修改当前选中的节点
                try:
                    self.state.apply_range_to_node(
                        self.state.selected_node, path, 
                        float(start_f.value), float(end_f.value), float(step_f.value),
                        property_drop.value
                    )
                    self.page.pop_dialog()
                except Exception as ex: 
                    get_ui_logger().log_error(f"Range Error: {ex}")
            else:
                # 普通模式：更新当前节点 rule
                val = value_input.value
                if val.replace('.','').isdigit(): val = float(val)
                rule = ModifierRule(target_path=path, value=val, label=f"[{idx+1}] {property_drop.value}")
                self.state.update_node(self.state.selected_node.id, rule=rule)
                self.page.pop_dialog()

        self.page.show_dialog(ft.AlertDialog(
            title=ft.Text("配置变异规则"),
            content=ft.Column([category_drop, char_drop, property_drop, ft.Divider(height=10), is_range, value_input, range_fields], spacing=10, height=450, width=400, scroll=ft.ScrollMode.AUTO),
            actions=[
                ft.TextButton(content=ft.Text("取消"), on_click=lambda _: self.page.pop_dialog()),
                ft.ElevatedButton(content=ft.Text("确认添加"), bgcolor=GenshinTheme.PRIMARY, color=GenshinTheme.ON_PRIMARY, on_click=on_confirm)
            ]
        ))

    def _toggle_mode(self, sw, val_in, range_row):
        val_in.visible = not sw.value
        range_row.visible = sw.value
        val_in.update(); range_row.update()

    def _handle_category_change(self, e, property_drop, char_drop, targets):
        cat = e.control.value
        property_drop.options = [ft.dropdown.Option(p) for p in targets[cat]]; property_drop.disabled = False
        char_drop.visible = (cat in ["角色属性", "武器属性"])
        property_drop.update(); char_drop.update()

    def _map_to_path(self, category, prop, idx):
        m = {"角色属性": ["level", "constellation"], "武器属性": ["level", "refinement"]}
        field = prop # 默认
        if category == "角色属性": field = {"等级": "level", "命座": "constellation"}.get(prop, prop)
        elif category == "武器属性": field = {"等级": "level", "精炼": "refinement"}.get(prop, prop)
        
        path = ["context_config"]
        if category in ["角色属性", "武器属性"]:
            path.extend(["team", idx, "character" if category=="角色属性" else "weapon", field])
        else: path.extend(["environment", prop])
        return path

    def _handle_name_change(self, e):
        if self.state.selected_node: self.state.update_node(self.state.selected_node.id, name=e.control.value)

    def _handle_sync_click(self, e):
        config = self.state.get_selected_node_config()
        if config: self.state.branch_to_main.put({"type": "APPLY_CONFIG", "config": config, "action_sequence_raw": config.get("action_sequence_raw", [])})

    def _delete_rule(self):
        if self.state.selected_node: self.state.update_node(self.state.selected_node.id, rule=None)
