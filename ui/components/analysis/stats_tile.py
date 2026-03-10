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
    theme_color: str
):
    """[V9.1] 紧凑型生存状态栏：展示 HP 和能量进度"""
    hp_ratio = max(0.0, min(1.0, current_hp / max_hp)) if max_hp > 0 else 0
    en_ratio = max(0.0, min(1.0, current_energy / max_energy)) if max_energy > 0 else 0

    return ft.Column([
        # HP Bar
        ft.Stack([
            ft.Container(height=4, bgcolor=ft.Colors.WHITE_10, border_radius=2),
            ft.Container(height=4, width=200 * hp_ratio, bgcolor=ft.Colors.GREEN_400, border_radius=2, animate=300),
        ], width=200),
        # Energy Bar (更细)
        ft.Stack([
            ft.Container(height=2, bgcolor=ft.Colors.WHITE_10, border_radius=1),
            ft.Container(height=2, width=200 * en_ratio, bgcolor=theme_color, border_radius=1, animate=300, opacity=0.8),
        ], width=200),
    ], spacing=2)


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

    # 本地状态
    snapshot, set_snapshot = ft.use_state(None)
    loading, set_loading = ft.use_state(False)

    # 抓取当前帧快照
    def fetch_frame_data():
        if not data_service.adapter:
            return

        async def _fetch():
            set_loading(True)
            try:
                if data_service.adapter:
                    data = await data_service.adapter.get_frame(frame_id)
                    set_snapshot(cast(Any, data))
            finally:
                set_loading(False)

        data_service.state.run_task(_fetch)

    ft.use_effect(fetch_frame_data, [frame_id, char_id, data_service.state.current_session_id])

    # 检查数据状态
    if not base_slot or not base_slot.data or char_id not in base_slot.data:
        return ft.Container(
            content=ft.Text("请先选择角色", color=ft.Colors.WHITE_38),
            alignment=ft.Alignment.CENTER
        )

    # 更新 ViewModel 快照
    vm.snapshot = cast(dict[str, Any] | None, snapshot)

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
            padding=ft.padding.symmetric(horizontal=4, vertical=1),
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
            padding=ft.padding.symmetric(horizontal=4, vertical=1),
            border_radius=3
        ))

    main_column_controls: list[ft.Control] = [
        ft.Row([
            ft.Icon(UIFormatter.get_element_icon(element), size=16, color=theme_color),
            ft.Column([
                ft.Text(char_name, size=13, weight=ft.FontWeight.BOLD),
                CharacterStatusBar(curr_hp, max_hp, curr_en, max_en, theme_color)
            ], spacing=2, expand=True),
            ft.Text(f"F_{frame_id}", size=9, color=ft.Colors.WHITE_10, font_family="Consolas")
        ], vertical_alignment=ft.CrossAxisAlignment.START),
        ft.Divider(height=1, color=ft.Colors.WHITE_10),
        ft.Column(controls=grid_rows, spacing=4, scroll=ft.ScrollMode.HIDDEN, expand=True),
        ft.Row([
            ft.Row(controls=effect_tags, spacing=4, expand=True, wrap=True),
            ft.Text(f"{len(active_mods)} Mods", size=8, color=ft.Colors.WHITE_24),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
    ]

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
    """展开态渲染逻辑 (Full Screen Audit & Config)"""
    # 创建 ViewModel
    vm = ft.use_memo(
        lambda: StatsViewModel(data_service, instance_id),
        [instance_id]
    )

    char_id = data_service.state.get_tile_char(instance_id)
    selected_stat, set_selected_stat = ft.use_state("攻击力")

    base_slot = data_service.get_slot("char_base")
    frame_id = data_service.state.current_frame  # V9.2: 直接访问 vm 属性

    # 同步 ViewModel 的角色 ID
    if vm.target_char_id != char_id:
        vm.target_char_id = char_id

    # 本地状态
    snapshot, set_snapshot = ft.use_state(None)

    # 副作用：抓取当前帧快照以获取修饰符
    def fetch_mods():
        if not data_service.adapter:
            return

        async def _fetch():
            if data_service.adapter:
                data = await data_service.adapter.get_frame(frame_id)
                set_snapshot(cast(Any, data))

        data_service.state.run_task(_fetch)

    ft.use_effect(fetch_mods, [frame_id, char_id])

    if not base_slot or not base_slot.data or char_id not in base_slot.data:
        return ft.Text("数据未就绪")

    # 更新 ViewModel 快照
    vm.snapshot = cast(dict[str, Any] | None, snapshot)

    # 获取当前勾选偏好
    prefs = vm.get_display_stats() or DEFAULT_STATS

    # --- 左侧：配置列表 ---
    def create_list_item(key: str) -> ft.Control:
        is_selected = (selected_stat == key)
        is_checked = key in prefs

        return ft.Container(
            content=ft.Row([
                ft.Checkbox(
                    value=is_checked,
                    on_change=lambda _: data_service.state.toggle_stat_preference(char_id, key),
                    scale=0.8,
                    fill_color=ft.Colors.AMBER_400
                ),
                ft.Text(key, size=13, weight=ft.FontWeight.BOLD if is_selected else None),
            ], spacing=0),
            padding=ft.padding.symmetric(horizontal=10, vertical=2),
            bgcolor=ft.Colors.WHITE_10 if is_selected else None,
            border_radius=8,
            on_click=lambda _: set_selected_stat(key)
        )

    list_controls: list[ft.Control] = [
        ft.Text("展示配置 (勾选以在仪表盘显示)", size=12, color=ft.Colors.WHITE_38),
        ft.Column([
            ft.ExpansionTile(
                title=ft.Text(gname, size=12, weight=ft.FontWeight.BOLD),
                controls=[create_list_item(k) for k in gstats],
                expanded=True,
                text_color=ft.Colors.AMBER_200,
                controls_padding=ft.padding.only(left=10)
            ) for gname, gstats in STAT_GROUPS.items()
        ], scroll=ft.ScrollMode.ADAPTIVE, expand=True)
    ]
    left_column = ft.Column(controls=list_controls, expand=1)

    # --- 右侧：审计面板 ---
    total, bonus, formula = vm.calculate_stat(selected_stat)

    relevant_mods = vm.get_relevant_mods(selected_stat)

    modifier_list_controls: list[ft.Control] = [
        ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.BOLT_ROUNDED, size=14, color=ft.Colors.AMBER_400),
                ft.Text(m['name'], size=13, weight=ft.FontWeight.W_600, expand=True),
                ft.Text(f"+{m['value']:.1f}", color=ft.Colors.GREEN_400, weight=ft.FontWeight.BOLD),
                ft.Text(f"({m['op']})", size=10, color=ft.Colors.WHITE_24)
            ]),
            padding=10, bgcolor=ft.Colors.WHITE_10, border_radius=8
        ) for m in relevant_mods
    ]

    right_panel_content: list[ft.Control] = [
        ft.Text(f"{selected_stat} 审计详情", size=20, weight=ft.FontWeight.W_900),
        ft.Container(
            content=ft.Column([
                ft.Text("瞬时计算公式", size=11, color=ft.Colors.WHITE_38),
                ft.Text(formula, size=16, font_family="Consolas", color=ft.Colors.AMBER_100),
                ft.Divider(height=20, color=ft.Colors.WHITE_10),
                ft.Row([
                    ft.Text("最终结果", size=12, color=ft.Colors.WHITE_54),
                    ft.Text(f"{total:.2f}", size=24, weight=ft.FontWeight.W_900, color=ft.Colors.WHITE)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ]),
            padding=20, bgcolor=ft.Colors.BLACK12, border_radius=12
        ),
        ft.Text(f"贡献修饰符 ({len(relevant_mods)})", size=12, weight=ft.FontWeight.BOLD),
        ft.Column(controls=modifier_list_controls, scroll=ft.ScrollMode.ADAPTIVE, expand=True) if relevant_mods else ft.Text("当前帧无相关动态修饰符", color=ft.Colors.WHITE_24, italic=True)
    ]

    right_panel = ft.Container(
        content=ft.Column(controls=right_panel_content, spacing=15),
        padding=20,
        expand=2,
        bgcolor="#1A1822",
        border_radius=12
    )

    return ft.Row([left_column, ft.VerticalDivider(width=1), right_panel], expand=True, spacing=20)


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
