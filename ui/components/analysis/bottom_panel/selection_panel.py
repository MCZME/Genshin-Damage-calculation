"""[V17.0] 选择面板组件

提供事件选择界面的组件。

重构说明：
- 使用 SelectionPanelViewModel 和 EventCardViewModel 进行数据绑定
- 组件消费 ViewModel，不直接消费字典数据
"""
import flet as ft
from typing import Callable, TYPE_CHECKING

from ui.view_models.analysis.bottom_panel.selection_vm import (
    EventCardViewModel,
    SelectionPanelViewModel,
)
from .utils import format_val

if TYPE_CHECKING:
    from ui.view_models.analysis.tile_vms.types import FrameRangeSelection


@ft.component
def EventCard(vm: EventCardViewModel, on_click: Callable[[EventCardViewModel], None]):
    """事件卡片 - 横向展示

    Args:
        vm: 事件卡片 ViewModel
        on_click: 点击回调
    """
    return ft.Container(
        content=ft.Column([
            # 角色名称（灰色小字）
            ft.Text(
                vm.source,
                size=9,
                color=ft.Colors.WHITE_54,
                no_wrap=True,
                overflow=ft.TextOverflow.ELLIPSIS,
                text_align=ft.TextAlign.CENTER,
            ),
            # 伤害名称（主标题）
            ft.Text(
                vm.name,
                size=11,
                weight=ft.FontWeight.W_600,
                color=ft.Colors.WHITE,
                no_wrap=True,
                overflow=ft.TextOverflow.ELLIPSIS,
                text_align=ft.TextAlign.CENTER,
            ),
            # 元素图标 + 伤害值
            ft.Row([
                ft.Container(
                    width=8,
                    height=8,
                    bgcolor=vm.element_color,
                    border_radius=4,
                ),
                ft.Text(
                    format_val(vm.damage),
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    color=vm.element_color,
                ),
            ], spacing=4, alignment=ft.MainAxisAlignment.CENTER),
            # 事件ID和帧
            ft.Text(
                f"#{vm.event_id} F{vm.frame}",
                size=9,
                color=ft.Colors.WHITE_38,
                font_family="Consolas",
                text_align=ft.TextAlign.CENTER,
            ),
        ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        width=110,
        padding=ft.Padding.all(8),
        bgcolor=ft.Colors.with_opacity(0.15, vm.element_color) if vm.is_selected else ft.Colors.WHITE_10,
        border_radius=8,
        border=ft.Border.all(2, vm.element_color) if vm.is_selected else ft.Border.all(1, ft.Colors.WHITE_12),
        on_click=lambda _: on_click(vm),
        animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
    )


@ft.component
def SelectionPanelHeader(vm: SelectionPanelViewModel):
    """选择面板头部 - 范围概览

    Args:
        vm: 选择面板 ViewModel
    """
    if not vm.has_selection:
        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.TOUCH_APP, size=20, color=ft.Colors.WHITE_38),
                ft.Text("点击脉冲图选择帧范围", size=14, color=ft.Colors.WHITE_54),
            ], spacing=12),
            padding=ft.Padding(left=24, top=12, right=24, bottom=12),
        )

    return ft.Container(
        content=ft.Row([
            # 总伤害
            ft.Column([
                ft.Text("范围总伤害", size=11, color=ft.Colors.WHITE_54),
                ft.Text(
                    format_val(vm.total_damage),
                    size=24,
                    weight=ft.FontWeight.W_900,
                    color="#FFA726"  # GenshinTheme.PRIMARY
                ),
            ], spacing=2),
            ft.VerticalDivider(width=1, color=ft.Colors.WHITE_12),
            # 事件数
            ft.Column([
                ft.Text("事件数", size=11, color=ft.Colors.WHITE_54),
                ft.Text(
                    str(vm.get_event_count()),
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE
                ),
            ], spacing=2),
            ft.VerticalDivider(width=1, color=ft.Colors.WHITE_12),
            # 时间范围
            ft.Column([
                ft.Text("时间范围", size=11, color=ft.Colors.WHITE_54),
                ft.Text(
                    f"{vm.time_range_seconds:.1f}s",
                    size=16,
                    weight=ft.FontWeight.W_600,
                    color=ft.Colors.WHITE_70
                ),
            ], spacing=2),
            ft.VerticalDivider(width=1, color=ft.Colors.WHITE_12),
            # 帧范围
            ft.Column([
                ft.Text("帧范围", size=11, color=ft.Colors.WHITE_54),
                ft.Text(
                    f"#{vm.start_frame} - #{vm.end_frame}",
                    size=14,
                    weight=ft.FontWeight.W_500,
                    color=ft.Colors.WHITE_54,
                    font_family="Consolas"
                ),
            ], spacing=2),
        ], spacing=24, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.Padding(left=24, top=12, right=24, bottom=12),
        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
        border_radius=12,
        margin=ft.Margin.only(left=16, right=16, top=8, bottom=8),
    )


@ft.component
def EventCardsGrid(
    event_cards: list[EventCardViewModel],
    on_event_click: Callable[[EventCardViewModel], None]
):
    """事件卡片网格

    Args:
        event_cards: 事件卡片 ViewModel 列表
        on_event_click: 事件点击回调
    """
    if event_cards:
        return ft.Row(
            [
                EventCard(vm=card, on_click=on_event_click)
                for card in event_cards
            ],
            spacing=8,
            run_spacing=8,
            wrap=True,
            expand=True,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
    else:
        return ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.INBOX_ROUNDED, size=48, color=ft.Colors.WHITE_24),
                ft.Text(
                    "范围内无伤害事件",
                    size=14,
                    color=ft.Colors.WHITE_38,
                    italic=True
                ),
            ], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.Alignment.CENTER,
            padding=ft.Padding(top=32, bottom=32),
            expand=True,
        )


@ft.component
def SelectionPanel(
    selection: 'FrameRangeSelection | None',
    selected_event: dict | None,
    on_event_click: Callable[[dict], None],
    on_close: Callable[[], None] | None
):
    """选择面板 - 事件卡片横向排列，自动换行

    [V17.0] 使用 SelectionPanelViewModel 进行数据绑定

    Args:
        selection: 帧范围选择数据
        selected_event: 当前选中的事件
        on_event_click: 事件点击回调
        on_close: 关闭回调
    """
    # 创建 ViewModel
    vm = SelectionPanelViewModel.from_selection(
        selection=selection,
        selected_event=selected_event,
        on_event_click=on_event_click,
    )

    def handle_card_click(card_vm: EventCardViewModel):
        """处理事件卡片点击"""
        vm.handle_event_click(card_vm)

    # 头部：范围概览
    header = SelectionPanelHeader(vm=vm)

    # 事件卡片网格
    event_count = vm.get_event_count()
    event_cards_grid = EventCardsGrid(
        event_cards=vm.event_cards,
        on_event_click=handle_card_click,
    )

    return ft.Column([
        # 范围概览头部
        header,
        # 事件列表标签
        ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.GRID_VIEW_ROUNDED, size=16, color=ft.Colors.WHITE_54),
                ft.Text(
                    f"事件列表 ({event_count})" if event_count else "事件列表",
                    size=12,
                    weight=ft.FontWeight.W_600,
                    color=ft.Colors.WHITE_70
                ),
            ], spacing=8),
            padding=ft.Padding(left=16, right=16, top=8, bottom=4),
        ),
        # 事件卡片网格
        ft.Container(
            content=event_cards_grid,
            padding=ft.Padding(left=16, right=16, bottom=16),
            expand=True,
        ),
    ], spacing=0, expand=True)
