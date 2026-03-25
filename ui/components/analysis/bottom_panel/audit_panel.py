"""[V20.0] 审计面板组件

提供伤害审计详情界面的组件。

[V20.0] 纯数据设计：
- MultiplierCard 根据 FormulaPartData 数据创建组件
- ViewModel 只存储数据，不存储组件
- 组件在渲染时根据数据和回调创建 Flet 控件
"""
import flet as ft
from collections.abc import Callable
from typing import TYPE_CHECKING

from ui.theme import GenshinTheme
from core.persistence.processors.audit.types import DamageType

if TYPE_CHECKING:
    from ui.view_models.analysis.bottom_panel.audit_panel_vm import AuditPanelViewModel
    from ui.view_models.analysis.bottom_panel.damage_chain_vm import (
        MultiplierCardViewModel,
        DamageResultCardViewModel,
        DamageChainRowViewModel,
    )
    from ui.view_models.analysis.bottom_panel.domain_detail_vm import (
        ModifierCardViewModel,
        DomainDetailSectionViewModel,
    )

from .utils import format_val


# ============================================================
# 公式渲染辅助函数
# ============================================================


def _resolve_color(color_str: str) -> str:
    """将颜色字符串解析为 Flet 颜色

    Args:
        color_str: 颜色字符串，可能是：
            - 标准 Flet 颜色名（如 "white54"）
            - 十六进制颜色（如 "#FFA726"）
            - bucket_color（直接传递）

    Returns:
        Flet 可用的颜色值
    """
    # Flet 颜色映射表（常用颜色）
    color_map = {
        "white54": ft.Colors.WHITE_54,
        "white70": ft.Colors.WHITE_70,
        "white38": ft.Colors.WHITE_38,
        "white24": ft.Colors.WHITE_24,
        "amber400": ft.Colors.AMBER_400,
    }

    # 检查是否是预定义颜色
    if color_str in color_map:
        return color_map[color_str]

    # 直接返回（十六进制或其他格式）
    return color_str


def render_formula_part(
    part,  # FormulaPartData (TextPart | DomainValuePart)
    selected_domain: str | None,
    active_bucket: str | None,
    on_domain_click: Callable[[str, str], None] | None,
) -> ft.Control:
    """将公式部分数据渲染为 Flet 控件

    Args:
        part: 公式部分数据（TextPart 或 DomainValuePart）
        selected_domain: 选中的域
        active_bucket: 当前激活的乘区
        on_domain_click: 域点击回调

    Returns:
        Flet 控件
    """
    from ui.components.analysis.bottom_panel.multiplier_formulas import TextPart, DomainValuePart

    if isinstance(part, TextPart):
        # 文本部分：直接创建 Text 控件
        return ft.Text(
            part.content,
            size=part.size,
            color=_resolve_color(part.color),
        )

    elif isinstance(part, DomainValuePart):
        # 域值部分：创建可点击的域值控件
        formatted = f"{part.value:{part.format_spec}}"
        text = f"+{formatted}" if part.show_sign and part.value >= 0 else formatted

        # 选中判断：必须同时匹配 bucket 和 domain
        is_selected = active_bucket == part.bucket_key and selected_domain == part.domain_key

        def safe_on_tap(e):
            """安全点击处理，防止组件已从页面移除时的 RuntimeError"""
            try:
                if on_domain_click:
                    on_domain_click(part.bucket_key, part.domain_key)
            except (RuntimeError, AttributeError):
                pass

        return ft.GestureDetector(
            content=ft.Container(
                content=ft.Text(
                    text,
                    size=11,
                    color=part.bucket_color if is_selected else ft.Colors.WHITE_70,
                    weight=ft.FontWeight.BOLD if is_selected else ft.FontWeight.NORMAL,
                ),
                bgcolor=ft.Colors.with_opacity(0.2, part.bucket_color)
                if is_selected
                else ft.Colors.with_opacity(0.05, part.bucket_color),
                border_radius=4,
                padding=ft.Padding(left=4, right=4, top=2, bottom=2),
            ),
            on_tap=safe_on_tap,
        )

    else:
        # 未知类型，返回空容器
        return ft.Container()


def render_formula_parts(
    parts: list,  # list[FormulaPartData]
    selected_domain: str | None,
    active_bucket: str | None,
    on_domain_click: Callable[[str, str], None] | None,
) -> list[ft.Control]:
    """将公式部分数据列表渲染为 Flet 控件列表

    Args:
        parts: 公式部分数据列表
        selected_domain: 选中的域
        active_bucket: 当前激活的乘区
        on_domain_click: 域点击回调

    Returns:
        Flet 控件列表
    """
    return [
        render_formula_part(part, selected_domain, active_bucket, on_domain_click)
        for part in parts
    ]


