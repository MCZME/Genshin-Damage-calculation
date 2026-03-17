"""[V11.0] 选择面板组件

提供事件选择界面的组件。
"""
import flet as ft
from typing import Callable

from ui.theme import GenshinTheme
from ui.view_models.analysis.tile_vms.types import FrameRangeSelection
from .utils import format_val


@ft.component
def EventCard(
    event: dict,
    is_selected: bool,
    on_click: Callable[[dict], None]
):
    """事件卡片 - 横向展示

    Args:
        event: 事件数据
        is_selected: 是否选中
        on_click: 点击回调
    """
    elem_color = GenshinTheme.get_element_color(event.get('element', 'Neutral'))

    return ft.Container(
        content=ft.Column([
            # 角色名称（灰色小字）
            ft.Text(
                event.get('source', '未知'),
                size=9,
                color=ft.Colors.WHITE_54,
                no_wrap=True,
                overflow=ft.TextOverflow.ELLIPSIS,
                text_align=ft.TextAlign.CENTER,
            ),
            # 伤害名称（主标题）
            ft.Text(
                event.get('name', '未知伤害'),
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
                    bgcolor=elem_color,
                    border_radius=4,
                ),
                ft.Text(
                    format_val(event.get('dmg', 0)),
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    color=elem_color,
                ),
            ], spacing=4, alignment=ft.MainAxisAlignment.CENTER),
            # 事件ID和帧
            ft.Text(
                f"#{event.get('event_id')} F{event.get('frame')}",
                size=9,
                color=ft.Colors.WHITE_38,
                font_family="Consolas",
                text_align=ft.TextAlign.CENTER,
            ),
        ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        width=110,
        padding=ft.Padding.all(8),
        bgcolor=ft.Colors.with_opacity(0.15, elem_color) if is_selected else ft.Colors.WHITE_10,
        border_radius=8,
        border=ft.Border.all(2, elem_color) if is_selected else ft.Border.all(1, ft.Colors.WHITE_12),
        on_click=lambda _: on_click(event),
        animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
    )


@ft.component
def SelectionPanel(
    selection: FrameRangeSelection | None,
    selected_event: dict | None,
    on_event_click: Callable[[dict], None],
    on_close: Callable[[], None] | None
):
    """选择面板 - 事件卡片横向排列，自动换行

    Args:
        selection: 帧范围选择数据
        selected_event: 当前选中的事件
        on_event_click: 事件点击回调
        on_close: 关闭回调
    """
    events = selection.events if selection else []

    # 头部：范围概览
    if not selection:
        header = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.TOUCH_APP, size=20, color=ft.Colors.WHITE_38),
                ft.Text("点击脉冲图选择帧范围", size=14, color=ft.Colors.WHITE_54),
            ], spacing=12),
            padding=ft.Padding(left=24, top=12, right=24, bottom=12),
        )
    else:
        header = ft.Container(
            content=ft.Row([
                # 总伤害
                ft.Column([
                    ft.Text("范围总伤害", size=11, color=ft.Colors.WHITE_54),
                    ft.Text(
                        format_val(selection.total_damage),
                        size=24,
                        weight=ft.FontWeight.W_900,
                        color=GenshinTheme.PRIMARY
                    ),
                ], spacing=2),
                ft.VerticalDivider(width=1, color=ft.Colors.WHITE_12),
                # 事件数
                ft.Column([
                    ft.Text("事件数", size=11, color=ft.Colors.WHITE_54),
                    ft.Text(
                        str(len(events)),
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
                        f"{selection.time_range_seconds:.1f}s",
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
                        f"#{selection.start_frame} - #{selection.end_frame}",
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

    # 事件卡片网格（使用 Wrap 实现自动换行）
    if events:
        event_cards_content = ft.Row(
            [
                EventCard(
                    event=ev,
                    is_selected=(selected_event is not None and ev.get('event_id') == selected_event.get('event_id')),
                    on_click=on_event_click
                ) for ev in events
            ],
            spacing=8,
            run_spacing=8,
            wrap=True,
            expand=True,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
    else:
        event_cards_content = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.INBOX_ROUNDED, size=48, color=ft.Colors.WHITE_24),
                ft.Text(
                    "范围内无伤害事件" if selection else "点击脉冲图选择帧范围",
                    size=14,
                    color=ft.Colors.WHITE_38,
                    italic=True
                ),
            ], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.Alignment.CENTER,
            padding=ft.Padding(top=32, bottom=32),
            expand=True,
        )

    return ft.Column([
        # 范围概览头部
        header,
        # 事件列表标签
        ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.GRID_VIEW_ROUNDED, size=16, color=ft.Colors.WHITE_54),
                ft.Text(
                    f"事件列表 ({len(events)})" if events else "事件列表",
                    size=12,
                    weight=ft.FontWeight.W_600,
                    color=ft.Colors.WHITE_70
                ),
            ], spacing=8),
            padding=ft.Padding(left=16, right=16, top=8, bottom=4),
        ),
        # 事件卡片网格
        ft.Container(
            content=event_cards_content,
            padding=ft.Padding(left=16, right=16, bottom=16),
            expand=True,
        ),
    ], spacing=0, expand=True)
