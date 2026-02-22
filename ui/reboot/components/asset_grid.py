import flet as ft
from typing import Any
from ui.theme import GenshinTheme

class AssetCard(ft.Container):
    """
    单个资产卡片 (角色/武器) - 适配 Flet 0.21+
    """
    def __init__(
        self,
        item_id: Any,
        name: str,
        rarity: int = 5,
        element: str = "Neutral",
        is_selected: bool = False,
        is_implemented: bool = True,
        on_click=None
    ):
        super().__init__()
        self.key = str(item_id) # 强制转为字符串 Key
        self.item_id = item_id
        self.item_name = name
        self.rarity = rarity
        self.element = element
        self.is_selected = is_selected
        self.on_click_callback = on_click
        
        # 稀有度背景渐变
        rarity_gradient = ft.LinearGradient(
            begin=ft.Alignment(0, -1),
            end=ft.Alignment(0, 1),
            colors=["#E9B053", "#D3962F"] if self.rarity == 5 else ["#AF8FE6", "#8A69C4"]
        )
        elem_color = GenshinTheme.get_element_color(self.element)
        
        # 容器属性
        self.content = ft.Stack([
            # 背景渐变
            ft.Container(
                gradient=rarity_gradient,
                border_radius=8,
                expand=True,
            ),
            # 顶部稀有度点缀 (模拟星级感)
            ft.Container(
                content=ft.Row(
                    [ft.Icon(ft.Icons.STAR, size=10, color=ft.Colors.WHITE_70) for _ in range(self.rarity)],
                    spacing=0,
                    alignment=ft.MainAxisAlignment.START,
                ),
                padding=ft.Padding(5, 2, 0, 0),
            ),
            # 底部名字遮罩
            ft.Container(
                content=ft.Text(
                    self.item_name, 
                    size=9, 
                    color=ft.Colors.WHITE, 
                    weight=ft.FontWeight.BOLD, 
                    text_align=ft.TextAlign.CENTER,
                    overflow=ft.TextOverflow.ELLIPSIS
                ),
                alignment=ft.Alignment.BOTTOM_CENTER,
                padding=ft.Padding(2, 0, 2, 4),
                gradient=ft.LinearGradient(
                    begin=ft.Alignment.TOP_CENTER,
                    end=ft.Alignment.BOTTOM_CENTER,
                    colors=[ft.Colors.TRANSPARENT, ft.Colors.BLACK45]
                ),
                expand=True
            )
        ])
        self.width = 80
        self.height = 80
        self.border_radius = 8
        self.border = ft.Border.all(2, elem_color if self.is_selected else ft.Colors.TRANSPARENT)
        self.shadow = GenshinTheme.get_element_glow(self.element, intensity=0.8) if self.is_selected else None
        
        # 处理未实装视觉：降低不透明度
        if not is_implemented:
            self.opacity = 0.4
            self.mouse_cursor = ft.MouseCursor.FORBIDDEN
            self.on_click = None
        else:
            self.on_click = self._handle_click
            self.mouse_cursor = ft.MouseCursor.CLICK

        self.animate_scale = ft.Animation(200, ft.AnimationCurve.EASE_OUT)
        self.scale = 1.05 if self.is_selected else 1.0

    def set_selected(self, selected: bool):
        """局部更新选中态属性，由父容器统一 update"""
        if self.is_selected == selected:
            return
        self.is_selected = selected
        elem_color = GenshinTheme.get_element_color(self.element)
        self.border = ft.Border.all(2, elem_color if self.is_selected else ft.Colors.TRANSPARENT)
        self.shadow = GenshinTheme.get_element_glow(self.element, intensity=0.8) if self.is_selected else None
        self.scale = 1.05 if self.is_selected else 1.0

    def _handle_click(self, e):
        if self.on_click_callback:
            self.on_click_callback(self.item_id)

