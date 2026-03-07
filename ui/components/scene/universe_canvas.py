import flet as ft
import flet.canvas as cv
from ui.theme import GenshinTheme

@ft.component
def UniverseNodeUI(node, is_selected, on_click, on_add):
    """画布上的物理节点 (声明式)"""
    accent = GenshinTheme.PRIMARY if node.id != "root" else ft.Colors.AMBER
    is_managed = getattr(node, "is_managed", False)

    leaf_badge = ft.Container(
        content=ft.Text("SAMPLE", size=7, weight=ft.FontWeight.W_900, color=GenshinTheme.ON_PRIMARY),
        bgcolor=GenshinTheme.PRIMARY,
        padding=ft.Padding.symmetric(horizontal=5, vertical=1),
        border_radius=ft.border_radius.only(top_left=8, bottom_right=10),
        visible=len(node.children) == 0,
        right=0, bottom=0,
    )

    return ft.Container(
        content=ft.Stack([
            ft.Column([
                ft.Row([
                    ft.Text(
                        node.name or "宇宙变体",
                        size=11, weight=ft.FontWeight.BOLD, expand=True,
                        color=ft.Colors.AMBER_100 if is_managed else GenshinTheme.ON_SURFACE,
                    ),
                    ft.IconButton(
                        ft.Icons.ADD_CIRCLE_OUTLINE, icon_size=14,
                        on_click=lambda _: on_add(node),
                        opacity=0.6, icon_color=GenshinTheme.PRIMARY,
                    ),
                ], spacing=5),
                ft.Text(
                    node.rule.label if node.rule else ("BASE" if node.id == "root" else "Inherited"),
                    size=9, opacity=0.4, color=GenshinTheme.TEXT_SECONDARY,
                ),
            ], spacing=2, tight=True),
            leaf_badge,
        ]),
        width=140, padding=10, bgcolor=GenshinTheme.SURFACE,
        border=ft.border.all(2, accent if is_selected else (ft.Colors.AMBER_900 if is_managed else None)),
        border_radius=12,
        on_click=lambda _: on_click(node),
        shadow=ft.BoxShadow(blur_radius=15 if is_selected else 5, color="rgba(0,0,0,0.3)"),
    )

class UniverseCanvas:
    """
    宇宙画布 (V4.5 全声明式重构版)。
    不再继承 Control，而是通过 build() 返回 UI 树。
    """
    def __init__(self, state):
        self.state = state

    @ft.component
    def build(self):
        # 1. 订阅状态 (通过读取 observable)
        root = self.state.universe_root
        selected_node = self.state.selected_node
        _trigger = self.state.mutation_counter # 强制重绘触发器

        # 2. 递归构建 UI 元素列表
        nodes_list = []
        lines_list = []

        def _draw_recursive(node, x_depth, y_idx):
            is_selected = (selected_node and selected_node.id == node.id)
            pos_x = 100 + x_depth * 250
            pos_y = 100 + y_idx * 120

            # 声明式实例化
            ui_node = UniverseNodeUI(
                node=node, is_selected=is_selected, 
                on_click=self.state.select_node, on_add=self.state.add_branch
            )
            nodes_list.append(ft.Container(content=ui_node, left=pos_x, top=pos_y))

            line_color = "#D1A2FF"
            line_paint = ft.Paint(color=line_color, style=ft.PaintingStyle.STROKE, stroke_width=2.0)
            arrow_paint = ft.Paint(color=line_color, style=ft.PaintingStyle.FILL)

            child_y = y_idx
            for child in node.children:
                c_pos_x = 100 + (x_depth + 1) * 250
                c_pos_y = 100 + child_y * 120
                lines_list.append(
                    cv.Path([
                        cv.Path.MoveTo(pos_x + 140, pos_y + 30),
                        cv.Path.CubicTo(pos_x + 190, pos_y + 30, pos_x + 190, c_pos_y + 30, c_pos_x, c_pos_y + 30),
                    ], paint=line_paint)
                )
                lines_list.append(
                    cv.Path([
                        cv.Path.MoveTo(c_pos_x, c_pos_y + 30),
                        cv.Path.LineTo(c_pos_x - 10, c_pos_y + 24),
                        cv.Path.LineTo(c_pos_x - 10, c_pos_y + 36),
                        cv.Path.Close(),
                    ], paint=arrow_paint)
                )
                _draw_recursive(child, x_depth + 1, child_y)
                child_y += 1

        _draw_recursive(root, 0, 0)

        # 3. 组装容器
        tree_container = ft.Stack([
            cv.Canvas(shapes=lines_list, width=8000, height=8000),
            ft.Stack(controls=nodes_list, width=8000, height=8000, clip_behavior=ft.ClipBehavior.NONE)
        ], width=8000, height=8000, clip_behavior=ft.ClipBehavior.NONE)

        viewer = ft.InteractiveViewer(
            content=tree_container, expand=True, min_scale=0.1, max_scale=2.0,
            boundary_margin=ft.Margin(2000, 2000, 2000, 2000), clip_behavior=ft.ClipBehavior.NONE,
        )

        return ft.GestureDetector(
            content=viewer, expand=True, on_tap=lambda _: self.state.select_node(None),
        )
