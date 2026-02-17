import flet as ft
import flet_charts as fch
from ui.components.analysis.base_widget import BaseAnalysisWidget
from ui.theme import GenshinTheme

class DamageDistributionWidget(BaseAnalysisWidget):
    """
    伤害分布饼图组件 (V3.2)
    展示按角色或按元素的总伤害占比。
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config["mode"] = "character" # 默认按角色分布
        self._setup_pie()

    def _setup_pie(self):
        # 1. 构造饼图
        self.chart = fch.PieChart(
            sections=[],
            sections_space=2,
            center_space_radius=40,
            expand=True,
        )

        # 2. 构造图例容器
        self.legend = ft.Column(spacing=5, scroll=ft.ScrollMode.AUTO)

        # 3. 布局
        self.body.content = ft.Row([
            ft.Container(content=self.chart, expand=True, padding=10),
            ft.VerticalDivider(width=1, color="rgba(255,255,255,0.05)"),
            ft.Container(content=self.legend, width=150, padding=10)
        ], spacing=0)

    async def load_data(self):
        """加载数据并计算分布占比"""
        if not self.adapter: return
        
        raw_data = await self.adapter.get_dps_data()
        if not raw_data:
            self.update_subtitle("(无伤害数据)")
            return

        # 聚合数据
        stats = {}
        total_dmg = 0
        mode = self.config["mode"]

        for d in raw_data:
            key = d["source"] if mode == "character" else d["element"]
            stats[key] = stats.get(key, 0) + d["value"]
            total_dmg += d["value"]

        if total_dmg == 0: return

        # 准备颜色映射 (如果是元素模式，使用主题色)
        colors = [
            ft.Colors.AMBER, ft.Colors.BLUE, ft.Colors.RED, 
            ft.Colors.GREEN, ft.Colors.PURPLE, ft.Colors.CYAN
        ]

        # 构造饼图块和图例
        self.chart.sections.clear()
        self.legend.controls.clear()
        
        sorted_stats = sorted(stats.items(), key=lambda x: x[1], reverse=True)
        
        for i, (key, val) in enumerate(sorted_stats):
            percent = val / total_dmg
            color = GenshinTheme.get_element_color(key) if mode == "element" else colors[i % len(colors)]
            
            # 饼图块
            self.chart.sections.append(
                fch.PieChartSection(
                    value=val,
                    title=f"{percent*100:.0f}%" if percent > 0.05 else "",
                    title_style=ft.TextStyle(size=10, weight=ft.FontWeight.BOLD),
                    color=color,
                    radius=30,
                )
            )
            
            # 图例项
            self.legend.controls.append(
                ft.Row([
                    ft.Container(width=8, height=8, bgcolor=color, border_radius=4),
                    ft.Column([
                        ft.Text(key, size=10, weight=ft.FontWeight.BOLD, no_wrap=True),
                        ft.Text(f"{val/10000:.1f}w ({percent*100:.1f}%)", size=9, opacity=0.5),
                    ], spacing=0)
                ], spacing=8)
            )

        self.update_subtitle(f"(按{'角色' if mode == 'character' else '元素'}分布)")
        self.refresh_settings_menu()
        
        try:
            self.chart.update()
            self.update()
        except: pass

    def get_settings_items(self):
        return [
            ft.PopupMenuItem(content=ft.Text("维度: 按角色占比"), on_click=lambda _: self._switch_mode("character")),
            ft.PopupMenuItem(content=ft.Text("维度: 按元素占比"), on_click=lambda _: self._switch_mode("element")),
        ]

    def _switch_mode(self, mode):
        self.config["mode"] = mode
        self.page.run_task(self.load_data)
