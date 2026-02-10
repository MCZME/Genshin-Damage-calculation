import flet as ft
import flet.canvas as cv
from typing import Callable, Optional, Dict
from core.batch.models import SimulationNode

class UniverseCanvas:
    """
    分支宇宙画布组件 (Flet 原生版)。
    使用 Stack + Canvas 实现高性能的树形交互。
    """
    def __init__(self, root: SimulationNode, on_node_select: Callable[[SimulationNode], None]):
        self.root = root
        self.on_node_select = on_node_select
        self.selected_node_id: Optional[str] = root.id
        
        # UI 坐标缓存 (node_id -> {x, y})
        self.coords: Dict[str, Dict[str, float]] = {}
        
        # 整体偏移 (Panning)
        self.pan_offset = ft.Offset(0, 0)
        
        # 核心容器
        self.nodes_stack = ft.Stack(expand=True)
        self.container = ft.GestureDetector(
            content=self.nodes_stack,
            on_pan_update=self._handle_pan,
            expand=True
        )

    def update_root(self, new_root: SimulationNode):
        self.root = new_root
        self.render()

    def render(self):
        """同步树状态到 Flet Stack"""
        self.nodes_stack.controls.clear()
        self.coords.clear()
        
        # 1. 计算并收集节点位置与连线
        shapes = []
        level_counts = {}

        def traverse(node, level, x):
            y_idx = level_counts.get(level, 0)
            level_counts[level] = y_idx + 1
            
            node_x = x
            node_y = y_idx * 130 + 100
            self.coords[node.id] = {"x": node_x, "y": node_y}
            
            for child in node.children:
                child_x, child_y = traverse(child, level + 1, x + 300)
                
                # 绘制贝塞尔曲线 (基于当前 Panning 偏移)
                lx1, ly1 = node_x + 140, node_y + 32
                lx2, ly2 = child_x, child_y + 32
                lcp_x = (lx1 + lx2) / 2
                
                shapes.append(
                    cv.Path([
                        cv.Path.MoveTo(lx1 + self.pan_offset.x, ly1 + self.pan_offset.y),
                        cv.Path.CubicTo(
                            lcp_x + self.pan_offset.x, ly1 + self.pan_offset.y,
                            lcp_x + self.pan_offset.x, ly2 + self.pan_offset.y,
                            lx2 + self.pan_offset.x, ly2 + self.pan_offset.y
                        )
                    ], paint=ft.Paint(color="#333333", stroke_width=2, style=ft.PaintingStyle.STROKE))
                )
            return node_x, node_y

        traverse(self.root, 0, 100)

        # 2. 添加背景连线层
        self.nodes_stack.controls.append(cv.Canvas(shapes=shapes, expand=True))

        # 3. 添加前景节点层
        for node_id, pos in self.coords.items():
            node_obj = self._find_in_tree(self.root, node_id)
            if not node_obj: continue
            
            is_selected = node_id == self.selected_node_id
            accent = ft.Colors.ORANGE_ACCENT_700 if node_id == "root" else ft.Colors.BLUE_700
            
            card = ft.Container(
                content=ft.Column([
                    ft.Text(node_obj.name or "宇宙变体", size=12, weight=ft.FontWeight.BOLD),
                    ft.Text(f"ID: {node_id}", size=8, color=ft.Colors.WHITE38),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=2),
                width=140,
                height=65,
                bgcolor="#121212",
                border=ft.Border(
                    ft.BorderSide(2 if is_selected else 1.5, accent if is_selected else ft.Colors.with_opacity(0.3, accent)),
                    ft.BorderSide(2 if is_selected else 1.5, accent if is_selected else ft.Colors.with_opacity(0.3, accent)),
                    ft.BorderSide(2 if is_selected else 1.5, accent if is_selected else ft.Colors.with_opacity(0.3, accent)),
                    ft.BorderSide(2 if is_selected else 1.5, accent if is_selected else ft.Colors.with_opacity(0.3, accent))
                ),
                border_radius=12,
                left=pos["x"] + self.pan_offset.x,
                top=pos["y"] + self.pan_offset.y,
                on_click=lambda _, n=node_obj: self._on_click(n),
                animate_position=300,
                shadow=ft.BoxShadow(blur_radius=15 if is_selected else 5, color=ft.Colors.BLACK),
            )
            self.nodes_stack.controls.append(card)

        try:
            self.nodes_stack.update()
        except Exception:
            pass

    def _on_click(self, node):
        self.selected_node_id = node.id
        self.on_node_select(node)
        self.render()

    def _handle_pan(self, e: ft.DragUpdateEvent):
        dx = getattr(e, 'delta_x', getattr(e, 'dx', 0))
        dy = getattr(e, 'delta_y', getattr(e, 'dy', 0))
        self.pan_offset = ft.Offset(self.pan_offset.x + dx, self.pan_offset.y + dy)
        self.render()

    def _find_in_tree(self, root: SimulationNode, target_id: str) -> Optional[SimulationNode]:
        if root.id == target_id: return root
        for child in root.children:
            found = self._find_in_tree(child, target_id)
            if found: return found
        return None