import flet as ft
import flet.canvas as cv
from ui.theme import GenshinTheme


class UniverseNodeUI(ft.Container):
    """画布上的物理节点"""

    def __init__(self, node, is_selected, on_click, on_add):
        accent = GenshinTheme.PRIMARY if node.id != "root" else ft.Colors.AMBER

        # 受控节点样式：如果是受控节点，使用虚线边框或特定颜色，并隐藏添加按钮
        is_managed = getattr(node, "is_managed", False)

        leaf_badge = ft.Container(
            content=ft.Text(
                "SAMPLE",
                size=7,
                weight=ft.FontWeight.W_900,
                color=GenshinTheme.ON_PRIMARY,
            ),
            bgcolor=GenshinTheme.PRIMARY,
            padding=ft.padding.symmetric(horizontal=5, vertical=1),
            border_radius=ft.border_radius.only(top_left=8, bottom_right=10),
            visible=len(node.children) == 0,
            right=0,
            bottom=0,
        )

        super().__init__(
            content=ft.Stack(
                [
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(
                                        node.name or "宇宙变体",
                                        size=11,
                                        weight=ft.FontWeight.BOLD,
                                        expand=True,
                                        color=ft.Colors.AMBER_100
                                        if is_managed
                                        else GenshinTheme.ON_SURFACE,
                                    ),
                                    ft.IconButton(
                                        ft.Icons.ADD_CIRCLE_OUTLINE,
                                        icon_size=14,
                                        on_click=lambda _: on_add(node),
                                        opacity=0.6,
                                        icon_color=GenshinTheme.PRIMARY,
                                        visible=True,  # 允许受控节点添加后续分支
                                    ),
                                ],
                                spacing=5,
                            ),
                            ft.Text(
                                node.rule.label
                                if node.rule
                                else ("BASE" if node.id == "root" else "Inherited"),
                                size=9,
                                opacity=0.4,
                                color=GenshinTheme.TEXT_SECONDARY,
                            ),
                        ],
                        spacing=2,
                        tight=True,
                    ),
                    leaf_badge,
                ]
            ),
            width=140,
            padding=10,
            bgcolor=GenshinTheme.SURFACE,
            border=ft.border.all(
                2,
                accent
                if is_selected
                else (ft.Colors.AMBER_900 if is_managed else None),
            ),
            border_radius=12,
            on_click=lambda _: on_click(node),
            shadow=ft.BoxShadow(
                blur_radius=15 if is_selected else 5, color="rgba(0,0,0,0.3)"
            ),
        )


class UniverseTreeContainer(ft.Stack):
    """具体的绘图容器"""

    def __init__(self):
        super().__init__(width=8000, height=8000, clip_behavior=ft.ClipBehavior.NONE)
        self.line_layer = cv.Canvas(width=8000, height=8000)
        self.node_layer = ft.Stack(
            width=8000, height=8000, clip_behavior=ft.ClipBehavior.NONE
        )
        self.controls = [self.line_layer, self.node_layer]


class UniverseCanvas(ft.GestureDetector):
    """
    核心：宇宙画布。
    使用 GestureDetector 包装 InteractiveViewer 以捕获背景点击。
    """

    def __init__(self, state):
        self.state = state
        self.tree_container = UniverseTreeContainer()

        # 1. 核心查看器
        self.viewer = ft.InteractiveViewer(
            content=self.tree_container,
            expand=True,
            min_scale=0.1,
            max_scale=2.0,
            boundary_margin=ft.Margin(2000, 2000, 2000, 2000),
            clip_behavior=ft.ClipBehavior.NONE,
        )

        # 2. 包装器，用于捕获非拖拽的点击
        super().__init__(
            content=self.viewer,
            expand=True,
            on_tap=lambda _: self.state.select_node(None),
        )

    def refresh(self):
        new_nodes = []
        new_lines = []
        self._draw_collect(self.state.universe_root, 0, 0, new_nodes, new_lines)

        self.tree_container.node_layer.controls = new_nodes
        self.tree_container.line_layer.shapes = new_lines

        try:
            if self.page:
                self.page.update()
            else:
                self.update()
        except:
            pass

    def _draw_collect(self, node, x_depth, y_idx, nodes_list, lines_list):
        is_selected = (
            self.state.selected_node and self.state.selected_node.id == node.id
        )
        pos_x = 100 + x_depth * 250
        pos_y = 100 + y_idx * 120

        ui_node = UniverseNodeUI(
            node, is_selected, self.state.select_node, self.state.add_branch
        )
        # 注意：为了让背景 Tap 能穿过 Container，我们将 node 包装层设为不阻止点击（但这可能不可行）
        # 正确做法：给节点设置 on_click，Flet 会优先处理子项点击
        nodes_list.append(ft.Container(content=ui_node, left=pos_x, top=pos_y))

        line_color = "#D1A2FF"
        line_paint = ft.Paint(
            color=line_color, style=ft.PaintingStyle.STROKE, stroke_width=2.0
        )
        arrow_paint = ft.Paint(color=line_color, style=ft.PaintingStyle.FILL)

        child_y = y_idx
        for child in node.children:
            c_pos_x = 100 + (x_depth + 1) * 250
            c_pos_y = 100 + child_y * 120

            lines_list.append(
                cv.Path(
                    [
                        cv.Path.MoveTo(pos_x + 140, pos_y + 30),
                        cv.Path.CubicTo(
                            pos_x + 190,
                            pos_y + 30,
                            pos_x + 190,
                            c_pos_y + 30,
                            c_pos_x,
                            c_pos_y + 30,
                        ),
                    ],
                    paint=line_paint,
                )
            )

            lines_list.append(
                cv.Path(
                    [
                        cv.Path.MoveTo(c_pos_x, c_pos_y + 30),
                        cv.Path.LineTo(c_pos_x - 10, c_pos_y + 24),
                        cv.Path.LineTo(c_pos_x - 10, c_pos_y + 36),
                        cv.Path.Close(),
                    ],
                    paint=arrow_paint,
                )
            )

            self._draw_collect(child, x_depth + 1, child_y, nodes_list, lines_list)
            child_y += 1
