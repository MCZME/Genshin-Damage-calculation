import flet as ft
from ui.states.app_state import AppState
from core.logger import get_ui_logger
from core.batch.models import ModifierRule
from ui.theme import GenshinTheme

@ft.component
def MutationInspector(state: AppState):
    """
    声明式节点变异检视器 (V4.5)。
    """
    node = state.selected_node
    is_visible = node is not None
    
    # 模拟刷新逻辑：根据 node 状态计算布局
    if not is_visible:
        return ft.Container(
            width=340, bgcolor="rgba(80, 70, 100, 0.6)", blur=ft.Blur(20, 20),
            border_radius=20, border=ft.border.all(2, "rgba(255, 255, 255, 0.15)"),
            padding=20, right=20, top=100, bottom=40,
            animate_offset=ft.Animation(400, ft.AnimationCurve.DECELERATE),
            offset=ft.Offset(1.2, 0)
        )

    # 1. 规则渲染工厂
    def build_rule_tile(rule: ModifierRule):
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(rule.label or "变异项", weight=ft.FontWeight.BOLD, size=13, color=GenshinTheme.ON_SURFACE),
                    ft.IconButton(
                        ft.Icons.CLOSE, icon_size=14,
                        on_click=lambda _: state.update_node(node.id, rule=None),
                        visible=not node.is_managed
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Text(" > ".join(map(str, rule.target_path)), size=10, opacity=0.5, color=GenshinTheme.ON_SURFACE),
                ft.Row([
                    ft.Container(
                        content=ft.Text("VALUE", size=9, weight=ft.FontWeight.BOLD, color=GenshinTheme.ON_PRIMARY),
                        bgcolor=GenshinTheme.PRIMARY, padding=ft.Padding(6, 2, 6, 2), border_radius=4,
                    ),
                    ft.Text(str(rule.value), size=11, weight=ft.FontWeight.BOLD, color=GenshinTheme.ON_SURFACE, expand=True),
                ], spacing=10),
            ], spacing=8),
            padding=15, bgcolor="rgba(255,255,255,0.03)", border=ft.border.all(1, "rgba(255,255,255,0.1)"), border_radius=12,
        )

    # 2. 规则区域构建
    rules_controls = []
    if node.is_managed:
        rules_controls.append(
            ft.Container(
                content=ft.Text("该节点由区间生成器管理，规则固定，但可在其后添加新分支", size=11, color=ft.Colors.AMBER_200, italic=True),
                padding=10, bgcolor="rgba(255, 193, 7, 0.05)", border_radius=8,
            )
        )
    
    if node.rule:
        rules_controls.append(build_rule_tile(node.rule))
        btn_text = "更改变异规则"
    else:
        rules_controls.append(
            ft.Container(
                content=ft.Text("基准配置 (无变异)", size=12, italic=True, opacity=0.3, color=GenshinTheme.ON_SURFACE),
                padding=ft.Padding(0, 10, 0, 10), alignment=ft.Alignment.CENTER,
            )
        )
        btn_text = "添加变异规则"

    # 添加规则按钮
    has_children = len(node.children) > 0
    if node.id != "root" and not node.is_managed and not has_children:
        rules_controls.append(
            ft.TextButton(
                content=ft.Text(btn_text, color=GenshinTheme.PRIMARY),
                icon=ft.Icons.ADD_CIRCLE_OUTLINE if not node.rule else ft.Icons.EDIT_NOTE_ROUNDED,
                on_click=lambda _: show_add_rule_dialog(state)
            )
        )
    elif has_children and node.id != "root":
        rules_controls.append(
            ft.Container(
                content=ft.Text("该节点作为分支起点，不可直接添加规则", size=11, color=ft.Colors.AMBER_200, italic=True),
                padding=10, bgcolor="rgba(255, 193, 7, 0.05)", border_radius=8,
            )
        )

    # 3. 头部与底部
    name_edit = ft.TextField(
        label="节点名称", value=node.name or "", disabled=node.is_managed,
        dense=True, text_size=14, bgcolor="transparent", border_color="rgba(255,255,255,0.1)",
        on_change=lambda e: state.update_node(node.id, name=e.control.value),
        expand=True,
    )

    sync_btn = ft.IconButton(
        icon=ft.Icons.SYNC_ALT_ROUNDED, icon_color=GenshinTheme.PRIMARY, tooltip="同步到工作台",
        visible=node.id != "root",
        on_click=lambda _: state.branch_to_main.put({
            "type": "APPLY_CONFIG", "config": state.get_selected_node_config(),
            "action_sequence_raw": state.get_selected_node_config().get("action_sequence_raw", []),
        })
    )

    delete_btn = ft.ElevatedButton(
        content=ft.Text("删除此节点", weight=ft.FontWeight.BOLD),
        icon=ft.Icons.DELETE_OUTLINE, bgcolor=ft.Colors.RED_900, color=ft.Colors.WHITE,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
        width=300, visible=node.id != "root" and not node.is_managed,
        on_click=lambda _: state.remove_node(node.id),
    )

    return ft.Container(
        content=ft.Column([
            ft.Text("节点配置 (INSPECTOR)", size=10, weight=ft.FontWeight.BOLD, opacity=0.4, color=GenshinTheme.ON_SURFACE),
            ft.Row([name_edit, sync_btn], spacing=10),
            ft.Divider(height=1, color="rgba(255,255,255,0.05)"),
            ft.Column(rules_controls, spacing=15, scroll=ft.ScrollMode.AUTO, expand=True),
            ft.Divider(height=1, color="rgba(255,255,255,0.05)"),
            delete_btn,
        ], spacing=15),
        width=340, bgcolor="rgba(80, 70, 100, 0.6)", blur=ft.Blur(20, 20),
        border_radius=20, border=ft.border.all(2, "rgba(255, 255, 255, 0.15)"),
        padding=20, right=20, top=100, bottom=40,
        animate_offset=ft.Animation(400, ft.AnimationCurve.DECELERATE),
        offset=ft.Offset(0, 0)
    )

