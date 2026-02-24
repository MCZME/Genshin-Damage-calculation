import flet as ft
import math
from ui.theme import GenshinTheme
from ui.components.analysis.base_widget import AnalysisTile
from core.persistence.adapter import ReviewDataAdapter

class ReplayTile(AnalysisTile):
    """
    磁贴：物理重演投影。
    2D 俯视图展示角色与目标的位移与相对位置。
    """
    def __init__(self):
        super().__init__("战况物理投影", ft.Icons.VIDEOGAME_ASSET_OUTLINED)
        self.trajectories = {}
        self.current_frame = 0
        self.scale = 20 # 坐标缩放比例 (1米 = 20像素)
        
        # 预定义颜色映射
        self.entity_colors = {}
        
        # UI 控件
        self.canvas = ft.Canvas(
            expand=True,
            on_resize=self._handle_resize,
            shapes=[
                # 背景网格 (后续绘制)
            ]
        )
        self.content = ft.Container(
            content=self.canvas,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            bgcolor="rgba(0,0,0,0.1)",
            border_radius=12
        )

    def update_data(self, trajectories):
        self.trajectories = trajectories
        # 为每个实体分配固定颜色
        colors = [ft.Colors.AMBER_400, ft.Colors.BLUE_400, ft.Colors.PURPLE_400, ft.Colors.GREEN_400, ft.Colors.RED_400]
        for i, name in enumerate(self.trajectories.keys()):
            self.entity_colors[name] = colors[i % len(colors)]
        self._draw_replay()

    def load_data(self, adapter: ReviewDataAdapter):
        pass

    def sync_to_frame(self, frame_id: int):
        self.current_frame = frame_id
        self._draw_replay()

    def _draw_replay(self):
        """核心绘制逻辑：每一帧清除并重绘 Canvas"""
        if not self.trajectories: return
        
        shapes = []
        cx, cy = 0, 0 # 中心点偏移量 (由 resize 确定)
        # 获取 Canvas 实际尺寸
        width = getattr(self.canvas, "width", 400) or 400
        height = getattr(self.canvas, "height", 300) or 300
        cx, cy = width / 2, height / 2

        # 1. 绘制网格
        for i in range(-10, 11):
            # 纵线
            shapes.append(ft.cv.CanvasLine(
                cx + i * self.scale, cy - 200, 
                cx + i * self.scale, cy + 200, 
                ft.Paint(color="rgba(255,255,255,0.05)", stroke_width=1)
            ))
            # 横线
            shapes.append(ft.cv.CanvasLine(
                cx - 200, cy + i * self.scale, 
                cx + 200, cy + i * self.scale, 
                ft.Paint(color="rgba(255,255,255,0.05)", stroke_width=1)
            ))

        # 2. 绘制实体
        for name, points in self.trajectories.items():
            # 查找当前帧最接近的点 (轨迹是有序的)
            point = self._find_point_at_frame(points, self.current_frame)
            if not point: continue
            
            x, z = point['pos']
            color = self.entity_colors.get(name, ft.Colors.WHITE)
            is_on = point.get('on', True)
            
            # 画实体点 (在场实心，后台空心)
            paint = ft.Paint(color=color, style=ft.PaintingStyle.FILL if is_on else ft.PaintingStyle.STROKE, stroke_width=2)
            shapes.append(ft.cv.CanvasCircle(cx + x * self.scale, cy - z * self.scale, 8, paint))
            
            # 画实体名称
            shapes.append(ft.cv.CanvasText(
                cx + x * self.scale + 12, cy - z * self.scale - 12,
                text=name,
                style=ft.TextStyle(size=10, color=color, weight=ft.FontWeight.W_600)
            ))
            
            # 画运动残影 (前 10 帧)
            tail = self._get_tail_points(points, self.current_frame, 10)
            if len(tail) > 1:
                path_points = []
                for tp in tail:
                    tx, tz = tp['pos']
                    path_points.append(ft.Offset(cx + tx * self.scale, cy - tz * self.scale))
                
                shapes.append(ft.cv.CanvasPath(
                    [ft.cv.CanvasPathMoveTo(path_points[0].x, path_points[0].y)] + 
                    [ft.cv.CanvasPathLineTo(p.x, p.y) for p in path_points[1:]],
                    ft.Paint(color=color, stroke_width=2, style=ft.PaintingStyle.STROKE, stroke_cap=ft.StrokeCap.ROUND, opacity=0.3)
                ))

        self.canvas.shapes = shapes
        try: self.canvas.update()
        except: pass

    def _find_point_at_frame(self, points, frame):
        # 二分查找或简单查找最接近的帧
        last = None
        for p in points:
            if p['f'] > frame: break
            last = p
        return last

    def _get_tail_points(self, points, frame, depth):
        result = []
        for p in points:
            if frame - depth <= p['f'] <= frame:
                result.append(p)
            if p['f'] > frame: break
        return result

    def _handle_resize(self, e):
        # 强制重绘以适配新中心点
        self._draw_replay()
