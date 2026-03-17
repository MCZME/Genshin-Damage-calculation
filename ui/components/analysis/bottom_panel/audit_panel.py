"""[V11.0] 审计面板组件

提供伤害审计详情界面的组件。

[V12.0] 支持两种伤害路径：
- 常规伤害路径：6 桶模型
- 剧变反应路径：4 桶模型
"""
import flet as ft
from collections.abc import Callable

from ui.theme import GenshinTheme
from core.persistence.processors.audit import AuditProcessor
from core.persistence.processors.audit.types import DamageType
from .constants import BUCKET_COLORS, NORMAL_BUCKET_CONFIGS, TRANSFORMATIVE_BUCKET_CONFIGS
from .utils import format_val
from .multiplier_formulas import build_formula, build_transformative_formula


@ft.component
def DomainValue(
    value: float,
    domain_key: str,
    bucket_key: str,
    bucket_color: str,
    is_selected: bool,
    on_click: Callable[[str, str], None],
    show_sign: bool = True,
    format_spec: str = ".1f",
    suffix: str = ""
):
    """可点击的域值显示

    Args:
        value: 域值
        domain_key: 域键名
        bucket_key: 所属乘区键
        bucket_color: 乘区颜色
        is_selected: 是否选中
        on_click: 点击回调，接收 (bucket_key, domain_key)
        show_sign: 是否显示正号
        format_spec: 数值格式
        suffix: 后缀
    """
    formatted = f"{value:{format_spec}}{suffix}"
    text = f"+{formatted}" if show_sign and value >= 0 else formatted

    return ft.GestureDetector(
        content=ft.Container(
            content=ft.Text(
                text,
                size=11,
                color=bucket_color if is_selected else ft.Colors.WHITE_70,
                weight=ft.FontWeight.BOLD if is_selected else ft.FontWeight.NORMAL,
            ),
            bgcolor=ft.Colors.with_opacity(0.2, bucket_color) if is_selected else ft.Colors.with_opacity(0.05, bucket_color),
            border_radius=4,
            padding=ft.Padding(left=4, right=4, top=2, bottom=2),
        ),
        on_tap=lambda _: on_click(bucket_key, domain_key),
    )


