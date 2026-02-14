import flet as ft
import flet.canvas as cv
from ui.theme import GenshinTheme


class VisualPane(ft.Column):
    """
    右栏：可视化面板 (自适应修复版)
    """

    def __init__(self, state):
        super().__init__(expand=True, spacing=15)
        self.state = state
        self.is_compact = False

        # 显式定义的显示尺寸 (由布局同步)
        self.display_w = 332.0  # 380 - padding
        self.display_h = 400.0

        self.env_card = self._build_env_card()
        self.canvas = cv.Canvas(expand=True)

        self.canvas_container = ft.Container(
            content=ft.Stack(
                [
                    self.canvas,
                    ft.Stack(key="entity_layer", expand=True),
                    ft.Container(
                        content=ft.Text(
                            "BATTLEFIELD",
                            size=9,
                            weight=ft.FontWeight.W_900,
                            opacity=0.1,
                        ),
                        top=10,
                        left=10,
                    ),
                ]
            ),
            expand=True,
            bgcolor="rgba(0, 0, 0, 0.3)",
            border_radius=16,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )

        self.compact_placeholder = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.Icons.MAP, color=GenshinTheme.PRIMARY, size=20),
                    ft.Text(
                        "VISUAL",
                        size=9,
                        rotate=ft.Rotate(1.57),
                        weight=ft.FontWeight.W_900,
                        opacity=0.3,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=20,
            ),
            alignment=ft.Alignment.CENTER,
            expand=True,
        )

    def update_size(self, width: float, height: float):
        """外部主动推入真实物理尺寸"""
        self.display_w = width
        self.display_h = height
        self._draw_all()

    def _build_env_card(self):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(
                                ft.Icons.CLOUD_QUEUE, color=ft.Colors.CYAN_200, size=18
                            ),
                            ft.Text(
                                "环境状态",
                                size=12,
                                weight=ft.FontWeight.BOLD,
                                color=GenshinTheme.ON_SURFACE,
                            ),
                        ],
                        spacing=8,
                    ),
                    ft.Divider(height=1, color="rgba(255, 255, 255, 0.05)"),
                    ft.Row(
                        [
                            self._build_info_item("天气", "Clear"),
                            self._build_info_item("场地", "Neutral"),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                ],
                spacing=12,
            ),
            padding=16,
            bgcolor="rgba(255, 255, 255, 0.02)",
            border_radius=16,
            on_click=lambda _: self.state.select_environment(),
        )

    def did_mount(self):
        self.refresh()

    def refresh(self):
        self.controls.clear()
        if self.is_compact:
            self.controls.append(self.compact_placeholder)
        else:
            self.controls.extend(
                [
                    self.env_card,
                    ft.Text(
                        "战场态势", size=10, weight=ft.FontWeight.W_900, opacity=0.4
                    ),
                    self.canvas_container,
                ]
            )
            env = self.state.environment
            try:
                self.env_card.content.controls[2].controls[0].controls[
                    1
                ].value = env.get("weather", "N/A")
                self.env_card.content.controls[2].controls[1].controls[
                    1
                ].value = env.get("field", "N/A")
            except:
                pass
            self._draw_all()

        if self.page:
            try:
                self.update()
            except:
                pass

    def _draw_all(self):
        # 强制检查 Canvas 是否就绪
        try:
            _ = self.canvas.page
        except:
            return

        w, h = self.display_w, self.display_h
        cx, cy = w / 2, h / 2
        scale = 15.0

        # 交互层操作
        try:
            self.canvas_container.content.controls[1].controls.clear()
        except:
            pass

        shapes = []
        # 1. 网格
        grid_paint = ft.Paint(
            style=ft.PaintingStyle.STROKE,
            color="rgba(255, 255, 255, 0.12)",
            stroke_width=1,
        )
        axis_paint = ft.Paint(
            style=ft.PaintingStyle.STROKE,
            color="rgba(255, 255, 255, 0.3)",
            stroke_width=1.5,
        )

        max_m = 25
        for m in range(-max_m, max_m + 1):
            lx = cx + (m * scale)
            if 0 <= lx <= w:
                shapes.append(
                    cv.Line(lx, 0, lx, h, paint=grid_paint if m != 0 else axis_paint)
                )
            ly = cy + (m * scale)
            if 0 <= ly <= h:
                shapes.append(
                    cv.Line(0, ly, w, ly, paint=grid_paint if m != 0 else axis_paint)
                )

        # 2. 实体
        for i, member in enumerate(self.state.team):
            if not member:
                continue
            pos = member.get("position", {"x": 0, "z": 0})
            color = GenshinTheme.get_element_color(
                member["character"].get("element", "Neutral")
            )
            is_selected = (
                self.state.selection
                and self.state.selection.get("type") == "character"
                and self.state.selection.get("index") == i
            )
            self._add_shape_dot(
                shapes, cx, cy, pos["x"], pos["z"], scale, color, w, h, is_selected
            )
            self._add_interaction_node(
                cx,
                cy,
                pos["x"],
                pos["z"],
                scale,
                lambda _, idx=i: self.state.select_character(idx),
            )

        for i, target in enumerate(self.state.targets):
            pos = target.get("position", {"x": 0, "z": 0})
            is_selected = (
                self.state.selection
                and self.state.selection.get("type") == "target"
                and self.state.selection.get("index") == i
            )
            self._add_shape_dot(
                shapes,
                cx,
                cy,
                pos["x"],
                pos["z"],
                scale,
                ft.Colors.RED_ACCENT,
                w,
                h,
                is_selected,
            )
            self._add_interaction_node(
                cx,
                cy,
                pos["x"],
                pos["z"],
                scale,
                lambda _, idx=i: self.state.select_target(idx),
            )

        self.canvas.shapes = shapes
        if self.canvas.page:
            try:
                self.canvas.update()
            except:
                pass

    def _add_shape_dot(self, shapes, cx, cy, x, z, scale, color, w, h, is_selected):
        ui_x = cx + (x * scale)
        ui_y = cy - (z * scale)
        if 0 <= ui_x <= w and 0 <= ui_y <= h:
            if is_selected:
                shapes.append(
                    cv.Circle(
                        ui_x,
                        ui_y,
                        12,
                        paint=ft.Paint(
                            color=ft.Colors.with_opacity(0.4, color),
                            style=ft.PaintingStyle.STROKE,
                            stroke_width=2,
                        ),
                    )
                )
            shapes.append(
                cv.Circle(
                    ui_x,
                    ui_y,
                    5,
                    paint=ft.Paint(color=color, style=ft.PaintingStyle.FILL),
                )
            )
            shapes.append(
                cv.Circle(
                    ui_x,
                    ui_y,
                    9,
                    paint=ft.Paint(
                        color=ft.Colors.with_opacity(0.3, color),
                        style=ft.PaintingStyle.FILL,
                    ),
                )
            )

    def _add_interaction_node(self, cx, cy, x, z, scale, on_click):
        ui_x = cx + (x * scale)
        ui_y = cy - (z * scale)
        try:
            self.canvas_container.content.controls[1].controls.append(
                ft.Container(
                    width=30,
                    height=30,
                    left=ui_x - 15,
                    top=ui_y - 15,
                    on_click=on_click,
                    border_radius=15,
                )
            )
        except:
            pass

    def _build_info_item(self, label, value):
        return ft.Column(
            [
                ft.Text(label, size=9, color=GenshinTheme.TEXT_SECONDARY),
                ft.Text(
                    value,
                    size=12,
                    weight=ft.FontWeight.W_600,
                    color=GenshinTheme.ON_SURFACE,
                ),
            ],
            spacing=2,
        )
