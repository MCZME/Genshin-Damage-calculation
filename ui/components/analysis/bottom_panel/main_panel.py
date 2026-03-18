"""[V19.0] 主面板组件

提供底部弹出面板的主入口组件。

[V19.0] 父子持有设计：
- BottomPanelViewModel 在组件内部通过 use_state 创建
- 管理面板切换和子 ViewModel
- SelectionPanel/AuditPanel 消费各自的子 ViewModel
"""
import flet as ft
from typing import TYPE_CHECKING, Callable

from .constants import PANEL_BG_COLOR
from .selection_panel import SelectionPanel
from .audit_panel import AuditPanel
from ui.view_models.analysis.bottom_panel import BottomPanelViewModel

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
        animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT)
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
    on_close: Callable[[], None] | None
):
    """伤害审计底部弹出面板

    [V19.0] 父子持有设计：
    - BottomPanelViewModel 在组件内部通过 use_state 创建
    - 持有 selection 和 audit 两个子 ViewModel
    - 面板切换逻辑由 BottomPanelViewModel 处理

    Args:
        state: 分析状态（外部状态，用于同步触发条件）
        on_close: 关闭回调
    """
    # 外部状态（触发条件）
    external_vm = state.vm
    selection_data = external_vm.frame_range_selection
    selected_event = external_vm.selected_event
    data_service = external_vm.data_service

    # [V19.0] 局部状态：底部面板容器 ViewModel
    # 直接传入实例，符合官方 @ft.observable 模式
    panel_vm, _ = ft.use_state(BottomPanelViewModel())

    # 缓存前值，用于比较是否变化
    prev_selection_ref = ft.use_ref(None)
    prev_event_ref = ft.use_ref(None)

    # 同步外部触发条件
    def _sync_external_state():
        """同步外部状态到内部 ViewModel"""
        # 确保子 ViewModel 已初始化
        panel_vm.ensure_initialized()

        # 同步 data_service
        panel_vm.data_service = data_service

        # 检查 selection_data 是否变化
        prev_selection = prev_selection_ref.current
        selection_changed = prev_selection is not selection_data

        if selection_changed:
            prev_selection_ref.current = selection_data

            if selection_data:
                panel_vm.visible = True
                panel_vm.panel_mode = "selection"
                panel_vm.update_selection(
                    selection_data,
                    selected_event,
                    on_event_click=lambda ev: panel_vm.switch_to_audit(ev),
                )
            else:
                panel_vm.visible = False
            return

        # 检查 selected_event 是否变化
        prev_event = prev_event_ref.current
        event_changed = prev_event is not selected_event

        if event_changed:
            prev_event_ref.current = selected_event

            if selected_event and panel_vm.visible:
                panel_vm.switch_to_audit(selected_event)

    ft.use_effect(_sync_external_state, [selection_data, selected_event, data_service])

    def handle_event_click(ev: dict):
        """处理事件点击 - 切换到审计面板"""
        panel_vm.switch_to_audit(ev)

    def handle_back():
        """返回选择面板"""
        panel_vm.switch_to_selection()

    def handle_close():
        """关闭面板"""
        panel_vm.hide()
        if on_close:
            on_close()

    # 计算面板高度
    panel_height = 420 if panel_vm.panel_mode == "selection" else 320

    # 根据面板模式渲染不同内容
    if panel_vm.panel_mode == "selection":
        panel_content = SelectionPanel(
            selection=selection_data,
            selected_event=selected_event,
            on_event_click=handle_event_click,
            on_close=handle_close,
        )
    else:
        panel_content = AuditPanel(
            vm=panel_vm.audit,
            on_back=handle_back,
            on_close=handle_close,
        )

    return ft.Container(
        content=ft.Column([
            DragHandle(handle_close),
            panel_content,
        ], spacing=0, expand=True),
        bgcolor=PANEL_BG_COLOR,
        border_radius=ft.BorderRadius(top_left=20, top_right=20, bottom_left=0, bottom_right=0),
        height=panel_height,
        bottom=0 if panel_vm.visible else -panel_height,
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
