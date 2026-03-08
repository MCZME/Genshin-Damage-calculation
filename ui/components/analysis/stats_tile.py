import flet as ft
from typing import Any, cast
from ui.theme import GenshinTheme
from ui.services.ui_formatter import UIFormatter
from ui.states.analysis_state import AnalysisState
from ui.components.analysis.base_widget import AnalysisTile

# --- Constants & Groups ---
STAT_GROUPS: dict[str, list[str]] = {
    "基础属性": ["生命值", "攻击力", "防御力", "元素精通"],
    "进阶属性": ["暴击率", "暴击伤害", "元素充能效率", "治疗加成", "受治疗加成"],
    "元素加成": ["火元素伤害加成", "水元素伤害加成", "草元素伤害加成", "雷元素伤害加成", "风元素伤害加成", "冰元素伤害加成", "岩元素伤害加成", "物理伤害加成"],
    "其他": ["抗打断", "护盾强效"]
}

DEFAULT_STATS: list[str] = ["攻击力", "生命值", "防御力", "元素精通", "暴击率", "暴击伤害", "元素充能效率", "伤害加成"]

def calculate_snapshot_stat(base_stats: dict[str, Any], mods: list[dict[str, Any]], key: str, element: str = "Neutral") -> tuple[float, float, str]:
    """
    [V8.5] 核心计算引擎：基于基础快照与动态修饰符还原瞬时数值。
    返回: (最终值, 加成值, 公式字符串)
    """
    base = float(base_stats.get(key, 0.0))
    pct_bonus = float(base_stats.get(f"{key}%", 0.0))
    flat_bonus = float(base_stats.get(f"固定{key}", 0.0))
    
    # 针对“伤害加成”的特殊逻辑：合并全伤与元素伤
    actual_keys = [key]
    if key == "伤害加成":
        if element != "Neutral":
            actual_keys.append(f"{element}元素伤害加成")
    
    # 计算公式追踪
    formula = f"{base:.0f}"
    
    # 叠加修饰符
    for m in mods:
        m_stat = str(m.get("stat", ""))
        m_val = float(m.get("value", 0.0))
        
        # 匹配属性名或其百分比/固定变体
        if m_stat in actual_keys:
            flat_bonus += m_val
        elif m_stat.replace("%", "") in actual_keys and "%" in m_stat:
            pct_bonus += m_val
        elif m_stat.replace("固定", "") in actual_keys and "固定" in m_stat:
            flat_bonus += m_val
            
    if key in ["攻击力", "生命值", "防御力"]:
        total = base * (1 + pct_bonus / 100) + flat_bonus
        bonus = total - base
        formula = f"{base:.0f} × (1 + {pct_bonus:.1f}%) + {flat_bonus:.0f}"
        return total, bonus, formula
    
    # 其他属性（如精通、双暴、充能）通常是平铺加法
    total = base + flat_bonus
    # 某些属性在 base_stats 中已经是百分比（如暴击率）
    bonus = total - base
    is_pct_stat = any(x in key for x in ["率", "伤害", "充能", "加成", "效率"])
    formula = f"{base:.1f}{'%' if is_pct_stat else ''} + {flat_bonus:.1f}"
    return total, bonus, formula

