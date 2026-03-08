import flet as ft
from collections.abc import Callable
from ui.theme import GenshinTheme

def format_val(val: float, is_percent: bool = False) -> str:
    if is_percent:
        return f"+{val*100:.1f}%"
    return f"{val:,.0f}"

@ft.component
def AuditDetailItem(step: dict, is_primary: bool = False):
    """审计明细项：MD3 卡片风格"""
    strip_color = GenshinTheme.PRIMARY if is_primary else GenshinTheme.GOLD_DARK
    
    return ft.Container(
        content=ft.Row([
            ft.Row([
                ft.Container(width=4, height=18, bgcolor=strip_color, border_radius=2),
                ft.Column([
                    ft.Text(step.get('source', '未知来源'), size=14, weight=ft.FontWeight.W_600, color=ft.Colors.ON_SURFACE),
                    ft.Text(step.get('stat', ""), size=11, color=ft.Colors.ON_SURFACE_VARIANT) if step.get('stat') else ft.Container(),
                ], spacing=0, alignment=ft.MainAxisAlignment.CENTER),
            ], spacing=12),
            
            ft.Text(
                f"{step.get('value', 0):+g}" if step.get('op') == "ADD" else f"x{step.get('value', 1.0)}", 
                size=14, weight=ft.FontWeight.W_900, color=GenshinTheme.GOLD_LIGHT
            )
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        padding=ft.Padding(16, 12, 16, 12), 
        bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.ON_SURFACE),
        border_radius=12,
        border=ft.Border.all(1, ft.Colors.with_opacity(0.05, ft.Colors.ON_SURFACE)),
    )

@ft.component
def MultiplierBlock(id_key: str, name: str, val: str, is_active: bool, on_change: Callable):
    """函数式乘区方块：MD3 FilterChip 风格"""
    bg_color = ft.Colors.with_opacity(0.2, GenshinTheme.PRIMARY) if is_active else ft.Colors.with_opacity(0.03, ft.Colors.ON_SURFACE)
    text_color = GenshinTheme.PRIMARY if is_active else ft.Colors.ON_SURFACE_VARIANT
    border_obj = ft.Border.all(width=2, color=GenshinTheme.PRIMARY) if is_active else ft.Border.all(width=1, color=ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE))
    
    return ft.Container(
        content=ft.Column([
            ft.Text(name, size=10, weight=ft.FontWeight.W_500, color=text_color, opacity=0.8),
            ft.Text(val, size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE),
        ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
        width=72, height=56, 
        border_radius=12, 
        alignment=ft.Alignment(0, 0),
        border=border_obj,
        bgcolor=bg_color,
        on_click=lambda _: on_change(id_key),
        animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT)
    )

@ft.component
def DamageAuditInspector(state, model, dist_slot, detail_slot, on_fetch_detail):
    active_bucket, set_active_bucket = ft.use_state("BASE")
    selected_event = model.selected_event
    
    current_frame = model.current_frame
    frame_map = {}
    if dist_slot and hasattr(dist_slot, 'data') and isinstance(dist_slot.data, dict):
        frame_map = dist_slot.data.get("frame_map", {})
    
    frame_data = frame_map.get(current_frame, {"events": [], "total": 0})
    raw_events = frame_data.get("events", [])
    events = sorted(raw_events, key=lambda x: x.get('dmg', 0), reverse=True)
    total_dmg = frame_data.get("total", 0)

    def handle_event_click(ev):
        state.set_selected_event(ev)
        set_active_bucket("BASE")
        if on_fetch_detail:
            on_fetch_detail(ev.get('event_id'))

    # --- 视图 A: 快照概览 ---
    def build_snapshot_view():
        return ft.Column([
            ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text("当前帧总伤害", size=12, color=ft.Colors.ON_SURFACE_VARIANT, weight=ft.FontWeight.W_500),
                        ft.Text(format_val(total_dmg), size=36, weight=ft.FontWeight.W_900, color=GenshinTheme.PRIMARY, style=ft.TextStyle(letter_spacing=-0.5)),
                    ], spacing=2),
                    ft.Column([
                        ft.Text("项目数", size=12, color=ft.Colors.ON_SURFACE_VARIANT, weight=ft.FontWeight.W_500, text_align=ft.TextAlign.RIGHT),
                        ft.Text(str(len(events)), size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE, text_align=ft.TextAlign.RIGHT),
                    ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.END)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                margin=ft.Margin.only(bottom=24, top=8),
            ),
            
            ft.Row([
                ft.Icon(ft.Icons.SEGMENT_ROUNDED, size=18, color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Text("伤害事件日志", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE),
            ], spacing=8),
            
            ft.Container(
                content=ft.ListView(
                    controls=[
                        ft.Container(
                            key=f"LOG_EV_{ev.get('event_id')}",
                            content=ft.Row([
                                ft.Column([
                                    ft.Text(ev.get('source', '未知来源'), size=15, weight=ft.FontWeight.W_600, color=ft.Colors.ON_SURFACE),
                                    ft.Row([
                                        ft.Text(f"#{ev.get('event_id', '???')}", size=11, color=ft.Colors.ON_SURFACE_VARIANT, weight=ft.FontWeight.W_500),
                                        ft.Text("•", size=11, color=ft.Colors.ON_SURFACE_VARIANT),
                                        ft.Text(ev.get('element', '无属性'), size=11, weight=ft.FontWeight.BOLD, 
                                               color=GenshinTheme.get_element_color(ev.get('element'))),
                                    ], spacing=6),
                                ], spacing=4, alignment=ft.MainAxisAlignment.CENTER),
                                ft.Text(format_val(ev.get('dmg', 0)), size=18, weight=ft.FontWeight.W_900, color=ft.Colors.ON_SURFACE),
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            padding=ft.Padding(20, 14, 20, 14),
                            margin=ft.Margin.only(bottom=8),
                            border_radius=16,
                            bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.ON_SURFACE),
                            border=ft.Border.all(1, ft.Colors.with_opacity(0.05, ft.Colors.ON_SURFACE)),
                            on_click=lambda _, e=ev: handle_event_click(e),
                        ) for ev in events
                    ],
                    spacing=0, expand=True,
                ),
                expand=True,
                margin=ft.Margin.only(top=12)
            )
        ], key="snapshot_view", expand=True)

    # --- 视图 B: 审计详情 ---
    def build_audit_view():
        if not selected_event:
            return ft.Container()
        
        buckets_data = detail_slot.data or {}
        elem_color = GenshinTheme.get_element_color(selected_event.get('element'))
        
        bucket_configs = [
            ("BASE", "base", "基础属性"),
            ("MULT", "multiplier", "倍率加值"),
            ("BONUS", "bonus", "增伤乘区"),
            ("CRIT", "crit", "暴击乘区"),
            ("REACT", "reaction", "反应乘区"),
            ("DEF", "defense", "防御减免"),
            ("RES", "resistance", "抗性削减")
        ]
        
        def create_block(key, data_key, label):
            val_str = "0"
            if data_key in buckets_data:
                b = buckets_data[data_key]
                if data_key == 'base':
                    val_str = format_val(b.get('total', 0))
                elif data_key == 'multiplier':
                    m = b.get('multiplier', 1.0)
                    f = b.get('flat', 0.0)
                    val_str = f"{m:.2f}x" if f == 0 else f"{m:.1f}+{format_val(f)}"
                else:
                    v = b.get('multiplier', 1.0)
                    val_str = f"{v:.2f}x"
            
            return MultiplierBlock(
                id_key=key,
                name=label, val=val_str, 
                is_active=active_bucket == key,
                on_change=set_active_bucket
            )

        row1_controls = []
        for i, config in enumerate(bucket_configs[:4]):
            row1_controls.append(create_block(*config))
            if i < 3:
                row1_controls.append(ft.Text("×", size=12, color=ft.Colors.ON_SURFACE_VARIANT, weight=ft.FontWeight.BOLD))

        row2_controls = []
        for i, config in enumerate(bucket_configs[4:]):
            row2_controls.append(create_block(*config))
            if i < 2:
                row2_controls.append(ft.Text("×", size=12, color=ft.Colors.ON_SURFACE_VARIANT, weight=ft.FontWeight.BOLD))
        
        row2_controls.extend([
            ft.Text("=", size=16, weight=ft.FontWeight.W_900, color=ft.Colors.ON_SURFACE_VARIANT),
            ft.Container(
                content=ft.Text(format_val(selected_event.get('dmg', 0)), size=18, weight=ft.FontWeight.W_900, color=elem_color),
                padding=ft.Padding(left=12, top=6, right=12, bottom=6),
                bgcolor=ft.Colors.with_opacity(0.12, elem_color),
                border_radius=10,
                border=ft.Border.all(1, ft.Colors.with_opacity(0.2, elem_color))
            )
        ])

        current_data_key = next((c[1] for c in bucket_configs if c[0] == active_bucket), "base")
        current_steps = buckets_data.get(current_data_key, {}).get('steps', [])

        return ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Column([
                            ft.Row(controls=row1_controls, spacing=8, alignment=ft.MainAxisAlignment.CENTER),
                            ft.Row(controls=row2_controls, spacing=8, alignment=ft.MainAxisAlignment.CENTER),
                        ], spacing=12),
                        padding=ft.Padding(20, 24, 20, 24),
                        bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.ON_SURFACE),
                        border_radius=24,
                        border=ft.Border.all(1, ft.Colors.with_opacity(0.05, ft.Colors.ON_SURFACE)),
                        margin=ft.Margin.only(bottom=24)
                    ),
                    
                    ft.Row([
                        ft.Icon(ft.Icons.SEGMENT_ROUNDED, size=18, color=ft.Colors.ON_SURFACE_VARIANT),
                        ft.Text("计算逻辑详情", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE),
                    ], spacing=8),
                    
                    ft.Container(
                        content=ft.ListView(
                            controls=[
                                AuditDetailItem(step, is_primary=active_bucket=="BASE") 
                                for step in current_steps
                            ] if not detail_slot.loading else [
                                ft.Container(
                                    content=ft.ProgressRing(width=24, height=24, stroke_width=2, color=GenshinTheme.PRIMARY), 
                                    alignment=ft.Alignment(0, 0), 
                                    padding=ft.Padding(top=60, left=0, right=0, bottom=0)
                                )
                            ],
                            spacing=10, expand=True,
                        ),
                        expand=True,
                        margin=ft.Margin.only(top=12)
                    )
                ], spacing=0),
                expand=True
            )
        ], key="audit_view", expand=True)

    current_content = build_audit_view() if selected_event else build_snapshot_view()
    
    return ft.AnimatedSwitcher(
        content=current_content,
        transition=ft.AnimatedSwitcherTransition.FADE,
        duration=400,
        switch_in_curve=ft.AnimationCurve.EASE_OUT_QUINT,
        expand=True
    )
