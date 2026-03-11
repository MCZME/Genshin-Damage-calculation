"""
[V9.1] 角色实时面板磁贴组件

重构说明：
- 数据转换逻辑已迁移至 StatsViewModel
- 组件仅负责 UI 渲染
- 混合使用缓存和动态查询
"""
import flet as ft
from typing import TYPE_CHECKING, Any, cast

from ui.components.analysis.base_widget import AnalysisTile
from ui.view_models.analysis.tile_vms.stats_vm import StatsViewModel, STAT_GROUPS, DEFAULT_STATS
from ui.theme import GenshinTheme
from ui.services.ui_formatter import UIFormatter

if TYPE_CHECKING:
    from ui.services.analysis_data_service import AnalysisDataService


@ft.component
def CharacterStatusBar(
    current_hp: float,
    max_hp: float,
    current_energy: float,
    max_energy: float,
    theme_color: str,
    show_hp: bool = True,
    show_energy: bool = True,
    compact: bool = True
):
    """[V9.5] 生存状态栏：展示 HP 和能量进度（响应式布局）
    支持独立显示控制：
    - show_hp=True, show_energy=False → 只显示 HP 条
    - show_hp=False, show_energy=True → 只显示能量条
    - 两者皆 False → 返回空容器

    Args:
        compact: 紧凑模式（用于仪表盘），展开态使用更宽的长条样式
    """
    # 如果两者都不显示，返回空容器
    if not show_hp and not show_energy:
        return ft.Container()

    hp_ratio = max(0.0, min(1.0, current_hp / max_hp)) if max_hp > 0 else 0
    en_ratio = max(0.0, min(1.0, current_energy / max_energy)) if max_energy > 0 else 0

    # [V9.5] 根据模式调整条的高度
    hp_bar_height = 4 if compact else 6
    en_bar_height = 2 if compact else 4

    bars: list[ft.Control] = []

    # HP Bar - 仅当 show_hp 为 True 时渲染
    if show_hp:
        bars.append(ft.ProgressBar(
            value=hp_ratio,
            bar_height=hp_bar_height,
            color=ft.Colors.GREEN_400,
            bgcolor=ft.Colors.WHITE_10,
            expand=True
        ))

    # Energy Bar (更细) - 仅当 show_energy 为 True 时渲染
    if show_energy:
        bars.append(ft.ProgressBar(
            value=en_ratio,
            bar_height=en_bar_height,
            color=theme_color,
            bgcolor=ft.Colors.WHITE_10,
            expand=True
        ))

    return ft.Column(bars, spacing=2, expand=True)