@ft.component
def CharacterStatusBar(current_hp: float, max_hp: float, current_energy: float, max_energy: float, theme_color: str):
    """[V9.2] 紧凑型生存状态栏：展示 HP 和能量进度"""
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
def StatsDashboard(state: AnalysisState, instance_id: str):
    """正常态渲染逻辑 (2x2 Dashboard)"""
    char_id = state.get_tile_char(instance_id)
    frame_id = state.model.current_frame
    
    # 1. 订阅数据槽位
    base_slot = state.data_manager.get_slot("char_base")
    
    # [FIX] 纠正 use_state 的用法：解构赋值
    snapshot, set_snapshot = ft.use_state(None)
    loading, set_loading = ft.use_state(False)

    # 2. 抓取当前帧快照
    def fetch_frame_data():
        if not state.adapter:
            return
        async def _fetch():
            set_loading(True)
            try:
                if state.adapter:
                    data = await state.adapter.get_frame(frame_id)
                    # [FIX] 显式转换消除 setter 参数告警
                    set_snapshot(cast(Any, data))
            finally:
                set_loading(False)
        state.run_task(_fetch)

    ft.use_effect(fetch_frame_data, [frame_id, char_id, state.model.current_session_id])

    if not base_slot or not base_slot.data or char_id not in base_slot.data:
        return ft.Container(content=ft.Text("请先选择角色", color=ft.Colors.WHITE_38), alignment=ft.Alignment.CENTER)

    # 3. 准备展示数据
    char_base = cast(dict[str, Any], base_slot.data[char_id])
    char_name = str(char_base.get("名称", "Unknown"))
    element_zh = "无"
    if state.app_state and char_name in state.app_state.char_map:
        element_zh = str(state.app_state.char_map[char_name].get("element", "无"))
    
    theme_color = GenshinTheme.get_element_color(element_zh)
    
    # 获取动态数据
    active_mods: list[dict[str, Any]] = []
    active_effects: list[dict[str, Any]] = []
    shields: list[dict[str, Any]] = []
    curr_hp = float(char_base.get("生命值", 0))
    max_hp = curr_hp
    curr_en = 0.0
    max_en = float(char_base.get("元素爆发能量", 40.0))

    # [FIX] 使用 cast 后的字典
    snap_dict = cast(dict[str, Any] | None, snapshot)
    if snap_dict and "team" in snap_dict:
        char_snap = next((c for c in snap_dict["team"] if c["entity_id"] == char_id), None)
        if char_snap:
            active_mods = char_snap.get("active_modifiers", [])
            active_effects = char_snap.get("active_effects", [])
            shields = char_snap.get("shields", [])
            curr_hp = float(char_snap.get("current_hp", curr_hp))
            curr_en = float(char_snap.get("current_energy", 0.0))
            final_hp, _, _ = calculate_snapshot_stat(char_base, active_mods, "生命值", element_zh)
            max_hp = final_hp

    # 获取用户偏好
    display_stats = state.get_stat_preferences(char_id)
    if not display_stats:
        display_stats = DEFAULT_STATS

    def create_stat_unit(key: str) -> ft.Control:
        total, bonus, _ = calculate_snapshot_stat(char_base, active_mods, key, element_zh)
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
        pair = display_stats[i:i+2]
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
        total_shield = sum(s.get('current_hp', 0) for s in shields)
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
            ft.Icon(UIFormatter.get_element_icon(element_zh), size=16, color=theme_color),
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
def StatsDetailAudit(state: AnalysisState, instance_id: str):
    """展开态渲染逻辑 (Full Screen Audit & Config)"""
    char_id = state.get_tile_char(instance_id)
    # [FIX] 纠正 use_state 的用法
    selected_stat, set_selected_stat = ft.use_state("攻击力")
    
    base_slot = state.data_manager.get_slot("char_base")
    frame_id = state.model.current_frame
    
    # [FIX] 解构赋值
    snapshot, set_snapshot = ft.use_state(None)

    # 副作用：抓取当前帧快照以获取修饰符
    def fetch_mods():
        if not state.adapter:
            return
        async def _fetch():
            if state.adapter:
                data = await state.adapter.get_frame(frame_id)
                # [FIX] 显式转换
                set_snapshot(cast(Any, data))
        state.run_task(_fetch)
    ft.use_effect(fetch_mods, [frame_id, char_id])

    if not base_slot or not base_slot.data or char_id not in base_slot.data:
        return ft.Text("数据未就绪")

    char_base = cast(dict[str, Any], base_slot.data[char_id])
    char_name = str(char_base.get("名称", "Unknown"))
    element_zh = "无"
    if state.app_state and char_name in state.app_state.char_map:
        element_zh = str(state.app_state.char_map[char_name].get("element", "无"))
    
    active_mods: list[dict[str, Any]] = []
    # [FIX] 使用解构赋值后的变量
    snap_dict = cast(dict[str, Any] | None, snapshot)
    if snap_dict and "team" in snap_dict:
        char_snap = next((c for c in snap_dict["team"] if c["entity_id"] == char_id), None)
        if char_snap:
            active_mods = char_snap.get("active_modifiers", [])

    # 获取当前勾选偏好
    prefs = state.get_stat_preferences(char_id) or DEFAULT_STATS

    # --- 左侧：配置列表 ---
    def create_list_item(key: str) -> ft.Control:
        # [FIX] 直接使用解构后的变量
        is_selected = (selected_stat == key)
        is_checked = key in prefs
        
        return ft.Container(
            content=ft.Row([
                ft.Checkbox(
                    value=is_checked, 
                    on_change=lambda _: state.toggle_stat_preference(char_id, key),
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
    total, bonus, formula = calculate_snapshot_stat(char_base, active_mods, selected_stat, element_zh)
    
    relevant_mods: list[dict[str, Any]] = []
    search_keys = [selected_stat, f"{selected_stat}%", f"固定{selected_stat}"]
    if selected_stat == "伤害加成":
        search_keys.append(f"{element_zh}元素伤害加成")
        
    for m in active_mods:
        if m.get("stat") in search_keys:
            relevant_mods.append(m)

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
    磁贴：角色实时面板 (V2.0 - 瞬时快照审计版)
    规格: 2x2
    """
    def __init__(self, state: AnalysisState, instance_id: str):
        super().__init__("角色实时面板", ft.Icons.PERSON_SEARCH_ROUNDED, "stats", state)
        self.instance_id = instance_id
        # 初始主题色，实际渲染时由内容组件动态计算
        self.theme_color = GenshinTheme.ELEMENT_COLORS["Neutral"]
        self.is_maximized = False # 由 TileContainer 状态驱动
        self.has_settings = True # [V8.8] 显式开启设置按钮

    def get_settings_items(self) -> list[ft.PopupMenuItem]:
        """[V9.0] 构造角色切换菜单项列表"""
        base_slot = self.state.data_manager.get_slot("char_base")
        if not base_slot or not base_slot.data:
            return []

        menu_items: list[ft.PopupMenuItem] = []
        char_data = cast(dict[int, Any], base_slot.data)
        iid = cast(str, self.instance_id) 
        
        for cid, stats in char_data.items():
            name = str(stats.get("名称", f"ID:{cid}"))
            # [FIX] 闭包内引用局部变量确保安全
            def make_handler(_cid, _iid=iid):
                return lambda e: self.state.set_tile_char(_iid, _cid)
            
            menu_items.append(ft.PopupMenuItem(content=ft.Text(name), on_click=make_handler(cid)))
        return menu_items

    def render(self) -> ft.Control:
        """
        [V8.6] 渲染入口分发。
        根据 self.is_maximized 状态决定展示仪表盘（2x2）还是深度审计（全屏）。
        """
        iid = cast(str, self.instance_id)
        if getattr(self, "is_maximized", False):
            return StatsDetailAudit(state=self.state, instance_id=iid)
        
        return StatsDashboard(state=self.state, instance_id=iid)