# ============================================================
# 组件定义
# ============================================================


@ft.component
def MultiplierCard(vm: 'MultiplierCardViewModel'):
    """[V20.0] 乘区卡片 - 两行结构（公式 + 总计）

    使用 MultiplierCardViewModel 进行数据绑定。
    [V20.0] formula_parts 是数据结构，组件渲染时转换为控件

    Args:
        vm: 乘区卡片 ViewModel
    """
    # 将数据转换为控件
    formula_controls = render_formula_parts(
        parts=vm.formula_parts,
        selected_domain=vm.selected_domain,
        active_bucket=vm.active_bucket,
        on_domain_click=vm.on_domain_click,
    )

    # 构建列内容
    column_content = [
        # 标签
        ft.Text(
            vm.bucket_label,
            size=10,
            color=ft.Colors.WHITE_54,
            text_align=ft.TextAlign.CENTER,
        ),
        # 公式行
        ft.Row(
            formula_controls,
            spacing=1,
            alignment=ft.MainAxisAlignment.CENTER,
            wrap=False,
        ),
    ]

    # 如果有第二行公式，添加分割线和第二行
    if vm.formula_parts_line2:
        formula_controls_line2 = render_formula_parts(
            parts=vm.formula_parts_line2,
            selected_domain=vm.selected_domain,
            active_bucket=vm.active_bucket,
            on_domain_click=vm.on_domain_click,
        )
        column_content.extend([
            # 分数线
            ft.Container(height=1, bgcolor=ft.Colors.WHITE_38, width=60),
            ft.Row(
                formula_controls_line2,
                spacing=1,
                alignment=ft.MainAxisAlignment.CENTER,
                wrap=False,
            ),
        ])

    # 添加分割线和总计
    column_content.extend([
        # 分割线
        ft.Container(height=1, bgcolor=ft.Colors.WHITE_12),
        # 总计
        ft.Text(
            vm.total_text,
            size=12,
            weight=ft.FontWeight.BOLD,
            color=_resolve_color(vm.total_color),
            text_align=ft.TextAlign.CENTER,
        ),
    ])

    return ft.Container(
        content=ft.Column(column_content, spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.Padding.all(8),
        bgcolor=ft.Colors.with_opacity(0.15, vm.bucket_color) if vm.is_selected else ft.Colors.WHITE_10,
        border_radius=8,
        border=ft.Border.all(2, vm.bucket_color) if vm.is_selected else ft.Border.all(1, ft.Colors.WHITE_12),
        animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
    )


@ft.component
def DamageResultCard(vm: 'DamageResultCardViewModel'):
    """[V17.0] 伤害结果卡片 - 显示最终伤害值

    使用 DamageResultCardViewModel 进行数据绑定。

    Args:
        vm: 伤害结果卡片 ViewModel
    """
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
                format_val(vm.damage_value),
                size=12,
                weight=ft.FontWeight.BOLD,
                color=vm.element_color,
                text_align=ft.TextAlign.CENTER,
            ),
        ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        width=80,
        padding=ft.Padding.all(8),
        bgcolor=ft.Colors.with_opacity(0.15, vm.element_color),
        border_radius=8,
        border=ft.Border.all(2, vm.element_color),
    )


