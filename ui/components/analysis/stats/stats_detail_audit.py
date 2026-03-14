"""
[V9.5 Pro V2] 角色实时面板展开态审计组件

展开态渲染逻辑 - 二分监控矩阵布局
[V9.6] 简化为纯 UI 组件，接收 ViewModel 实例
[V9.7] 集成自适应公式链与乘区修饰符卡片
"""
import flet as ft

from ui.view_models.analysis.tile_vms.stats_vm import StatsViewModel, STAT_GROUPS, DEFAULT_STATS
from ui.components.analysis.stats.status_capsule import StatusCapsuleGrid
from ui.components.analysis.stats.status_indicator import AdaptiveStatusCluster
from ui.components.analysis.stats.formula_chain import InlineFormulaChain
from ui.services.ui_formatter import UIFormatter


@ft.component
def StatsDetailAudit(vm: StatsViewModel):
    """[V9.6] 展开态渲染 - 纯 UI 组件

    接收由父组件传入的 ViewModel 实例，不再自行管理生命周期。

    布局结构：
    ┌─────────────────────────────────────────────────────────┐
    │ 顶部：整合全景看板 (Integrated Header)                    │
    │ [图标+名称] | [自适应状态集群] | [帧号]                    │
    ├─────────────────────────────────────────────────────────┤
    │ 二分监控矩阵 (Split Monitor Matrix) - expand=3           │
    │ ┌────────────────────────────┬────────────────┐          │
    │ │ 左区 70% 配置矩阵 (横向)    │ 右区 30% 效果墙 │          │
    │ │ ┌─────┬─────┬─────┬─────┐ │ [胶囊网格]      │          │
    │ │ │生存 │基础 │进阶 │元素 │ │  · 效果1        │          │
    │ │ │状态 │属性 │属性 │加成 │ │  · 效果2        │          │
    │ │ └─────┴─────┴─────┴─────┘ │  · ...         │          │
    │ │                            │  (内部滚动)    │          │
    │ └────────────────────────────┴────────────────┘          │
    ├─────────────────────────────────────────────────────────┤
    │ 底部：审计面板 (Audit Panel) - expand=2                  │
    └─────────────────────────────────────────────────────────┘
    """
    # 本地 UI 状态
    selected_stat, set_selected_stat = ft.use_state("攻击力")

    # 从 VM 获取数据
    theme_color = vm.theme_color
    element = vm.element
    char_name = vm.char_name
    frame_id = vm.frame_id
    curr_hp = vm.current_hp
    max_hp = vm.max_hp
    curr_en = vm.current_energy
    max_en = vm.max_energy

    # 获取当前勾选偏好
    prefs_list = vm.get_display_stats() or DEFAULT_STATS
    prefs = set(prefs_list)

    # [V9.5 Pro V2] 获取自适应状态指示器数据
    # 展开模式：状态条始终可见 (always_show=True)
    # 通过 VM 代理方法获取选中状态
    status_selection = vm.get_status_bar_selection()
    status_indicators = vm.get_status_indicators(
        selection=status_selection,
        focus_name=selected_stat,
        always_show=True
    )
    effects_with_frames = vm.active_effects_with_frames

    # ============================================================
    # 第一层：顶部整合看板 (Integrated Header)
    # ============================================================
    def create_integrated_header() -> ft.Control:
        """
        [V9.5 Pro V2] 创建整合顶部看板
        使用 AdaptiveStatusCluster 替代固定宽度状态条
        状态条可点击选中，在审计面板显示详情
        """
        # 左侧集群：图标 + 名称
        left_cluster = ft.Row([
            ft.Icon(UIFormatter.get_element_icon(element), size=20, color=theme_color),
            ft.Text(char_name, size=16, weight=ft.FontWeight.BOLD),
        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        # 中间：自适应状态集群（点击切换展示状态）
        # 展开模式：状态条始终可见
        has_visible_indicators = any(ind.get("visible", False) for ind in status_indicators)
        status_cluster: ft.Control = ft.Container()  # 默认空占位
        if has_visible_indicators:
            # 直接使用 AdaptiveStatusCluster 返回的 Row
            # 点击仅切换展示状态，不再触发审计面板选中
            status_cluster = AdaptiveStatusCluster(
                indicators=status_indicators,
                expand=True,
                min_width=60.0,
                bar_height=6,
                on_indicator_click=vm.toggle_status_bar_selection
            )

        # 右侧：帧号
        right_unit = ft.Text(f"Frame {frame_id}", size=10, color=ft.Colors.WHITE_38)

        return ft.Container(
            content=ft.Row([
                left_cluster,
                status_cluster,
                right_unit,
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding.all(10),
            bgcolor=ft.Colors.BLACK_26,
            border_radius=ft.BorderRadius.all(8)
        )

    # ============================================================
    # 配置矩阵复选框工厂
    # ============================================================
    def create_stat_checkbox(key: str) -> ft.Control:
        """创建属性勾选项（数值项）- 适度紧凑的设计"""
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
                    on_change=lambda _: vm.state.vm.toggle_stat_preference(vm.target_char_id, key),
                    scale=0.75,
                    fill_color=ft.Colors.AMBER_400,
                    expand=1
                ),
                ft.Text(key, size=10, weight=ft.FontWeight.BOLD if is_selected else None, expand=4, no_wrap=True),
                ft.Text(f"{total:{fmt}}{suffix}", size=10, color=ft.Colors.AMBER_100, weight=ft.FontWeight.W_600, expand=2),
            ], tight=True, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding(left=6, right=6, top=2, bottom=2),
            bgcolor=ft.Colors.AMBER_900 if is_selected else ft.Colors.WHITE_12,
            border_radius=6,
            width=148,  # 适度放宽宽度
            on_click=lambda _: set_selected_stat(key)
        )

    # ============================================================
    # 第二层：二分监控矩阵 (Split Monitor Matrix)
    # ============================================================
    def create_split_monitor_matrix() -> ft.Control:
        """
        [V9.5 Pro V2] 创建二分监控矩阵
        - 左区 70%: 配置矩阵 (横向平铺)
        - 右区 30%: 效果墙（始终显示）+ 内部滚动
        """
        # 左区：构建平铺内容
        left_content: list[ft.Control] = [
            ft.Text("属性配置 (勾选以在仪表盘显示)", size=11, color=ft.Colors.WHITE_38),
        ]

        for gname, gstats in STAT_GROUPS.items():
            left_content.append(
                ft.Column([
                    ft.Text(gname, size=8, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_200),
                    ft.Row(
                        controls=[create_stat_checkbox(k) for k in gstats],
                        spacing=8,
                        wrap=True
                    )
                ], spacing=6)
            )

        left_zone = ft.Container(
            content=ft.Column(
                controls=left_content,
                spacing=8,
                scroll=ft.ScrollMode.ADAPTIVE,
                expand=True
            ),
            padding=ft.Padding.all(8),
            bgcolor=ft.Colors.BLACK_12,
            border_radius=ft.BorderRadius.all(8),
            expand=7  # 70%
        )

        # 右区：效果墙 (30%) - 始终显示
        if effects_with_frames:
            right_zone = ft.Container(
                content=ft.Column([
                    ft.Text(
                        f"活跃效果 ({len(effects_with_frames)})",
                        size=10,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE_54
                    ),
                    ft.Column(
                        controls=[
                            StatusCapsuleGrid(
                                effects=effects_with_frames,
                                bgcolor=ft.Colors.BLACK_26
                            )
                        ],
                        spacing=6,
                        scroll=ft.ScrollMode.ADAPTIVE,
                        expand=True
                    ),
                ], spacing=6, expand=True),
                padding=ft.Padding.all(12),
                bgcolor=ft.Colors.BLACK_12,
                border_radius=ft.BorderRadius.all(8),
                expand=3  # 30%
            )
        else:
            # 无效果时显示提示
            right_zone = ft.Container(
                content=ft.Column([
                    ft.Text("活跃效果", size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE_54),
                    ft.Text("当前无活跃效果", size=11, color=ft.Colors.WHITE_24, italic=True),
                ], spacing=6, alignment=ft.MainAxisAlignment.CENTER, expand=True),
                padding=ft.Padding.all(12),
                bgcolor=ft.Colors.BLACK_12,
                border_radius=ft.BorderRadius.all(8),
                expand=3,
                alignment=ft.Alignment.CENTER
            )

        return ft.Row([
            left_zone,
            right_zone,
        ], spacing=8, expand=3, vertical_alignment=ft.CrossAxisAlignment.STRETCH)

    # ============================================================
    # 第三层：底部审计面板 (Audit Panel)
    # ============================================================
    def render_audit_panel() -> ft.Control:
        """[V9.5 Pro V2] 根据选中项类型渲染审计面板"""
        # 组件配置模式：血条
        if selected_stat == "血条":
            hp_pct = (curr_hp / max_hp * 100) if max_hp > 0 else 0
            return ft.Container(
                content=ft.Column([
                    ft.Text("当前生命值", size=11, color=ft.Colors.WHITE_38),
                    ft.Row([
                        ft.Text(f"{curr_hp:.0f}", size=28, weight=ft.FontWeight.W_900, color=ft.Colors.GREEN_400),
                        ft.Text(f"/ {max_hp:.0f}", size=18, color=ft.Colors.WHITE_54),
                    ], vertical_alignment=ft.CrossAxisAlignment.END, spacing=4),
                    ft.ProgressBar(
                        value=hp_pct / 100,
                        bar_height=10,
                        color=ft.Colors.GREEN_400,
                        bgcolor=ft.Colors.WHITE_10,
                        expand=True
                    ),
                ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.START),
                padding=ft.Padding.all(15),
                bgcolor="#1A1822",
                border_radius=12,
                expand=2
            )

        # 组件配置模式：能量条
        elif selected_stat == "能量条":
            en_pct = (curr_en / max_en * 100) if max_en > 0 else 0
            return ft.Container(
                content=ft.Column([
                    ft.Text("当前能量", size=11, color=ft.Colors.WHITE_38),
                    ft.Row([
                        ft.Text(f"{curr_en:.1f}", size=28, weight=ft.FontWeight.W_900, color=theme_color),
                        ft.Text(f"/ {max_en:.0f}", size=18, color=ft.Colors.WHITE_54),
                    ], vertical_alignment=ft.CrossAxisAlignment.END, spacing=4),
                    ft.ProgressBar(
                        value=en_pct / 100,
                        bar_height=10,
                        color=theme_color,
                        bgcolor=ft.Colors.WHITE_10,
                        expand=True
                    ),
                ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.START),
                padding=ft.Padding.all(15),
                bgcolor="#1A1822",
                border_radius=12,
                expand=2
            )

        # 面板属性审计模式
        else:
            return render_stat_audit()

    def render_stat_audit() -> ft.Control:
        """[V9.9] 渲染属性审计详情（来源分组）"""

        # 获取结构化分解数据
        audit_result, zoned_mods = vm.get_stat_breakdown(selected_stat)

        # 内联式公式链组件（融合卡片）
        formula_chain = InlineFormulaChain(
            result=audit_result,
            zoned_mods=zoned_mods
        )


        # 计算范式标签
        paradigm_label = "累乘型" if audit_result.paradigm == "cumulative" else "累加型"
        paradigm_color = ft.Colors.GREEN_400 if audit_result.paradigm == "cumulative" else ft.Colors.CYAN_400

        # 图例说明
        legend_row = ft.Row([
            ft.Row([
                ft.Container(width=12, height=4, bgcolor=ft.Colors.AMBER_400, border_radius=2),
                ft.Text("基础值", size=9, color=ft.Colors.WHITE_54),
            ], spacing=4),
            ft.Row([
                ft.Container(width=12, height=4, bgcolor=ft.Colors.GREEN_400, border_radius=2),
                ft.Text("百分比", size=9, color=ft.Colors.WHITE_54),
            ], spacing=4),
            ft.Row([
                ft.Container(width=12, height=4, bgcolor=ft.Colors.CYAN_400, border_radius=2),
                ft.Text("固定值", size=9, color=ft.Colors.WHITE_54),
            ], spacing=4),
        ], spacing=16)

        return ft.Container(
            content=ft.Column([
                # 标题行
                ft.Row([
                    ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.SEARCH, size=16, color=theme_color),
                            ft.Text(f"{selected_stat} 审计详情", size=14, weight=ft.FontWeight.W_800),
                            ft.Container(
                                content=ft.Text(paradigm_label, size=9, color=paradigm_color, weight=ft.FontWeight.W_600),
                                padding=ft.Padding(left=6, right=6, top=2, bottom=2),
                                bgcolor=ft.Colors.WHITE_12,
                                border_radius=4
                            ),
                        ], spacing=8),
                        legend_row,
                    ], spacing=4, expand=True),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.START),
                
                # 融合式公式链（包含嵌入式卡片）
                formula_chain,
                
            ], spacing=15),
            padding=ft.Padding.all(15),
            bgcolor="#1A1822",
            border_radius=12,
            expand=2
        )

    # ============================================================
    # 主布局：三层结构
    # ============================================================
    main_controls: list[ft.Control] = [
        # 第一层：顶部整合看板
        create_integrated_header(),
        # 第二层：二分监控矩阵 (比例分配)
        create_split_monitor_matrix(),
        ft.Divider(height=1, color=ft.Colors.WHITE_10),
        # 第三层：底部审计面板 (比例分配)
        render_audit_panel(),
    ]

    return ft.Column(
        main_controls,
        spacing=10,
        expand=True
    )