@ft.component
def MultiplierCard(
    bucket_key: str,
    bucket_label: str,
    bucket_data: dict,
    bucket_color: str,
    is_selected: bool,
    selected_domain: str | None,
    on_domain_click: Callable[[str, str], None],
    damage_type: DamageType = DamageType.NORMAL
):
    """[V12.0] 乘区卡片 - 两行结构（公式 + 总计）

    适配脱水存储机制：
    - CRIT 区：显示暴击乘数值（1 + CD% 或 1.00x）
    - MULTIPLIER 区：显示技能倍率 x (1 + 独立乘区%) + 倍率加值% + 固定值
    - DEFENSE/RESISTANCE 区：显示系数值及分量

    [V12.0] 支持伤害类型感知：
    - NORMAL: 使用常规伤害公式构建器
    - TRANSFORMATIVE: 使用剧变反应公式构建器

    注意：乘区卡片整体不可点击，只有域值（DomainValue）可点击。

    Args:
        bucket_key: 乘区键
        bucket_label: 乘区标签
        bucket_data: 乘区数据
        bucket_color: 乘区颜色（从外部传入）
        is_selected: 是否选中
        selected_domain: 选中的域
        on_domain_click: 域点击回调，接收 (bucket_key, domain_key)
        damage_type: 伤害类型（常规/剧变）
    """
    # 根据伤害类型选择公式构建器
    if damage_type == DamageType.TRANSFORMATIVE:
        result = build_transformative_formula(
            bucket_key=bucket_key,
            bucket_data=bucket_data,
            bucket_color=bucket_color,
            selected_domain=selected_domain,
            on_domain_click=on_domain_click,
        )
    else:
        result = build_formula(
            bucket_key=bucket_key,
            bucket_data=bucket_data,
            bucket_color=bucket_color,
            selected_domain=selected_domain,
            on_domain_click=on_domain_click,
        )
    formula_parts = result.formula_parts
    total_text = result.total_text
    total_color = result.total_color or bucket_color  # 使用覆盖颜色或默认桶颜色

    # [V2.5.6] 乘区卡片整体不可点击，只有域值可点击
    return ft.Container(
        content=ft.Column([
            # 标签
            ft.Text(
                bucket_label,
                size=10,
                color=ft.Colors.WHITE_54,
                text_align=ft.TextAlign.CENTER,
            ),
            # 公式行
            ft.Row(
                formula_parts,
                spacing=1,
                alignment=ft.MainAxisAlignment.CENTER,
                wrap=False,
            ),
            # 分割线 - 使用 Container 确保在自适应宽度下显示
            ft.Container(height=1, bgcolor=ft.Colors.WHITE_12),
            # 总计
            ft.Text(
                total_text,
                size=12,
                weight=ft.FontWeight.BOLD,
                color=total_color,
                text_align=ft.TextAlign.CENTER,
            ),
        ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.Padding.all(8),
        bgcolor=ft.Colors.with_opacity(0.15, bucket_color) if is_selected else ft.Colors.WHITE_10,
        border_radius=8,
        border=ft.Border.all(2, bucket_color) if is_selected else ft.Border.all(1, ft.Colors.WHITE_12),
        animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
    )


@ft.component
def DamageResultCard(damage_value: float, element: str = "Neutral"):
    """伤害结果卡片 - 显示最终伤害值

    Args:
        damage_value: 伤害值
        element: 元素类型（用于颜色）
    """
    elem_color = GenshinTheme.get_element_color(element)

    return ft.Container(
        content=ft.Column([
            ft.Text(
                "伤害",
                size=10,
                color=ft.Colors.WHITE_54,
                text_align=ft.TextAlign.CENTER,
            ),
            # 分割线
            ft.Container(height=1, bgcolor=ft.Colors.WHITE_12),
            ft.Text(
                format_val(damage_value),
                size=12,
                weight=ft.FontWeight.BOLD,
                color=elem_color,
                text_align=ft.TextAlign.CENTER,
            ),
        ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        width=80,
        padding=ft.Padding.all(8),
        bgcolor=ft.Colors.with_opacity(0.15, elem_color),
        border_radius=8,
        border=ft.Border.all(2, elem_color),
    )


@ft.component
def DamageChainRow(
    active_bucket: str | None,
    selected_domain: str | None,
    buckets_data: dict,
    damage_value: float = 0,
    element: str = "Neutral",
    damage_type: DamageType = DamageType.NORMAL,
    on_domain_click: Callable[[str, str], None] = lambda b, d: None
):
    """[V12.0] 伤害链行 - 根据伤害类型显示不同的桶结构

    常规伤害：7 个乘区卡片横向排列，用 × 连接
    剧变反应：4 个桶卡片横向排列，用 × 连接

    Args:
        active_bucket: 当前激活的乘区
        selected_domain: 选中的域
        buckets_data: 乘区数据
        damage_value: 最终伤害值
        element: 元素类型
        damage_type: 伤害类型（常规/剧变）
        on_domain_click: 域点击回调，接收 (bucket_key, domain_key)
    """
    cards: list[ft.Control] = []

    # 根据伤害类型选择桶配置
    if damage_type == DamageType.TRANSFORMATIVE:
        bucket_configs = TRANSFORMATIVE_BUCKET_CONFIGS
    else:
        bucket_configs = NORMAL_BUCKET_CONFIGS

    for i, (bucket_key, bucket_label, data_key) in enumerate(bucket_configs):
        bucket_data = buckets_data.get(data_key, {})
        bucket_color = BUCKET_COLORS.get(bucket_key, ft.Colors.WHITE)

        card = MultiplierCard(
            bucket_key=bucket_key,
            bucket_label=bucket_label,
            bucket_data=bucket_data,
            bucket_color=bucket_color,
            is_selected=active_bucket == bucket_key,
            selected_domain=selected_domain,
            on_domain_click=on_domain_click,
            damage_type=damage_type,
        )
        cards.append(card)

        # 添加连接符（除了最后一个乘区）
        if i < len(bucket_configs) - 1:
            cards.append(ft.Text("×", size=16, color=ft.Colors.WHITE_24, weight=ft.FontWeight.BOLD))

    # 添加等号和伤害结果卡片
    cards.append(ft.Text("=", size=16, color=ft.Colors.WHITE_24, weight=ft.FontWeight.BOLD))
    cards.append(DamageResultCard(damage_value, element))

    return ft.Container(
        content=ft.Row(
            cards,
            spacing=4,
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            wrap=False,
            scroll=ft.ScrollMode.ADAPTIVE,
        ),
        alignment=ft.Alignment.CENTER,
        padding=ft.Padding(left=8, right=8, top=8, bottom=4),
    )


@ft.component
def ModifierCard(modifier: dict, bucket_color: str):
    """修饰符卡片

    Args:
        modifier: 修饰符数据
        bucket_color: 乘区颜色
    """
    stat = modifier.get('stat', '')
    value = modifier.get('value', 0)

    # 判断是否为百分比属性
    # 1. stat 包含 '%' 字符
    # 2. stat 包含百分比属性关键词（加成、暴击、率等）
    pct_keywords = ('加成', '暴击', '率', '减抗', '减防', '穿透', '无视')
    is_pct = '%' in stat or stat.endswith(pct_keywords)

    value_text = f"+{value:.1f}%" if is_pct else f"+{value:.0f}"

    return ft.Container(
        content=ft.Column([
            ft.Text(
                value_text,
                size=12,
                weight=ft.FontWeight.BOLD,
                color=bucket_color,
            ),
            ft.Text(
                modifier.get('source', ''),
                size=10,
                color=ft.Colors.WHITE_54,
                no_wrap=True,
                overflow=ft.TextOverflow.ELLIPSIS,
            ),
        ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        width=80,
        padding=ft.Padding.all(8),
        bgcolor=ft.Colors.WHITE_10,
        border_radius=6,
    )


@ft.component
def DomainDetailSection(
    active_bucket: str | None,
    selected_domain: str | None,
    buckets_data: dict
):
    """域详情区 - 显示选中域的修饰符卡片

    [V13.0] 适配新的 6 桶模型：
    - CORE: 支持属性特定域（pct:攻击力）、技能倍率域（skill_mult:攻击力）、独立乘区等

    Args:
        active_bucket: 当前激活的乘区
        selected_domain: 选中的域
        buckets_data: 乘区数据
    """
    if not active_bucket:
        return ft.Container()

    # 获取当前乘区的数据键
    bucket_data_map = {key: data_key for key, _, data_key in NORMAL_BUCKET_CONFIGS}
    data_key = bucket_data_map.get(active_bucket, "core_dmg")
    bucket_color = BUCKET_COLORS.get(active_bucket, ft.Colors.WHITE)

    # 获取步骤列表
    steps = buckets_data.get(data_key, {}).get('steps', [])

    # [V13.0] CORE 区处理
    if active_bucket == "CORE":
        scaling_info = buckets_data.get(data_key, {}).get('scaling_info', [])

        # 处理属性特定域（如 "pct:攻击力", "flat:防御力"）
        if selected_domain and ":" in selected_domain:
            domain_type, attr_name = selected_domain.split(":", 1)

            if domain_type == "pct":
                # 百分比加成
                attr_info = next((i for i in scaling_info if i.get('attr_name') == attr_name), None)
                if attr_info:
                    modifiers = [
                        {"stat": f"{attr_name}%", "value": m.get("value", 0.0), "source": m.get("name", "未知来源")}
                        for m in attr_info.get('pct_modifiers', [])
                    ]
                else:
                    modifiers = []
                domain_label = f"{attr_name}百分比加成"

            elif domain_type == "flat":
                # 固定值加成
                attr_info = next((i for i in scaling_info if i.get('attr_name') == attr_name), None)
                if attr_info:
                    modifiers = [
                        {"stat": f"固定{attr_name}", "value": m.get("value", 0.0), "source": m.get("name", "未知来源")}
                        for m in attr_info.get('flat_modifiers', [])
                    ]
                else:
                    modifiers = []
                domain_label = f"{attr_name}固定值加成"

            elif domain_type == "skill_mult":
                # 技能倍率
                modifiers = [
                    s for s in steps
                    if s.get("stat", "").endswith("技能倍率%") and attr_name in s.get("stat", "")
                ]
                domain_label = f"{attr_name}倍率"

            else:
                modifiers = steps
                domain_label = "全部来源"

        elif selected_domain == "skill_mult":
            # 所有技能倍率
            modifiers = [s for s in steps if s.get("stat", "").endswith("技能倍率%") or s.get("stat") == "技能倍率%"]
            domain_label = "技能倍率"

        elif selected_domain == "independent":
            modifiers = [s for s in steps if s.get("stat") == "独立乘区%"]
            domain_label = "独立乘区"

        elif selected_domain == "bonus_pct":
            modifiers = [s for s in steps if s.get("stat") == "倍率加值%"]
            domain_label = "倍率加值"

        elif selected_domain == "flat":
            modifiers = [s for s in steps if s.get("stat") == "固定伤害值加成"]
            domain_label = "固定值加成"

        elif selected_domain == "pct":
            # 所有百分比加成
            modifiers = [s for s in steps if s.get('op') == 'PCT']
            domain_label = "百分比加成"

        else:
            modifiers = steps
            domain_label = "全部来源"

    else:
        # [V13.0] BONUS 和 CRIT 区处理
        if active_bucket == "BONUS":
            if selected_domain == "bonus_pct":
                # [V14.0] 优先从 modifiers 字段获取，回退到 steps 过滤
                modifiers = buckets_data.get(data_key, {}).get('modifiers', [])
                if not modifiers:
                    # 从 steps 中过滤增伤相关
                    modifiers = [s for s in steps if "伤害加成" in s.get("stat", "")]
                if not modifiers:
                    modifiers = [{"stat": "伤害加成", "value": 0.0, "source": "面板聚合值（含基础+装备+天赋）"}]
                domain_label = "增伤来源"
            else:
                modifiers = steps
                domain_label = "全部来源"

        elif active_bucket == "CRIT":
            # [V14.2] CRIT 区支持暴击率和暴击伤害分开展示
            if selected_domain == "crit_rate":
                # 显示暴击率来源
                modifiers = buckets_data.get(data_key, {}).get('crit_rate_modifiers', [])
                if not modifiers:
                    modifiers = [s for s in steps if "暴击率" in s.get("stat", "")]
                if not modifiers:
                    modifiers = [{"stat": "暴击率", "value": 0.0, "source": "面板聚合值（含基础+装备+天赋）"}]
                domain_label = "暴击率来源"
            else:
                # 显示暴击伤害来源（仅暴击伤害，排除暴击率）
                modifiers = buckets_data.get(data_key, {}).get('modifiers', [])
                if not modifiers:
                    # 从 steps 中过滤暴击伤害（排除暴击率）
                    modifiers = [s for s in steps if "暴击伤害" in s.get("stat", "")]
                if not modifiers:
                    modifiers = [{"stat": "暴击伤害", "value": 0.0, "source": "面板聚合值（含基础+装备+天赋）"}]
                domain_label = "暴击伤害来源"

        elif active_bucket == "REACT":
            # [V14.2] REACT 区专属处理
            if selected_domain == "em_bonus":
                # 显示精通加成来源
                modifiers = [s for s in steps if s.get("source") == "[精通转化]"]
                if not modifiers:
                    modifiers = [s for s in steps if "精通" in s.get("source", "")]
                if not modifiers:
                    modifiers = [{"stat": "精通转化", "value": 0.0, "source": "无精通加成"}]
                domain_label = "精通转化加成"
            elif selected_domain == "other_bonus":
                # 显示其他加成来源
                modifiers = [s for s in steps if s["stat"] == "反应加成系数" and s.get("source") != "[精通转化]"]
                domain_label = "反应加成来源"
            elif selected_domain == "reaction_base":
                # 显示反应基础倍率来源
                modifiers = [s for s in steps if s["stat"] == "反应基础倍率"]
                domain_label = "反应类型"
            else:
                modifiers = steps
                domain_label = "全部来源"

        else:
            # 其他乘区使用原有逻辑
            domain_values = AuditProcessor.calculate_domains(steps)

            if selected_domain == "domain1":
                modifiers = domain_values.domain1_modifiers
                domain_label = "固定值加成"
            elif selected_domain == "domain2":
                modifiers = domain_values.domain2_modifiers
                domain_label = "百分比加成"
            else:
                modifiers = steps
                domain_label = "全部来源"

    if not modifiers:
        return ft.Container()

    # 构建修饰符卡片行
    modifier_cards = ft.Row(
        [
            ModifierCard(modifier=mod, bucket_color=bucket_color)
            for mod in modifiers[:10]
        ],
        spacing=6,
        scroll=ft.ScrollMode.ADAPTIVE,
    )

    return ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.ACCOUNT_TREE_ROUNDED, size=14, color=ft.Colors.WHITE_54),
                ft.Text(f"{domain_label}", size=11, color=ft.Colors.WHITE_54),
                ft.Text(f"({len(modifiers)} 项)", size=10, color=ft.Colors.WHITE_38),
            ], spacing=6),
            modifier_cards,
        ], spacing=6),
        padding=ft.Padding(left=16, right=16, top=4, bottom=8),
        bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.WHITE),
        border_radius=8,
        margin=ft.Margin.only(left=16, right=16, top=4, bottom=4),
    )