@ft.component
def DamageChainRow(vm: 'DamageChainRowViewModel'):
    """[V17.0] 伤害链行 - 根据伤害类型显示不同的桶结构

    使用 DamageChainRowViewModel 进行数据绑定。
    multiplier_cards 由 ViewModel 的派生属性提供。

    Args:
        vm: 伤害链行 ViewModel
    """
    cards: list[ft.Control] = []

    # 从 ViewModel 获取乘区卡片列表
    for i, card_vm in enumerate(vm.multiplier_cards):
        cards.append(MultiplierCard(vm=card_vm))

        # 添加连接符（除了最后一个乘区）
        if i < len(vm.multiplier_cards) - 1:
            cards.append(ft.Text("×", size=16, color=ft.Colors.WHITE_24, weight=ft.FontWeight.BOLD))

    # 添加等号和伤害结果卡片
    cards.append(ft.Text("=", size=16, color=ft.Colors.WHITE_24, weight=ft.FontWeight.BOLD))
    if vm.damage_result:
        cards.append(DamageResultCard(vm=vm.damage_result))

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
def ModifierCard(vm: 'ModifierCardViewModel'):
    """[V17.0] 修饰符卡片

    使用 ModifierCardViewModel 进行数据绑定。

    Args:
        vm: 修饰符卡片 ViewModel
    """
    return ft.Container(
        content=ft.Column([
            ft.Text(
                vm.display_text,
                size=12,
                weight=ft.FontWeight.BOLD,
                color=vm.bucket_color,
            ),
            ft.Text(
                vm.source,
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
def DomainDetailSection(vm: 'DomainDetailSectionViewModel'):
    """[V17.0] 域详情区 - 显示选中域的修饰符卡片

    使用 DomainDetailSectionViewModel 进行数据绑定。
    modifier_cards 由 ViewModel 的派生属性提供。

    Args:
        vm: 域详情区 ViewModel
    """
    if not vm.has_content:
        return ft.Container()

    # 构建修饰符卡片行
    modifier_cards_row = ft.Row(
        [ModifierCard(vm=card_vm) for card_vm in vm.modifier_cards],
        spacing=6,
        scroll=ft.ScrollMode.ADAPTIVE,
    )

    return ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.ACCOUNT_TREE_ROUNDED, size=14, color=ft.Colors.WHITE_54),
                ft.Text(f"{vm.domain_label}", size=11, color=ft.Colors.WHITE_54),
                ft.Text(f"({vm.modifier_count} 项)", size=10, color=ft.Colors.WHITE_38),
            ], spacing=6),
            modifier_cards_row,
        ], spacing=6),
        padding=ft.Padding(left=16, right=16, top=4, bottom=8),
        bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.WHITE),
        border_radius=8,
        margin=ft.Margin.only(left=16, right=16, top=4, bottom=4),
    )


@ft.component
def AuditPanelHeader(
    event: dict | None,
    damage_type: DamageType,
    on_back: Callable[[], None]
):
    """审计面板头部

    Args:
        event: 事件数据
        damage_type: 伤害类型
        on_back: 返回回调
    """
    if event:
        elem_color = GenshinTheme.get_element_color(event.get('element', 'Neutral'))
        # 显示伤害类型标签
        type_label = "剧变" if damage_type == DamageType.TRANSFORMATIVE else "常规"
        return ft.Row(controls=[
            ft.IconButton(
                icon=ft.Icons.ARROW_BACK_ROUNDED,
                icon_size=18,
                icon_color=ft.Colors.WHITE_70,
                on_click=lambda _: on_back(),
                tooltip="返回选择",
                style=ft.ButtonStyle(padding=ft.Padding.all(4)),
            ),
            # 角色名称 + 伤害名称（左侧，同一行）
            ft.Row([
                ft.Text(
                    event.get('source', '未知来源'),
                    size=13,
                    color=ft.Colors.WHITE_70,
                    no_wrap=True,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                ft.Text(
                    event.get('name', '未知伤害'),
                    size=13,
                    weight=ft.FontWeight.W_600,
                    color=ft.Colors.WHITE,
                    no_wrap=True,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            # 填充空间
            ft.Container(expand=True),
            # 右侧：元素图标 + 类型标签 + 事件ID
            ft.Row([
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
            ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER)
    else:
        return ft.Row([
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


@ft.component
def AuditPanel(
    vm: 'AuditPanelViewModel',
    on_back: Callable[[], None],
    on_close: Callable[[], None] | None
):
    """[V17.0] 审计面板 - 两行布局（伤害链 + 域详情）

    使用 AuditPanelViewModel 的嵌套 ViewModel：
    - damage_chain: DamageChainRowViewModel
    - domain_detail: DomainDetailSectionViewModel

    支持两种伤害路径：
    - 常规伤害：6 桶模型
    - 剧变反应：3 桶模型

    Args:
        vm: 审计面板 ViewModel
        on_back: 返回回调
        on_close: 关闭回调
    """
    # 从 VM 获取状态
    event = vm.event
    damage_type = vm.damage_type

    # 头部信息
    header_content = AuditPanelHeader(
        event=event,
        damage_type=damage_type,
        on_back=on_back,
    )

    # 伤害链行（使用嵌套 ViewModel）
    damage_chain_row = DamageChainRow(vm=vm.damage_chain) if vm.damage_chain else ft.Container()

    # 域详情区（使用嵌套 ViewModel）
    domain_detail_section = DomainDetailSection(vm=vm.domain_detail) if vm.domain_detail else ft.Container()

    return ft.Column([
        # 头部
        ft.Container(
            content=header_content,
            padding=ft.Padding(left=4, top=8, right=4, bottom=4),
        ),
        # 第一行：伤害链
        damage_chain_row,
        # 第二行：域详情
        domain_detail_section,
        # 占位（可扩展显示更多详情）
        ft.Container(expand=True),
    ], spacing=0, expand=True)
