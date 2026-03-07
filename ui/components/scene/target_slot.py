import flet as ft
from ui.theme import GenshinTheme
from ui.components.scene.stat_input import StatInputField

@ft.component
def TargetSlot(
    data: dict, 
    on_change = None, 
    on_pick = None
):
    """
    声明式目标配置卡 (V4.5)。
    """
    # 1. 顶部：资产头部
    header = ft.GestureDetector(
        content=ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text(data.get('name', "未选择目标"), size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Text("点击切换怪物类型", size=10, color=GenshinTheme.TEXT_SECONDARY),
                ], spacing=2, expand=True),
                ft.Container(
                    content=ft.Text(f"Lv.{data['level']}", size=12, weight=ft.FontWeight.W_900),
                    padding=ft.Padding(8, 4, 8, 4),
                    bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.BLACK),
                    border_radius=4,
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.Padding(15, 12, 15, 12),
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
            border_radius=8,
            on_click=lambda _: on_pick() if on_pick else None,
        ),
        mouse_cursor=ft.MouseCursor.CLICK
    )

    # 2. 抗性配置网格
    res_keys = list(data['resists'].keys())
    res_controls = []
    for k in res_keys:
        def handle_res_change(v, key=k):
            data['resists'][key] = v
            if on_change: on_change()

        res_controls.append(
            StatInputField(
                label=k,
                value=data['resists'][k],
                suffix="%",
                element="Neutral",
                width=135,
                on_change=handle_res_change
            )
        )

    res_grid = ft.Column([
        ft.Text("元素/物理抗性 (%)", size=11, weight=ft.FontWeight.BOLD, color=GenshinTheme.TEXT_SECONDARY),
        ft.ResponsiveRow([
            ft.Column([res_controls[i] for i in range(0, 4)], col={"sm": 6}, spacing=5),
            ft.Column([res_controls[i] for i in range(4, 8)], col={"sm": 6}, spacing=5),
        ], spacing=10)
    ], spacing=8)

    # 3. 组装内容
    return ft.Container(
        content=ft.Column([
            header,
            ft.Divider(height=1, color=ft.Colors.WHITE_10),
            res_grid
        ], spacing=12),
        padding=ft.Padding(15, 15, 15, 15),
        bgcolor=GenshinTheme.SURFACE_VARIANT,
        border_radius=12,
        border=ft.Border.all(1, ft.Colors.with_opacity(0.1, GenshinTheme.ON_SURFACE)),
        width=320,
    )
