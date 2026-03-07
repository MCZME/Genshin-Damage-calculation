import flet as ft
from ui.theme import GenshinTheme
from ui.components.scene.stat_input import StatInputField
from ui.view_models.strategic.artifact_vm import ArtifactPieceViewModel

@ft.component
def SubStatRow(
    index: int,
    vm: ArtifactPieceViewModel,
    element: str,
    sub_options: list
):
    """
    单个副词条行组件，包含自动后缀判定逻辑与安全检查。
    """
    is_hovered, set_hovered = ft.use_state(False)
    elem_color = GenshinTheme.get_element_color(element)
    
    # 安全检查：防止在删除过程中索引越界导致的崩溃
    if index >= len(vm.sub_stats):
        return ft.Container()

    current_key = vm.sub_stats[index][0]
    current_val = vm.sub_stats[index][1]
    
    # 自动判定是否需要百分比后缀
    has_percent = "%" in current_key or "效率" in current_key or "加成" in current_key

    return ft.GestureDetector(
        on_enter=lambda _: set_hovered(True),
        on_exit=lambda _: set_hovered(False),
        content=ft.Container(
            content=ft.Stack([
                StatInputField(
                    label=current_key, 
                    value=current_val, 
                    suffix="%" if has_percent else "",
                    element=element, 
                    width=185,
                    label_options=sub_options,
                    on_change=lambda v: vm.update_sub_stat_value(index, v),
                    on_label_change=lambda l: vm.update_sub_stat_key(index, l)
                ),
                # 悬浮显示的微型删除按钮
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        icon_size=8,
                        icon_color=ft.Colors.RED_200,
                        padding=0,
                        width=14, height=14,
                        on_click=lambda _: vm.remove_sub_stat(index),
                        hover_color=ft.Colors.RED_900,
                    ),
                    alignment=ft.Alignment(1.0, -1.0),
                    padding=ft.Padding(0, 2, 2, 0),
                    opacity=1.0 if is_hovered else 0,
                    animate_opacity=200,
                )
            ]),
            bgcolor="transparent",
        )
    )

@ft.component
def ArtifactSlot(
    vm: ArtifactPieceViewModel,
    set_options: list, # 由外部 (LibraryVM) 传入选项列表
    element: str = "Neutral",
    on_change = None
):
    """
    声明式圣遗物配置插槽 (MVVM V5.0)。
    直接绑定到 ArtifactPieceViewModel。
    """
    elem_color = GenshinTheme.get_element_color(element)
    
    # 部位名映射
    slot_cn = {
        "Flower": "生之花", "Plume": "死之羽", "Sands": "时之沙", 
        "Goblet": "空之杯", "Circlet": "理之冠"
    }
    
    main_stat_options = {
        "Flower": ["生命值"],
        "Plume": ["攻击力"],
        "Sands": ["攻击力%", "生命值%", "防御力%", "元素精通", "元素充能效率%"],
        "Goblet": ["攻击力%", "生命值%", "防御力%", "元素精通", "火元素伤害加成%", "水元素伤害加成%", "风元素伤害加成%", "雷元素伤害加成%", "草元素伤害加成%", "冰元素伤害加成%", "岩元素伤害加成%", "物理伤害加成%"],
        "Circlet": ["攻击力%", "生命值%", "防御力%", "元素精通", "暴击率%", "暴击伤害%", "治疗加成%"]
    }

    # 1. 顶部：部位名称
    header = ft.Row([
        ft.Text(slot_cn.get(vm.slot_name, vm.slot_name), size=13, color=elem_color, weight=ft.FontWeight.BOLD),
    ], alignment=ft.MainAxisAlignment.START)

    # 2. 圣遗物套装选择
    name_dropdown = ft.Dropdown(
        value=vm.set_name,
        options=[ft.dropdown.Option(s) for s in set_options],
        hint_text="选择圣遗物套装...",
        dense=True,
        text_size=12,
        border=ft.InputBorder.UNDERLINE,
        border_color=ft.Colors.WHITE_10,
        focused_border_color=elem_color,
        content_padding=ft.Padding(0, 5, 0, 5),
        on_select=lambda e: vm.set_set_name(e.control.value)
    )

    # 3. 主词条配置
    current_main = vm.main_stat or main_stat_options.get(vm.slot_name, [""])[0]
    has_main_percent = "%" in current_main or "效率" in current_main or "加成" in current_main

    main_stat_drop = ft.Dropdown(
        value=current_main,
        options=[ft.dropdown.Option(s) for s in main_stat_options.get(vm.slot_name, [])],
        dense=True, text_size=12, border_radius=6, height=34, expand=2,
        bgcolor=ft.Colors.BLACK_26,
        border=ft.Border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
        on_select=lambda e: vm.set_main_stat(e.control.value)
    )
    
    main_val_input = ft.TextField(
        value=vm.main_val,
        suffix=ft.Text("%", size=10, color=GenshinTheme.TEXT_SECONDARY) if has_main_percent else None,
        dense=True, text_size=12, text_align=ft.TextAlign.RIGHT, border_radius=6, height=34, expand=1,
        bgcolor=ft.Colors.BLACK_26,
        border=ft.Border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
        on_change=lambda e: vm.set_main_val(e.control.value)
    )

    # 4. 副词条列表
    sub_options = ["生命值", "生命值%", "攻击力", "攻击力%", "防御力", "防御力%", "元素精通", "元素充能效率%", "暴击率%", "暴击伤害%"]
    
    substat_items = [
        SubStatRow(i, vm, element, sub_options) 
        for i in range(len(vm.sub_stats))
    ]

    # 5. 添加按钮逻辑
    add_sub_btn = ft.TextButton(
        "添加副词条", 
        icon=ft.Icons.ADD_CIRCLE_OUTLINE, 
        icon_color=elem_color,
        on_click=lambda _: vm.add_sub_stat(),
        visible=len(vm.sub_stats) < 4
    )

    # 6. 组装内容
    return ft.Container(
        content=ft.Column([
            header,
            name_dropdown,
            ft.Divider(height=2, color="transparent"), 
            ft.Text("主词条属性", size=10, color=GenshinTheme.TEXT_SECONDARY, weight=ft.FontWeight.W_600),
            ft.Row([main_stat_drop, main_val_input], spacing=5),
            ft.Divider(height=1, color=ft.Colors.WHITE_10),
            ft.Text("副词条属性", size=10, color=GenshinTheme.TEXT_SECONDARY, weight=ft.FontWeight.W_600),
            ft.Column(substat_items, spacing=5),
            ft.Row([add_sub_btn], alignment=ft.MainAxisAlignment.CENTER)
        ], spacing=5),
        padding=ft.Padding(15, 15, 15, 15),
        bgcolor=GenshinTheme.SURFACE_VARIANT,
        border_radius=10,
        border=ft.Border.all(1, ft.Colors.with_opacity(0.1, GenshinTheme.ON_SURFACE)),
        width=215
    )