@ft.component
def AuditPanel(
    event: dict | None,
    active_bucket: str | None,
    selected_domain: str | None,
    buckets_data: dict,
    on_domain_click: Callable[[str, str], None],
    on_back: Callable[[], None],
    on_close: Callable[[], None] | None,
    damage_type: DamageType = DamageType.NORMAL
):
    """[V12.0] 审计面板 - 两行布局（伤害链 + 域详情）

    支持两种伤害路径：
    - 常规伤害：7 桶模型
    - 剧变反应：4 桶模型

    Args:
        event: 当前事件数据
        active_bucket: 当前激活的乘区
        selected_domain: 选中的域
        buckets_data: 乘区数据
        damage_type: 伤害类型（常规/剧变）
        on_domain_click: 域点击回调，接收 (bucket_key, domain_key)
        on_back: 返回回调
        on_close: 关闭回调
    """
    # 头部信息
    if event:
        elem_color = GenshinTheme.get_element_color(event.get('element', 'Neutral'))
        # [V12.0] 显示伤害类型标签
        type_label = "剧变" if damage_type == DamageType.TRANSFORMATIVE else "常规"
        header_content = ft.Row([
            ft.IconButton(
                icon=ft.Icons.ARROW_BACK_ROUNDED,
                icon_size=18,
                icon_color=ft.Colors.WHITE_70,
                on_click=lambda _: on_back(),
                tooltip="返回选择",
                style=ft.ButtonStyle(padding=ft.Padding.all(4)),
            ),
            ft.Text(
                event.get('source', '未知来源'),
                size=14,
                weight=ft.FontWeight.W_600,
                color=ft.Colors.WHITE,
            ),
            ft.Container(
                width=6,
                height=6,
                bgcolor=elem_color,
                border_radius=3,
            ),
            ft.Text(
                f"[{type_label}] #{event.get('event_id')} F{event.get('frame')}",
                size=11,
                color=ft.Colors.WHITE_54,
                font_family="Consolas",
            ),
            ft.Container(expand=True),
            ft.Text(
                format_val(event.get('dmg', 0)),
                size=18,
                weight=ft.FontWeight.W_900,
                color=elem_color,
            ),
        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER)
    else:
        header_content = ft.Row([
            ft.IconButton(
                icon=ft.Icons.ARROW_BACK_ROUNDED,
                icon_size=18,
                icon_color=ft.Colors.WHITE_70,
                on_click=lambda _: on_back(),
                tooltip="返回选择",
                style=ft.ButtonStyle(padding=ft.Padding.all(4)),
            ),
            ft.Text("伤害审计", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE),
            ft.Container(expand=True),
        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER)

    return ft.Column([
        # 头部
        ft.Container(
            content=header_content,
            padding=ft.Padding(left=4, top=8, right=4, bottom=4),
        ),
        # 第一行：伤害链
        DamageChainRow(
            active_bucket=active_bucket,
            selected_domain=selected_domain,
            buckets_data=buckets_data,
            damage_value=event.get('dmg', 0) if event else 0,
            element=event.get('element', 'Neutral') if event else 'Neutral',
            damage_type=damage_type,
            on_domain_click=on_domain_click,
        ),
        # 第二行：域详情
        DomainDetailSection(
            active_bucket=active_bucket,
            selected_domain=selected_domain,
            buckets_data=buckets_data,
        ),
        # 占位（可扩展显示更多详情）
        ft.Container(expand=True),
    ], spacing=0, expand=True)
