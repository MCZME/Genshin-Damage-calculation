"""[V11.0] 主面板组件

提供底部弹出面板的主入口组件。
"""
import flet as ft
from typing import TYPE_CHECKING, Any, Callable

from .constants import PANEL_BG_COLOR
from .selection_panel import SelectionPanel
from .audit_panel import AuditPanel
from core.persistence.processors.audit.types import DamageType

if TYPE_CHECKING:
    from ui.states.analysis_state import AnalysisState


@ft.component
def DragHandle(on_close: Callable[[], None] | None):
    """拖拽横条组件 - 点击关闭面板

    悬停时横条展开并显示向下箭头，暗示"点击收起面板"。

    Args:
        on_close: 关闭回调
    """
    hovered, set_hovered = ft.use_state(False)

    # 横条本体
    bar = ft.Container(
        width=56 if hovered else 40,
        height=4,
        bgcolor=ft.Colors.WHITE_70 if hovered else ft.Colors.WHITE_30,
        border_radius=2,
        animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
    )

    # 倒三角指示器（悬停时显示）
    arrow = ft.Container(
        content=ft.Icon(
            ft.Icons.KEYBOARD_ARROW_DOWN_ROUNDED,
            size=16,
            color=ft.Colors.WHITE_54,
        ),
        opacity=1.0 if hovered else 0.0,
        offset=ft.Offset(0, 0 if hovered else -0.5),
        animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
    )

    # 整个区域作为交互热区
    return ft.Container(
        content=ft.Column(
            [bar, arrow],
            spacing=2,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        alignment=ft.Alignment.CENTER,
        padding=ft.Padding.only(top=12, bottom=8),
        height=48,  # 增大点击区域高度
        bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.WHITE) if hovered else ft.Colors.TRANSPARENT,
        animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
        on_click=lambda _: on_close() if on_close else None,
        on_hover=lambda e: set_hovered(e.data is True),
    )


@ft.component
def DamageAuditBottomPanel(
    state: 'AnalysisState',
    detail_slot: Any,
    on_close: Callable[[], None] | None
):
    """伤害审计底部弹出面板

    Args:
        state: 分析状态
        detail_slot: 详情槽位
        on_close: 关闭回调
    """
    vm = state.vm
    visible = vm.drawer_visible
    panel_mode = vm.panel_mode
    selection = vm.frame_range_selection
    selected_event = vm.selected_event

    # 本地状态：当前选中的乘区（不再默认选中，乘区不可点击）
    active_bucket, set_active_bucket = ft.use_state(None)
    # 本地状态：当前选中的域
    selected_domain, set_selected_domain = ft.use_state(None)

    # 获取审计数据
    buckets_data = detail_slot.data if detail_slot and detail_slot.data else {}

    def handle_event_click(ev: dict):
        """处理事件点击 - 切换到审计面板"""
        state.switch_to_audit(ev)
        set_active_bucket(None)
        set_selected_domain(None)

    def handle_domain_click(bucket_key: str, domain_key: str):
        """处理域值点击

        Args:
            bucket_key: 所属乘区键
            domain_key: 域键名
        """
        # 判断是否点击已选中的域（toggle 行为）
        if active_bucket == bucket_key and selected_domain == domain_key:
            # 取消选中
            set_active_bucket(None)
            set_selected_domain(None)
        else:
            # 选中新域
            set_active_bucket(bucket_key)
            set_selected_domain(domain_key)

    def handle_back():
        """返回选择面板"""
        state.switch_to_selection()

    # 计算面板高度
    panel_height = 420 if panel_mode == "selection" else 320

    # 从 buckets_data 提取伤害类型
    damage_type_ctx = buckets_data.get("_damage_type_ctx") if buckets_data else None
    damage_type = damage_type_ctx.damage_type if damage_type_ctx else DamageType.NORMAL

    # 根据面板模式渲染不同内容
    if panel_mode == "selection":
        panel_content = SelectionPanel(
            selection=selection,
            selected_event=selected_event,
            on_event_click=handle_event_click,
            on_close=on_close,
        )
    else:
        panel_content = AuditPanel(
            event=selected_event,
            active_bucket=active_bucket,
            selected_domain=selected_domain,
            buckets_data=buckets_data,
            on_domain_click=handle_domain_click,
            on_back=handle_back,
            on_close=on_close,
            damage_type=damage_type,
        )

    return ft.Container(
        content=ft.Column([
            DragHandle(on_close),  # 横条在最顶部
            panel_content,          # SelectionPanel 或 AuditPanel
        ], spacing=0, expand=True),
        bgcolor=PANEL_BG_COLOR,
        border_radius=ft.BorderRadius(top_left=20, top_right=20, bottom_left=0, bottom_right=0),
        height=panel_height,
        bottom=0 if visible else -panel_height,
        left=0,
        right=0,
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=24,
            color=ft.Colors.with_opacity(0.4, ft.Colors.BLACK),
            offset=ft.Offset(0, -4)
        ),
        animate=ft.Animation(500, ft.AnimationCurve.EASE_OUT_QUART),
    )