class AssetGrid(ft.Container):
    """
    带过滤功能的资产网格，适配 Flet 0.21+
    """
    def __init__(self, items: list, on_select=None, allow_filter_type: bool = True, allow_filter_element: bool = True):
        super().__init__()
        self.items = items # [{id, name, rarity, element, type(optional)}]
        self.on_select = on_select
        self.allow_filter_type = allow_filter_type
        self.allow_filter_element = allow_filter_element
        self.selected_id = None
        
        # 过滤状态
        self.selected_element = "全部"
        self.selected_type = "全部类型"
        self.show_only_implemented = True
        
        self.elements = ["全部", "火", "水", "风", "雷", "草", "冰", "岩", "物理"]
        self.types = ["全部类型", "单手剑", "双手剑", "长柄武器", "法器", "弓"]
        
        # 控件池：预先实例化所有卡片
        self.card_pool: Dict[str, AssetCard] = {}
        self._warm_up_pool()
        
        # 过滤器 Chip 引用池
        self.chips: Dict[str, ft.Container] = {}
        
        # 网格组件
        self.grid = ft.GridView(
            expand=True,
            runs_count=5,
            max_extent=100,
            child_aspect_ratio=1.0,
            spacing=10,
            run_spacing=10,
        )
        
        self._build_container()

    def _warm_up_pool(self):
        """全量预热控件池"""
        for item in self.items:
            card = AssetCard(
                item_id=item['id'],
                name=item['name'],
                rarity=item.get('rarity', 5),
                element=item.get('element', 'Neutral'),
                is_selected=False,
                is_implemented=item.get('is_implemented', True),
                on_click=self._on_item_click
            )
            self.card_pool[item['id']] = card

    def _build_container(self):
        # 构建过滤器栏
        filter_rows = []
        
        # 1. 元素过滤器行 (取决于开关)
        if self.allow_filter_element:
            filter_rows.append(
                ft.Row([
                    ft.Row(
                        [self._build_chip("element", el) for el in self.elements],
                        wrap=True, spacing=5, run_spacing=5, expand=True
                    ),
                    # 显隐开关 (放在第一行末尾)
                    self._build_implemented_switch()
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            )
        else:
            # 如果不显示元素过滤，则把实装开关单独放一行
            filter_rows.append(
                ft.Row([
                    ft.Text("资产过滤器", size=14, weight=ft.FontWeight.BOLD),
                    self._build_implemented_switch()
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            )

        # 2. 类型过滤器行 (取决于开关)
        if self.allow_filter_type:
            filter_rows.append(
                ft.Row(
                    [self._build_chip("type", t) for t in self.types],
                    wrap=True, spacing=5, run_spacing=5
                )
            )

        if filter_rows:
            filter_rows.append(ft.Divider(height=1, color=ft.Colors.WHITE_10))

        self.filter_column = ft.Column(filter_rows, spacing=10)
        
        self.content = ft.Column([
            self.filter_column,
            self.grid
        ], expand=True)
        self.padding = 10
        self._refresh_grid()

    def _build_implemented_switch(self):
        return ft.Container(
            content=ft.Row([
                ft.Text("仅显示已实装", size=11, color=ft.Colors.WHITE70),
                ft.Switch(
                    value=self.show_only_implemented, 
                    scale=0.7,
                    active_color=GenshinTheme.PRIMARY,
                    on_change=self._toggle_implemented_filter
                )
            ], spacing=5),
            padding=ft.Padding(10, 0, 0, 0)
        )

    def _build_chip(self, category_type: str, label: str):
        is_active = (self.selected_element == label) if category_type == "element" else (self.selected_type == label)
        elem_color = ft.Colors.WHITE
        if category_type == "element" and label != "全部":
            elem_color = GenshinTheme.get_element_color(label)
            
        def _on_click(e):
            if category_type == "element":
                self.selected_element = label
            else:
                self.selected_type = label
            # 局部更新 Chip 样式
            self._update_chips_visual()
            self._refresh_grid()
            # 不再调用全量 self.update()，由子组件各自负责更新

        chip = ft.Container(
            content=ft.Text(label, size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE if is_active else ft.Colors.WHITE_54),
            padding=ft.Padding(12, 6, 12, 6),
            bgcolor=ft.Colors.with_opacity(0.2, elem_color) if is_active else ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
            border_radius=15,
            border=ft.Border.all(1, elem_color if is_active else ft.Colors.TRANSPARENT),
            on_click=_on_click,
            animate=ft.Animation(200, ft.AnimationCurve.DECELERATE)
        )
        self.chips[f"{category_type}_{label}"] = chip
        return chip

    def _update_chips_visual(self):
        """局部遍历 Chips 并更新选中态视觉，避免 UI 抖动"""
        for key, chip in self.chips.items():
            cat, label = key.split("_", 1)
            is_active = (self.selected_element == label) if cat == "element" else (self.selected_type == label)
            elem_color = ft.Colors.WHITE
            if cat == "element" and label != "全部":
                elem_color = GenshinTheme.get_element_color(label)
            
            chip.content.color = ft.Colors.WHITE if is_active else ft.Colors.WHITE_54
            chip.bgcolor = ft.Colors.with_opacity(0.2, elem_color) if is_active else ft.Colors.with_opacity(0.05, ft.Colors.WHITE)
            chip.border = ft.Border.all(1, elem_color if is_active else ft.Colors.TRANSPARENT)
        
        try: self.filter_column.update() # 仅刷新过滤器行
        except: pass

    def _toggle_implemented_filter(self, e):
        self.show_only_implemented = e.control.value
        self._refresh_grid()

    def _on_item_click(self, item_id):
        # 二次检查实装状态
        item = next((i for i in self.items if i['id'] == item_id), None)
        if item and not item.get('is_implemented', True):
            return
            
        self.selected_id = item_id
        if self.on_select:
            self.on_select(item_id)
        # 刷新 Grid 即可
        self._refresh_grid()

    def _refresh_grid(self):
        # 1. 计算要显示的 ID 列表 (加入集合去重，防止 Flet 指针冲突)
        visible_ids = []
        seen_visible = set()
        for item in self.items:
            # 基础过滤过滤
            if self.show_only_implemented and not item.get('is_implemented', True):
                continue
            if self.allow_filter_element and self.selected_element != "全部" and item.get('element') != self.selected_element:
                continue
            if self.allow_filter_type and self.selected_type != "全部类型":
                item_type = item.get('type')
                if item_type and item_type != self.selected_type:
                    continue
            
            # 唯一性校验：Flet 严禁在同一个父容器中放置两个相同的控件对象
            if item['id'] not in seen_visible:
                visible_ids.append(item['id'])
                seen_visible.add(item['id'])

        # 2. 从池中摘取已存在的控件
        # 批量同步选中状态（仅对可见项）
        new_controls = []
        for vid in visible_ids:
            card = self.card_pool.get(vid)
            if card:
                card.set_selected(vid == self.selected_id)
                new_controls.append(card)

        # 3. 全量替换 Grid 控件列表 (Flet 处理动态增删最稳健的方式)
        self.grid.controls = new_controls
        
        try:
            self.grid.update() # 独立更新 GridView
        except Exception:
            pass