@ft.component
def StatsDashboard(
    data_service: 'AnalysisDataService',
    instance_id: str
):
    """正常态渲染逻辑 (2x2 Dashboard)"""
    # 创建 ViewModel
    vm = ft.use_memo(
        lambda: StatsViewModel(data_service, instance_id),
        [instance_id]
    )

    # 获取目标角色 ID (V9.2: 通过 vm 访问)
    char_id = data_service.state.get_tile_char(instance_id)
    frame_id = data_service.state.current_frame

    # 同步 ViewModel 的角色 ID
    if vm.target_char_id != char_id:
        vm.target_char_id = char_id

    # 获取基础数据槽位
    base_slot = data_service.get_slot("char_base")

    # [V9.3] 抓取当前帧快照 - 使用 ViewModel 的异步方法
    def fetch_frame_data():
        data_service.state.run_task(vm.fetch_snapshot)

    ft.use_effect(fetch_frame_data, [frame_id, char_id, data_service.state.current_session_id])

    # 检查数据状态
    if not base_slot or not base_slot.data or char_id not in base_slot.data:
        return ft.Container(
            content=ft.Text("请先选择角色", color=ft.Colors.WHITE_38),
            alignment=ft.Alignment.CENTER
        )

    # 获取基础渲染属性
    theme_color = vm.theme_color
    element = vm.element
    char_name = vm.char_name

    # 获取动态数据
    active_mods = vm.active_mods
    active_effects = vm.active_effects
    shields = vm.shields
    curr_hp = vm.current_hp
    max_hp = vm.max_hp
    curr_en = vm.current_energy
    max_en = vm.max_energy

    # 获取用户偏好
    display_stats = vm.get_display_stats()
    prefs = set(display_stats)  # 转换为集合便于快速查找

    # [V9.5] 生存状态条显示控制：使用"血条"/"能量条"而非"生命值"/"元素能量"
    show_hp_bar = "血条" in prefs
    show_energy_bar = "能量条" in prefs

    def create_stat_unit(key: str) -> ft.Control:
        total, bonus, _ = vm.calculate_stat(key)
        is_pct = any(x in key for x in ["率", "伤害", "充能", "加成", "效率"])
        fmt = ".1f" if is_pct else ".0f"
        suffix = "%" if is_pct else ""

        return ft.Column(
            controls=[
                ft.Text(key, size=9, color=ft.Colors.WHITE_54),
                ft.Row(
                    controls=[
                        ft.Text(f"{total:{fmt}}{suffix}", size=13, weight=ft.FontWeight.W_800),
                        ft.Text(f"+{bonus:{fmt}}{suffix}" if abs(bonus) > 0.1 else "", size=8, color=ft.Colors.GREEN_400)
                    ],
                    spacing=2,
                    vertical_alignment=ft.CrossAxisAlignment.END
                )
            ],
            spacing=0,
            expand=1
        )

    # 构造网格
    grid_rows: list[ft.Control] = []
    for i in range(0, len(display_stats), 2):
        pair = display_stats[i:i + 2]
        row_controls: list[ft.Control] = [create_stat_unit(k) for k in pair]
        if len(row_controls) < 2:
            row_controls.append(ft.Container(expand=1))
        grid_rows.append(ft.Row(controls=row_controls, spacing=10))

    # 效果图标行
    effect_tags: list[ft.Control] = [
        ft.Container(
            content=ft.Text(eff['name'][:2], size=8, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
            bgcolor=ft.Colors.AMBER_400,
            padding=ft.Padding(left=4, right=4, top=1, bottom=1),
            border_radius=3,
            tooltip=eff['name']
        ) for eff in active_effects
    ]

    # 护盾标识
    if shields:
        total_shield = vm.get_total_shield_hp()
        effect_tags.insert(0, ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.SHIELD_ROUNDED, size=10, color=ft.Colors.WHITE),
                ft.Text(f"{total_shield:.0f}", size=8, weight=ft.FontWeight.BOLD)
            ], spacing=2),
            bgcolor=ft.Colors.BLUE_GREY_700,
            padding=ft.Padding(left=4, right=4, top=1, bottom=1),
            border_radius=3
        ))

    main_column_controls: list[ft.Control] = []

    # [V9.2+] 顶部行：图标 + 名称 + 状态条（如果启用） + 帧号
    top_row_controls: list[ft.Control] = [
        ft.Icon(UIFormatter.get_element_icon(element), size=16, color=theme_color),
    ]

    # 名称 + 状态条列
    name_col_controls: list[ft.Control] = [
        ft.Text(char_name, size=13, weight=ft.FontWeight.BOLD),
    ]

    # [V9.2+] 根据偏好决定是否渲染状态条
    if show_hp_bar or show_energy_bar:
        name_col_controls.append(
            CharacterStatusBar(
                curr_hp, max_hp, curr_en, max_en, theme_color,
                show_hp=show_hp_bar,
                show_energy=show_energy_bar
            )
        )

    top_row_controls.append(ft.Column(name_col_controls, spacing=2, expand=True))
    top_row_controls.append(
        ft.Text(f"F_{frame_id}", size=9, color=ft.Colors.WHITE_10, font_family="Consolas")
    )

    main_column_controls.append(
        ft.Row(top_row_controls, vertical_alignment=ft.CrossAxisAlignment.START)
    )
    main_column_controls.append(ft.Divider(height=1, color=ft.Colors.WHITE_10))
    main_column_controls.append(ft.Column(controls=grid_rows, spacing=4, scroll=ft.ScrollMode.HIDDEN, expand=True))
    main_column_controls.append(ft.Row([
        ft.Row(controls=effect_tags, spacing=4, expand=True, wrap=True),
        ft.Text(f"{len(active_mods)} Mods", size=8, color=ft.Colors.WHITE_24),
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))

    return ft.Column(
        controls=main_column_controls,
        expand=True,
        spacing=6
    )


@ft.component
def StatsDetailAudit(
    data_service: 'AnalysisDataService',
    instance_id: str
):
    """[V9.5] 展开态渲染逻辑 - 三层响应式布局重构

    布局结构：
    ┌─────────────────────────────────────────────────────────┐
    │ 顶部：全景看板 (Identity Header)                          │
    │ [图标] [角色名] [━━━━━━ HP条 ━━━━━━] [━━ 能量条 ━━] [帧号] │
    ├─────────────────────────────────────────────────────────┤
    │ 中部：混合配置矩阵 (Hybrid Config Matrix)                 │
    │ ┌─────────┬─────────┬─────────┬─────────┐               │
    │ │ 生存状态 │ 基础属性 │ 进阶属性 │ 元素加成 │               │
    │ └─────────┴─────────┴─────────┴─────────┘               │
    ├─────────────────────────────────────────────────────────┤
    │ 底部：动态审计详情 (Audit Panel)                          │
    └─────────────────────────────────────────────────────────┘
    """
    # 创建 ViewModel
    vm = ft.use_memo(
        lambda: StatsViewModel(data_service, instance_id),
        [instance_id]
    )

    char_id = data_service.state.get_tile_char(instance_id)
    selected_stat, set_selected_stat = ft.use_state("攻击力")

    base_slot = data_service.get_slot("char_base")
    frame_id = data_service.state.current_frame

    # 同步 ViewModel 的角色 ID
    if vm.target_char_id != char_id:
        vm.target_char_id = char_id

    # 使用 ViewModel 的异步方法抓取快照
    def fetch_mods():
        data_service.state.run_task(vm.fetch_snapshot)

    ft.use_effect(fetch_mods, [char_id])

    if not base_slot or not base_slot.data or char_id not in base_slot.data:
        return ft.Text("数据未就绪")

    # 获取当前勾选偏好
    prefs_list = vm.get_display_stats() or DEFAULT_STATS
    prefs = set(prefs_list)

    # [V9.5] 从偏好中读取血条/能量条显示控制
    show_hp_bar = "血条" in prefs
    show_energy_bar = "能量条" in prefs

    # 获取渲染所需数据
    theme_color = vm.theme_color
    element = vm.element
    char_name = vm.char_name
    curr_hp = vm.current_hp
    max_hp = vm.max_hp
    curr_en = vm.current_energy
    max_en = vm.max_energy

    # ============================================================
    # 第一层：顶部全景看板 (Identity Header)
    # ============================================================
    def create_identity_header() -> ft.Control:
        """创建顶部全景看板"""
        # 基础控件：图标 + 名称
        header_controls: list[ft.Control] = [
            ft.Icon(UIFormatter.get_element_icon(element), size=20, color=theme_color),
            ft.Text(char_name, size=16, weight=ft.FontWeight.BOLD),
        ]

        # 如果启用状态条，添加展开态状态条
        if show_hp_bar or show_energy_bar:
            header_controls.append(
                ft.Container(
                    content=CharacterStatusBar(
                        curr_hp, max_hp, curr_en, max_en, theme_color,
                        show_hp=show_hp_bar,
                        show_energy=show_energy_bar,
                        compact=False  # 展开态使用更宽的样式
                    ),
                    width=200,  # 给状态条一个固定宽度
                    padding=ft.Padding(top=4, bottom=4, left=0, right=0)
                )
            )

        # 帧号
        header_controls.append(
            ft.Text(f"Frame {frame_id}", size=10, color=ft.Colors.WHITE_38)
        )

        return ft.Container(
            content=ft.Row(
                header_controls,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=ft.Padding.all(10),
            bgcolor=ft.Colors.BLACK_26,
            border_radius=ft.BorderRadius.all(8)
        )

    # ============================================================
    # 第二层：中部混合配置矩阵 (Hybrid Config Matrix)
    # ============================================================
    def create_component_checkbox(key: str) -> ft.Control:
        """创建组件勾选项（血条/能量条）- 无数值显示"""
        is_selected = (selected_stat == key)
        is_checked = key in prefs

        return ft.Container(
            content=ft.Row([
                ft.Checkbox(
                    value=is_checked,
                    on_change=lambda _: data_service.state.toggle_stat_preference(char_id, key),
                    scale=0.75,
                    fill_color=ft.Colors.AMBER_400
                ),
                ft.Text(key, size=11, weight=ft.FontWeight.BOLD if is_selected else None, expand=True),
            ], spacing=2, tight=True, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding(left=6, right=6, top=2, bottom=2),
            bgcolor=ft.Colors.AMBER_900 if is_selected else ft.Colors.WHITE_12,
            border_radius=6,
            on_click=lambda _: set_selected_stat(key)
        )

    def create_stat_checkbox(key: str) -> ft.Control:
        """创建属性勾选项（数值项）- 带数值显示"""
        is_selected = (selected_stat == key)
        is_checked = key in prefs

        # 计算属性值
        total, bonus, _ = vm.calculate_stat(key)
        is_pct = any(x in key for x in ["率", "伤害", "充能", "加成", "效率"])
        suffix = "%" if is_pct else ""
        fmt = ".1f" if is_pct else ".0f"

        return ft.Container(
            content=ft.Row([
                ft.Checkbox(
                    value=is_checked,
                    on_change=lambda _: data_service.state.toggle_stat_preference(char_id, key),
                    scale=0.75,
                    fill_color=ft.Colors.AMBER_400
                ),
                ft.Text(key, size=11, weight=ft.FontWeight.BOLD if is_selected else None, expand=True),
                ft.Text(f"{total:{fmt}}{suffix}", size=11, color=ft.Colors.AMBER_100, weight=ft.FontWeight.W_600),
            ], spacing=2, tight=True, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding(left=6, right=6, top=2, bottom=2),
            bgcolor=ft.Colors.AMBER_900 if is_selected else ft.Colors.WHITE_12,
            border_radius=6,
            on_click=lambda _: set_selected_stat(key)
        )

    # [V9.5] 组件项列表（生存状态分组）
    COMPONENT_KEYS = ["血条", "能量条"]

    # 将属性分组转换为列布局
    group_columns: list[ft.Control] = []
    for gname, gstats in STAT_GROUPS.items():
        column_content: list[ft.Control] = [
            ft.Text(gname, size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_200),
        ]
        for k in gstats:
            # 根据是否为组件项选择不同的渲染方式
            if k in COMPONENT_KEYS:
                column_content.append(create_component_checkbox(k))
            else:
                column_content.append(create_stat_checkbox(k))

        group_columns.append(
            ft.Column(controls=column_content, spacing=3, expand=1)
        )

    # 属性矩阵行
    matrix_row = ft.Row(
        controls=group_columns,
        spacing=15,
        expand=True
    )

    # ============================================================
    # 第三层：底部动态审计详情 (Audit Panel)
    # ============================================================
    def render_audit_panel() -> ft.Control:
        """[V9.5] 根据选中项类型渲染不同的审计面板"""
        # 组件配置模式：血条
        if selected_stat == "血条":
            hp_pct = (curr_hp / max_hp * 100) if max_hp > 0 else 0
            return ft.Container(
                content=ft.Column([
                    ft.Text("当前生命值", size=10, color=ft.Colors.WHITE_38),
                    ft.Row([
                        ft.Text(f"{curr_hp:.0f}", size=24, weight=ft.FontWeight.W_900, color=ft.Colors.GREEN_400),
                        ft.Text(f"/ {max_hp:.0f}", size=16, color=ft.Colors.WHITE_54),
                    ], vertical_alignment=ft.CrossAxisAlignment.END, spacing=4),
                    ft.Text(f"({hp_pct:.1f}%)", size=14, color=ft.Colors.AMBER_200),
                    ft.ProgressBar(
                        value=hp_pct / 100,
                        bar_height=8,
                        color=ft.Colors.GREEN_400,
                        bgcolor=ft.Colors.WHITE_10,
                        expand=True
                    ),
                ], spacing=8, horizontal_alignment=ft.CrossAxisAlignment.START),
                padding=ft.Padding.all(15),
                bgcolor="#1A1822",
                border_radius=12,
                expand=True
            )

        # 组件配置模式：能量条
        elif selected_stat == "能量条":
            en_pct = (curr_en / max_en * 100) if max_en > 0 else 0
            return ft.Container(
                content=ft.Column([
                    ft.Text("当前能量", size=10, color=ft.Colors.WHITE_38),
                    ft.Row([
                        ft.Text(f"{curr_en:.1f}", size=24, weight=ft.FontWeight.W_900, color=theme_color),
                        ft.Text(f"/ {max_en:.0f}", size=16, color=ft.Colors.WHITE_54),
                    ], vertical_alignment=ft.CrossAxisAlignment.END, spacing=4),
                    ft.Text(f"({en_pct:.1f}%)", size=14, color=ft.Colors.AMBER_200),
                    ft.ProgressBar(
                        value=en_pct / 100,
                        bar_height=8,
                        color=theme_color,
                        bgcolor=ft.Colors.WHITE_10,
                        expand=True
                    ),
                ], spacing=8, horizontal_alignment=ft.CrossAxisAlignment.START),
                padding=ft.Padding.all(15),
                bgcolor="#1A1822",
                border_radius=12,
                expand=True
            )

        # 面板属性审计模式
        else:
            return render_stat_audit()

    def render_stat_audit() -> ft.Control:
        """渲染属性审计详情（公式 + 修饰符堆栈）"""
        total, bonus, formula = vm.calculate_stat(selected_stat)
        relevant_mods = vm.get_relevant_mods(selected_stat)

        # 判断是否为百分比属性
        is_pct = any(x in selected_stat for x in ["率", "伤害", "充能", "加成", "效率"])
        suffix = "%" if is_pct else ""

        # 审计公式面板
        formula_panel = ft.Container(
            content=ft.Column([
                ft.Text("计算公式", size=10, color=ft.Colors.WHITE_38),
                ft.Text(formula, size=14, font_family="Consolas", color=ft.Colors.AMBER_100),
            ], spacing=4),
            padding=ft.Padding.all(12),
            bgcolor=ft.Colors.BLACK_26,
            border_radius=8,
            expand=1
        )

        # 最终结果面板
        result_panel = ft.Container(
            content=ft.Column([
                ft.Text("最终结果", size=10, color=ft.Colors.WHITE_38),
                ft.Text(f"{total:.2f}{suffix}", size=18, weight=ft.FontWeight.W_900, color=ft.Colors.WHITE),
            ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding.all(12),
            bgcolor=ft.Colors.AMBER_900,
            border_radius=8
        )

        # 修饰符列表（横向滚动）
        modifier_cards: list[ft.Control] = [
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.BOLT_ROUNDED, size=12, color=ft.Colors.AMBER_400),
                    ft.Text(m['name'], size=10, weight=ft.FontWeight.W_600, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(f"+{m['value']:.1f}", size=11, color=ft.Colors.GREEN_400, weight=ft.FontWeight.BOLD),
                    ft.Text(f"({m['op']})", size=8, color=ft.Colors.WHITE_38),
                ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.Padding.all(8),
                bgcolor=ft.Colors.WHITE_10,
                border_radius=6,
                width=100
            ) for m in relevant_mods[:8]
        ]

        modifiers_panel = ft.Column([
            ft.Text(f"贡献修饰符 ({len(relevant_mods)})", size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE_54),
            ft.Row(
                controls=modifier_cards if relevant_mods else [ft.Text("当前帧无相关修饰符", color=ft.Colors.WHITE_24, italic=True, size=10)],
                spacing=8,
                scroll=ft.ScrollMode.ADAPTIVE
            )
        ], spacing=6)

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(f"🔍 {selected_stat} 审计详情", size=14, weight=ft.FontWeight.W_800, expand=True),
                    result_panel
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                formula_panel,
                modifiers_panel,
            ], spacing=10),
            padding=ft.Padding.all(15),
            bgcolor="#1A1822",
            border_radius=12,
            expand=True
        )

    # ============================================================
    # 主布局：三层结构
    # ============================================================
    return ft.Column([
        # 第一层：顶部全景看板
        create_identity_header(),
        # 第二层：中部混合配置矩阵
        ft.Container(
            content=ft.Column([
                ft.Text("属性配置 (勾选以在仪表盘显示)", size=11, color=ft.Colors.WHITE_38),
                matrix_row,
            ], spacing=8),
            padding=ft.Padding.all(10),
            bgcolor=ft.Colors.BLACK_12,
            border_radius=ft.BorderRadius.all(8)
        ),
        ft.Divider(height=1, color=ft.Colors.WHITE_10),
        # 第三层：底部动态审计详情
        render_audit_panel(),
    ], spacing=10, expand=True, scroll=ft.ScrollMode.ADAPTIVE)


class CharacterStatsTile(AnalysisTile):
    """
    [V9.1] 磁贴：角色实时面板 (瞬时快照审计版)
    规格: 2x2

    重构说明：
    - 数据转换逻辑已迁移至 StatsViewModel
    - 组件仅负责 UI 渲染
    """

    def __init__(
        self,
        data_service: 'AnalysisDataService',
        instance_id: str
    ):
        super().__init__(
            "角色实时面板",
            ft.Icons.PERSON_SEARCH_ROUNDED,
            "stats",
            data_service.state
        )
        self.data_service = data_service
        self.instance_id = instance_id
        self.theme_color = GenshinTheme.ELEMENT_COLORS["Neutral"]
        self.is_maximized = False
        self.has_settings = True

    def get_settings_items(self) -> list[ft.PopupMenuItem]:
        """[V9.1] 构造角色切换菜单项列表"""
        base_slot = self.data_service.get_slot("char_base")
        if not base_slot or not base_slot.data:
            return []

        menu_items: list[ft.PopupMenuItem] = []
        char_data = cast(dict[int, Any], base_slot.data)
        iid = cast(str, self.instance_id)

        for cid, stats in char_data.items():
            name = str(stats.get("名称", f"ID:{cid}"))

            def make_handler(_cid, _iid=iid):
                return lambda e: self.data_service.state.set_tile_char(_iid, _cid)

            menu_items.append(ft.PopupMenuItem(content=ft.Text(name), on_click=make_handler(cid)))
        return menu_items

    def render(self) -> ft.Control:
        """
        [V9.1] 渲染入口分发。
        根据 self.is_maximized 状态决定展示仪表盘（2x2）还是深度审计（全屏）。
        """
        iid = cast(str, self.instance_id)
        if getattr(self, "is_maximized", False):
            return StatsDetailAudit(data_service=self.data_service, instance_id=iid)

        return StatsDashboard(data_service=self.data_service, instance_id=iid)