def show_add_rule_dialog(state: AppState):
    """
    添加规则对话框逻辑 (外部辅助函数)。
    """
    page = state.page # 假设 AppState 持有 page 引用
    if not page: return

    char_options = []
    current_config = state.get_selected_node_config()
    if current_config:
        team = current_config.get("context_config", {}).get("team", [])
        for i, member in enumerate(team):
            if member:
                char_options.append(ft.dropdown.Option(key=str(i), text=f"#{i + 1} {member['character']['name']}"))

    targets = {
        "角色属性": ["等级", "命座", "普攻等级", "战技等级", "爆发等级"],
        "武器属性": ["等级", "精炼"],
        "环境": ["天气", "场地状态"],
    }

    char_drop = ft.Dropdown(label="目标位置", options=char_options, value="0" if char_options else None, visible=False)
    property_drop = ft.Dropdown(label="属性", disabled=True)
    category_drop = ft.Dropdown(
        label="分类", options=[ft.dropdown.Option(k) for k in targets.keys()],
        on_select=lambda e: (
            setattr(property_drop, 'options', [ft.dropdown.Option(p) for p in targets[e.control.value]]),
            setattr(property_drop, 'disabled', False),
            setattr(char_drop, 'visible', e.control.value in ["角色属性", "武器属性"]),
            property_drop.update(), char_drop.update()
        )
    )

    is_range = ft.Switch(label="开启区间扫描模式", value=False)
    value_input = ft.TextField(label="具体数值", hint_text="输入替换值")
    start_f = ft.TextField(label="起始", width=100); end_f = ft.TextField(label="终止", width=100); step_f = ft.TextField(label="步长", width=100)
    range_fields = ft.Row([start_f, end_f, step_f], visible=False, spacing=10)
    
    is_range.on_change = lambda _: (
        setattr(value_input, 'visible', not is_range.value),
        setattr(range_fields, 'visible', is_range.value),
        value_input.update(), range_fields.update()
    )

    def on_confirm(_):
        if not category_drop.value or not property_drop.value: return
        idx = int(char_drop.value) if char_drop.visible else 0
        path = _map_to_path(category_drop.value, property_drop.value, idx)
        if is_range.value:
            state.apply_range_to_node(state.selected_node, path, float(start_f.value), float(end_f.value), float(step_f.value), property_drop.value)
        else:
            val = value_input.value
            if val.replace(".", "").isdigit(): val = float(val)
            rule = ModifierRule(target_path=path, value=val, label=f"[{idx + 1}] {property_drop.value}")
            state.update_node(state.selected_node.id, rule=rule)
        page.pop_dialog()

    page.show_dialog(
        ft.AlertDialog(
            title=ft.Text("配置变异规则"),
            content=ft.Column([category_drop, char_drop, property_drop, ft.Divider(height=10), is_range, value_input, range_fields], spacing=10, height=450, width=400, scroll=ft.ScrollMode.AUTO),
            actions=[
                ft.TextButton("取消", on_click=lambda _: page.pop_dialog()),
                ft.ElevatedButton("确认添加", bgcolor=GenshinTheme.PRIMARY, color=GenshinTheme.ON_PRIMARY, on_click=on_confirm),
            ],
        )
    )

def _map_to_path(category, prop, idx):
    field = prop
    if category == "角色属性": field = {"等级": "level", "命座": "constellation"}.get(prop, prop)
    elif category == "武器属性": field = {"等级": "level", "精炼": "refinement"}.get(prop, prop)
    path = ["context_config"]
    if category in ["角色属性", "武器属性"]: path.extend(["team", idx, "character" if category == "角色属性" else "weapon", field])
    else: path.extend(["environment", prop])
    return path
