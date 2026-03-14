"""
[V9.8] 内联式公式链组件

提供融合式的计算链展示，修饰符卡片直接嵌入公式中。
"""
import flet as ft
from ui.view_models.analysis.tile_vms.types import AuditResult, ZonedModifier, ModifierZone


# 乘区颜色方案
ZONE_COLORS: dict[ModifierZone, str] = {
    ModifierZone.BASE: ft.Colors.AMBER_400,      # 琥珀色 - 基础值
    ModifierZone.PERCENT: ft.Colors.GREEN_400,   # 绿色 - 百分比区
    ModifierZone.FLAT: ft.Colors.CYAN_400,       # 青蓝色 - 固定值区
}

# 负值颜色
NEGATIVE_COLOR = ft.Colors.RED_400


@ft.component
def ModifierInlineCard(
    modifier: ZonedModifier,
    is_highlighted: bool = False
) -> ft.Control:
    """
    内联修饰符卡片 - 紧凑设计，嵌入公式链中

    布局:
    ┌──────────┐
    │ 名称     │
    │ +值      │
    └──────────┘
    宽度约 80-100px，高度约 50px

    Args:
        modifier: 修饰符数据
        is_highlighted: 是否高亮
    """
    zone_color = ZONE_COLORS.get(modifier.zone, ft.Colors.WHITE)

    # 格式化值显示
    is_negative = modifier.value < 0
    value_color = NEGATIVE_COLOR if is_negative else zone_color
    value_sign = "-" if is_negative else "+"
    value_abs = abs(modifier.value)

    # 判断是否为百分比值
    is_pct = "%" in modifier.stat or modifier.zone == ModifierZone.PERCENT
    value_text = f"{value_sign}{value_abs:.1f}{'%' if is_pct else ''}"

    # 高亮边框
    border = ft.Border.all(2, zone_color) if is_highlighted else ft.Border.all(1, ft.Colors.WHITE_24)

    return ft.Container(
        content=ft.Column([
            ft.Text(
                modifier.name[:6],  # 截断名称
                size=9,
                weight=ft.FontWeight.W_600,
                no_wrap=True,
                overflow=ft.TextOverflow.ELLIPSIS,
                color=ft.Colors.WHITE_70
            ),
            ft.Text(
                value_text,
                size=11,
                color=value_color,
                weight=ft.FontWeight.BOLD,
                font_family="Consolas"
            ),
        ], spacing=1, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.Padding(left=6, right=6, top=4, bottom=4),
        bgcolor=ft.Colors.WHITE_12 if is_highlighted else ft.Colors.WHITE_10,
        border_radius=4,
        width=72,
        border=border
    )


@ft.component
def ZoneSummaryRow(
    label: str,
    value: float,
    zone: ModifierZone,
    is_pct: bool = False
) -> ft.Control:
    """乘区小计行"""
    zone_color = ZONE_COLORS.get(zone, ft.Colors.WHITE)
    suffix = "%" if is_pct else ""
    value_text = f"{value:.1f}{suffix}" if is_pct else f"{value:.0f}"

    return ft.Row([
        ft.Container(
            content=ft.Text("─" * 4, size=11, color=ft.Colors.WHITE_24),
            width=30
        ),
        ft.Text("=", size=11, color=ft.Colors.WHITE_54),
        ft.Text(f"{label}:", size=10, color=ft.Colors.WHITE_54),
        ft.Text(value_text, size=11, color=zone_color, weight=ft.FontWeight.W_600),
    ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER)





@ft.component
def InlineFormulaChain(
    result: AuditResult,
    zoned_mods: list[ZonedModifier]
) -> ft.Control:
    """
    内联式公式链 - 卡片直接嵌入公式中

    累加型布局:
    [基础值区段] + [加成卡片...]
    = 最终结果

    Args:
        result: 审计计算结果
        zoned_mods: 分区后的修饰符列表
    """
    # 按乘区分组修饰符
    flat_mods = [m for m in zoned_mods if m.zone == ModifierZone.FLAT]
    percent_mods = [m for m in zoned_mods if m.zone == ModifierZone.PERCENT]
    base_mods = [m for m in zoned_mods if m.zone == ModifierZone.BASE]

    # 判断是否为百分比属性
    is_pct = result.is_pct_stat
    suffix = "%" if is_pct else ""



    # ===== 构建单个域 (Domain) =====
    def build_domain(
        mods: list[ZonedModifier],
        domain_name: str,
        sum_value: float,
        zone: ModifierZone,
        is_pct_domain: bool = False
    ) -> ft.Control | None:
        if not mods and sum_value == 0:
            return None

        # 1. 域的卡片行 (卡片之间添加 +)
        card_row_controls: list[ft.Control] = []
        for i, m in enumerate(mods[:6]):
            if i > 0:
                card_row_controls.append(ft.Text("+", size=10, color=ft.Colors.WHITE_24))
            card_row_controls.append(ModifierInlineCard(m))

        # 2. 域的总和行 (自带上边框作为分割线)
        domain_color = ZONE_COLORS.get(zone, ft.Colors.WHITE)
        sum_suffix = "%" if is_pct_domain else ""
        sum_text = f"{sum_value:.1f}{sum_suffix}" if is_pct_domain else f"{sum_value:.0f}"

        sum_section = ft.Container(
            content=ft.Row([
                ft.Text("总和:", size=10, color=ft.Colors.WHITE_54),
                ft.Text(sum_text, size=13, color=domain_color, weight=ft.FontWeight.W_800),
            ], spacing=4, alignment=ft.MainAxisAlignment.CENTER, tight=True),
            border=ft.Border.only(top=ft.BorderSide(1, ft.Colors.WHITE_10)),
            padding=ft.padding.only(top=6),
            margin=ft.margin.only(top=2)
        )

        # 返回封装在 tight Row 中的 Container (防止宽度撑满)
        return ft.Row([
            ft.Container(
                content=ft.Column([
                    ft.Row(card_row_controls, spacing=4, alignment=ft.MainAxisAlignment.CENTER, tight=True),
                    sum_section
                ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True),
                padding=ft.Padding.all(8),
                border=ft.Border.all(1, ft.Colors.WHITE_10),
                border_radius=8,
                bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
            )
        ], tight=True)

    domain_blocks: list[ft.Control] = []

    if result.paradigm == "cumulative":
        # ===== 累乘型公式: Base + BaseMods * (1 + Percent) + Flat =====
        
        # 1. 静态基础值
        domain_blocks.append(ft.Column([
            ft.Container(
                content=ft.Text(f"{result.base:.0f}{suffix}", size=14, color=ZONE_COLORS[ModifierZone.BASE], weight=ft.FontWeight.BOLD),
                padding=ft.Padding(left=4, right=4, top=2, bottom=2)
            ),
            ft.Text("基础白值", size=10, color=ft.Colors.WHITE_38)
        ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True))

        # 2. 基础加成域 (如果有) [V10.1: 基础加成现在也盒装]
        if base_mods:
            domain_blocks.append(ft.Text("+", size=16, color=ft.Colors.WHITE_54))
            base_domain = build_domain(base_mods, "基础加成", sum(m.value for m in base_mods), ModifierZone.BASE, is_pct)
            if base_domain: domain_blocks.append(base_domain)

        # 3. 百分比域 (1 + %)
        if percent_mods and abs(result.pct_sum) > 0.01:
            domain_blocks.append(ft.Text("×", size=16, color=ft.Colors.WHITE_54))
            domain_blocks.append(ft.Text("(", size=18, color=ft.Colors.WHITE_54))
            domain_blocks.append(ft.Text("1 +", size=14, color=ft.Colors.WHITE_54))
            pct_domain = build_domain(percent_mods, "百分比加成", result.pct_sum, ModifierZone.PERCENT, True)
            if pct_domain: domain_blocks.append(pct_domain)
            domain_blocks.append(ft.Text(")", size=18, color=ft.Colors.WHITE_54))

        # 4. 固定值域
        if flat_mods and abs(result.flat_sum) > 0.01:
            domain_blocks.append(ft.Text("+", size=16, color=ft.Colors.WHITE_54))
            flat_domain = build_domain(flat_mods, "固定值加成", result.flat_sum, ModifierZone.FLAT, is_pct)
            if flat_domain: domain_blocks.append(flat_domain)

    elif result.paradigm == "pct_additive":
        # ===== 百分比累加型公式: Base + PctSum =====

        # 1. 静态基础值
        domain_blocks.append(ft.Column([
            ft.Container(
                content=ft.Text(f"{result.base:.1f}{suffix}", size=14, color=ZONE_COLORS[ModifierZone.BASE], weight=ft.FontWeight.BOLD),
                padding=ft.Padding(left=4, right=4, top=2, bottom=2)
            ),
            ft.Text("基础值", size=10, color=ft.Colors.WHITE_38)
        ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True))

        # 2. 百分比加成域
        if percent_mods and abs(result.pct_sum) > 0.01:
            domain_blocks.append(ft.Text("+", size=16, color=ft.Colors.WHITE_54))
            pct_domain = build_domain(percent_mods, "百分比加成", result.pct_sum, ModifierZone.PERCENT, True)
            if pct_domain: domain_blocks.append(pct_domain)

    else:  # additive
        # ===== 纯累加型公式: Base + FlatSum =====

        # 1. 静态基础值
        domain_blocks.append(ft.Column([
            ft.Container(
                content=ft.Text(f"{result.base:.1f}{suffix}", size=14, color=ZONE_COLORS[ModifierZone.BASE], weight=ft.FontWeight.BOLD),
                padding=ft.Padding(left=4, right=4, top=2, bottom=2)
            ),
            ft.Text("基础值", size=10, color=ft.Colors.WHITE_38)
        ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True))

        # 2. 固定值加成域
        all_mods = flat_mods + percent_mods
        if all_mods and abs(result.flat_sum) > 0.01:
            domain_blocks.append(ft.Text("+", size=16, color=ft.Colors.WHITE_54))
            flat_domain = build_domain(all_mods[:8], "加成", result.flat_sum, ModifierZone.FLAT, is_pct)
            if flat_domain: domain_blocks.append(flat_domain)

    # 最终结果
    total_text = f"{result.total:.2f}{suffix}"
    domain_blocks.append(ft.Text("=", size=16, color=ft.Colors.WHITE_54))
    domain_blocks.append(ft.Row([
        ft.Column([
            ft.Text("最终结果:", size=10, color=ft.Colors.WHITE_54),
            ft.Text(total_text, size=18, color=ft.Colors.AMBER_400, weight=ft.FontWeight.BOLD),
        ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.START, tight=True)
    ], tight=True))

    return ft.Container(
        content=ft.Row(
            domain_blocks, 
            spacing=8, 
            vertical_alignment=ft.CrossAxisAlignment.CENTER, 
            wrap=True,
            alignment=ft.MainAxisAlignment.START,
        ),
        padding=ft.Padding.all(12),
        bgcolor=ft.Colors.BLACK_26,
        border_radius=12
    )


@ft.component
def ZonedModifierCard(
    modifier: ZonedModifier,
    is_highlighted: bool = False
) -> ft.Control:
    """
    带乘区标记的修饰符卡片

    布局:
    ┌─────────────────────────┐
    │ █ 名称                  │  <- 左侧竖条颜色对应乘区
    │   +值                   │
    └─────────────────────────┘

    Args:
        modifier: 修饰符数据
        is_highlighted: 是否高亮
    """
    # 确定颜色
    zone_color = ZONE_COLORS.get(modifier.zone, ft.Colors.WHITE)

    # 格式化值显示
    is_negative = modifier.value < 0
    value_color = NEGATIVE_COLOR if is_negative else zone_color
    value_sign = "-" if is_negative else "+"
    value_abs = abs(modifier.value)

    # 判断是否为百分比值
    is_pct = "%" in modifier.stat
    value_text = f"{value_sign}{value_abs:.1f}{'%' if is_pct else ''}"

    # 高亮边框
    border = ft.Border.all(2, zone_color) if is_highlighted else None

    return ft.Container(
        content=ft.Row([
            # 左侧乘区指示条
            ft.Container(
                width=4,
                height=40,
                bgcolor=zone_color,
                border_radius=ft.BorderRadius(top_left=4, top_right=0, bottom_left=4, bottom_right=0)
            ),
            # 内容区域
            ft.Column([
                ft.Text(
                    modifier.name,
                    size=10,
                    weight=ft.FontWeight.W_600,
                    no_wrap=True,
                    overflow=ft.TextOverflow.ELLIPSIS,
                    color=ft.Colors.WHITE if is_highlighted else ft.Colors.WHITE,
                    expand=True
                ),
                ft.Text(
                    value_text,
                    size=12,
                    color=value_color,
                    weight=ft.FontWeight.BOLD
                ),
            ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.START, expand=True),
        ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.Padding(left=0, right=8, top=4, bottom=4),
        bgcolor=ft.Colors.WHITE_12 if is_highlighted else ft.Colors.WHITE_10,
        border_radius=6,
        width=110,
        border=border
    )


@ft.component
def ModifierCardGrid(
    modifiers: list[ZonedModifier],
    highlight_zone: ModifierZone | None = None,
    empty_text: str = "无加成来源"
) -> ft.Control:
    """
    [V9.9] 修饰符卡片网格 - 支持来源分组
    """
    if not modifiers:
        return ft.Container(
            content=ft.Text(empty_text, color=ft.Colors.WHITE_24, italic=True, size=10),
            padding=ft.Padding.all(12),
            alignment=ft.Alignment.CENTER
        )

    # 按 source_type 分组
    grouped: dict[str, list[ZonedModifier]] = {}
    for m in modifiers:
        stype = m.source_type or "Other"
        if stype not in grouped:
            grouped[stype] = []
        grouped[stype].append(m)

    sections: list[ft.Control] = []
    
    # 按照优先级排序来源
    source_order = ["Weapon", "Artifact", "Talent", "Resonance", "Other"]
    
    for stype in source_order:
        if stype not in grouped:
            continue
        
        mods = grouped[stype]
        icon = ft.Icons.SETTINGS
        if stype == "Weapon": icon = ft.Icons.SAFETY_CHECK
        elif stype == "Artifact": icon = ft.Icons.AUTO_AWESOME
        elif stype == "Talent": icon = ft.Icons.SKATEBOARDING
        elif stype == "Resonance": icon = ft.Icons.GROUPS

        sections.append(
            ft.Column([
                ft.Row([
                    ft.Icon(icon, size=12, color=ft.Colors.WHITE_38),
                    ft.Text(stype.upper(), size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE_38),
                ], spacing=4),
                ft.Row(
                    [ZonedModifierCard(m, highlight_zone == m.zone) for m in mods],
                    spacing=8,
                    wrap=True
                )
            ], spacing=6)
        )

    return ft.Column(
        sections,
        spacing=12,
        scroll=ft.ScrollMode.ADAPTIVE,
        expand=True
    )
