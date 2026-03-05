import flet as ft
from ui.theme import GenshinTheme
from ui.components.analysis.damage_audit_inspector import DamageAuditInspector

@ft.component
def FloatingDrawer(state, model, dist_slot, detail_slot, on_fetch_detail, on_close):
    """
    [V6.0] 极度脱水解耦版抽屉。
    仅接收纯数据 Slot 和原子回调，切断一切循环引用可能。
    """
    is_pinned, set_is_pinned = ft.use_state(False)
    
    visible = model.drawer_visible
    side = model.drawer_side
    width = 480
    selected_event = model.selected_event

    pos_args = {}
    # MD3 侧边抽屉标准圆角：非贴边一侧为大圆角 (28px)
    if side == "right":
        pos_args["right"] = 0 if visible else -width
        radius = ft.border_radius.only(top_left=28, bottom_left=28)
        shadow_offset = ft.Offset(-4, 0)
    else:
        pos_args["left"] = 0 if visible else -width
        radius = ft.border_radius.only(top_right=28, bottom_right=28)
        shadow_offset = ft.Offset(4, 0)

    # 动态页眉逻辑：MD3 风格
    if selected_event:
        header_content = ft.Row([
            ft.IconButton(
                icon=ft.Icons.ARROW_BACK, 
                icon_size=24, 
                icon_color=ft.Colors.ON_SURFACE,
                tooltip="返回概览",
                on_click=lambda _: state.set_selected_event(None),
            ),
            ft.Column([
                ft.Text(selected_event.get('source', '审计详情'), size=22, weight=ft.FontWeight.NORMAL, color=ft.Colors.ON_SURFACE), # Headline Small
                ft.Text(f"#{selected_event.get('event_id', '???')}", size=11, color=ft.Colors.ON_SURFACE_VARIANT, weight=ft.FontWeight.W_500), # Label Small
            ], spacing=2),
        ], spacing=16, alignment=ft.MainAxisAlignment.START)
    else:
        header_content = ft.Row([
            ft.Icon(ft.Icons.ANALYTICS, size=24, color=GenshinTheme.PRIMARY),
            ft.Text("伤害审计系统", size=22, weight=ft.FontWeight.NORMAL, color=ft.Colors.ON_SURFACE), # Headline Small
        ], spacing=16, alignment=ft.MainAxisAlignment.START)

    header = ft.Container(
        content=ft.Row([
            header_content,
            ft.Row([
                ft.IconButton(
                    ft.Icons.PUSH_PIN if is_pinned else ft.Icons.PUSH_PIN_OUTLINED, 
                    icon_size=24, 
                    icon_color=GenshinTheme.PRIMARY if is_pinned else ft.Colors.ON_SURFACE_VARIANT,
                    on_click=lambda _: set_is_pinned(not is_pinned),
                    tooltip="固定面板"
                ),
                ft.IconButton(
                    ft.Icons.CLOSE, 
                    icon_size=24, 
                    icon_color=ft.Colors.ON_SURFACE_VARIANT,
                    on_click=lambda _: on_close(),
                    tooltip="关闭面板"
                ),
            ], spacing=8)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        padding=ft.Padding(left=24, top=20, right=24, bottom=20),
        border=ft.Border.only(bottom=ft.BorderSide(1, ft.Colors.with_opacity(0.08, ft.Colors.ON_SURFACE)))
    )

    return ft.Container(
        content=ft.Column([
            header,
            ft.Container(
                content=DamageAuditInspector(
                    state=state, 
                    model=model, 
                    dist_slot=dist_slot, 
                    detail_slot=detail_slot, 
                    on_fetch_detail=on_fetch_detail
                ),
                padding=ft.Padding(left=24, top=16, right=24, bottom=24), # 增加全局内边距
                expand=True
            )
        ], spacing=0, expand=True),
        width=width, 
        top=12, bottom=12,
        bgcolor="#2B2738",
        border_radius=radius,
        # 移除边框，使用 Elevation (阴影)
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=16,
            color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK),
            offset=shadow_offset
        ),
        animate=ft.Animation(500, ft.AnimationCurve.EASE_OUT_CUBIC), # MD3 标准缓动
        **pos_args
    )
