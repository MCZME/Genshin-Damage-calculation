from typing import List

import flet as ft
from ui.theme import GenshinTheme
from ui.view_models.library_vm import AssetOption

@ft.component
def AssetCard(
    opt: AssetOption,
    is_selected: bool = False,
    on_click = None
):
    """单独资产卡片 (MVVM V5.0)"""
    rarity_gradient = ft.LinearGradient(
        begin=ft.Alignment(0, -1), end=ft.Alignment(0, 1),
        colors=["#E9B053", "#D3962F"] if opt.rarity == 5 else ["#AF8FE6", "#8A69C4"]
    )
    elem_color = GenshinTheme.get_element_color(opt.element)
    
    return ft.Container(
        content=ft.Stack([
            ft.Container(gradient=rarity_gradient, border_radius=8, expand=True),
            ft.Container(
                content=ft.Row(
                    [ft.Icon(ft.Icons.STAR, size=10, color=ft.Colors.WHITE_70) for _ in range(opt.rarity)],
                    spacing=0, alignment=ft.MainAxisAlignment.START,
                ),
                padding=ft.Padding(5, 2, 0, 0),
            ),
            ft.Container(
                content=ft.Text(opt.name, size=9, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER, overflow=ft.TextOverflow.ELLIPSIS),
                alignment=ft.Alignment.BOTTOM_CENTER, padding=ft.Padding(2, 0, 2, 4),
                gradient=ft.LinearGradient(begin=ft.Alignment.TOP_CENTER, end=ft.Alignment.BOTTOM_CENTER, colors=[ft.Colors.TRANSPARENT, ft.Colors.BLACK_45]),
                expand=True
            )
        ]),
        width=80, height=80, border_radius=8,
        border=ft.Border.all(2, elem_color if is_selected else ft.Colors.TRANSPARENT),
        shadow=GenshinTheme.get_element_glow(opt.element, intensity=0.8) if is_selected else None,
        scale=1.05 if is_selected else 1.0,
        animate_scale=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
        opacity=0.4 if not opt.is_implemented else 1.0,
        on_click=lambda _: on_click(opt.id) if (on_click and opt.is_implemented) else None,
    )

@ft.component
def FilterChip(label: str, is_active: bool, category: str, on_click: callable):
    chip_color = ft.Colors.WHITE
    if category == "element" and label != "全部":
        chip_color = GenshinTheme.get_element_color(label)
    
    return ft.Container(
        content=ft.Text(label, size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE if is_active else ft.Colors.WHITE_54),
        padding=ft.Padding(12, 6, 12, 6), border_radius=15,
        bgcolor=ft.Colors.with_opacity(0.2, chip_color) if is_active else ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
        border=ft.Border.all(1, chip_color if is_active else ft.Colors.TRANSPARENT),
        on_click=lambda _: on_click(category, label),
        animate=ft.Animation(200, ft.AnimationCurve.DECELERATE)
    )

@ft.component
def AssetGrid(
    items: List[AssetOption], # 这里的 items 已经是由 ViewModel 过滤后的结果
    on_select = None, 
    allow_filter_type: bool = True, 
    allow_filter_element: bool = True
):
    """
    高性能响应式资产网格 (MVVM V5.0)。
    接收预过滤的 AssetOption 列表。
    """
    # 局部 UI 状态 (仅用于点击高亮)
    selected_id, set_selected_id = ft.use_state(None)
    
    # 过滤器状态 (为了保持组件独立性，暂时保留局部过滤器，未来可移入 LibraryVM)
    sel_element, set_sel_element = ft.use_state("全部")
    sel_type, set_sel_type = ft.use_state("全部类型")
    search_query, set_search_query = ft.use_state("")
    show_only_impl, set_show_only_impl = ft.use_state(True)

    elements = ["全部", "火", "水", "风", "雷", "草", "冰", "岩", "物理"]
    types = ["全部类型", "单手剑", "双手剑", "长柄武器", "法器", "弓"]

    def handle_filter_click(category, label):
        if category == "element": set_sel_element(label)
        else: set_sel_type(label)

    def handle_item_click(item_id):
        set_selected_id(item_id)
        if on_select: on_select(item_id)

    # 1. 过滤逻辑 (组件级局部过滤)
    visible_options = []
    for opt in items:
        if show_only_impl and not opt.is_implemented: continue
        if allow_filter_element and sel_element != "全部" and opt.element != sel_element: continue
        if allow_filter_type and sel_type != "全部类型" and opt.type != sel_type: continue
        if search_query and search_query not in opt.name.lower(): continue
        visible_options.append(opt)

    # 2. 构建组件
    search_field = ft.TextField(
        hint_text="搜索名称...", prefix_icon=ft.Icons.SEARCH, height=35, text_size=12,
        content_padding=ft.Padding(10, 0, 10, 0), bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
        on_change=lambda e: set_search_query(e.control.value.lower())
    )

    header_rows = []
    if allow_filter_element:
        header_rows.append(ft.Row([
            ft.Row([FilterChip(el, sel_element == el, "element", handle_filter_click) for el in elements], wrap=True, spacing=5),
            ft.Row([
                ft.Text("仅已实装", size=10, color=ft.Colors.WHITE_70),
                ft.Switch(value=show_only_impl, scale=0.6, on_change=lambda e: set_show_only_impl(e.control.value))
            ], spacing=2)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))

    if allow_filter_type:
        header_rows.append(ft.Row([
            ft.Row([FilterChip(t, sel_type == t, "type", handle_filter_click) for t in types], wrap=True, spacing=5),
            ft.Container(content=search_field, width=200)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))

    # 3. 渲染网格
    if not visible_options:
        grid_display = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.SEARCH_OFF, size=48, color=ft.Colors.WHITE_24),
                ft.Text("未找到匹配资产", color=ft.Colors.WHITE_38)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.Alignment.CENTER, expand=True
        )
    else:
        grid_display = ft.GridView(
            controls=[
                AssetCard(opt, is_selected=(opt.id == selected_id), on_click=handle_item_click)
                for opt in visible_options
            ],
            expand=True, max_extent=100, child_aspect_ratio=1.0, spacing=10, run_spacing=10,
        )

    return ft.Container(
        content=ft.Column([
            ft.Column(header_rows, spacing=15),
            ft.Divider(height=1, color=ft.Colors.WHITE_10),
            grid_display
        ], expand=True),
        padding=10, expand=True
    )
