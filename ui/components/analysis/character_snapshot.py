import flet as ft
from ui.components.analysis.base_widget import BaseAnalysisWidget
from ui.theme import GenshinTheme

class CharacterSnapshotWidget(BaseAnalysisWidget):
    """
    角色快照组件：展示特定帧的面板属性与生效增益。
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config["target_id"] = None # 默认观察 1 号位
        self.team_members = []
        self._build_ui_structure()

    def _build_ui_structure(self):
        # 1. 属性网格
        self.stat_grid = ft.Column(spacing=5, scroll=ft.ScrollMode.AUTO)
        
        # 2. Buff 列表
        self.buff_list = ft.Row(wrap=True, spacing=5)
        
        # 3. 组装内容区
        self.body.content = ft.Column([
            ft.Text("实时属性面板", size=11, weight=ft.FontWeight.BOLD, opacity=0.7),
            ft.Container(
                content=self.stat_grid,
                height=150,
                bgcolor="rgba(0,0,0,0.1)",
                border_radius=10,
                padding=10
            ),
            ft.Divider(height=10, color="transparent"),
            ft.Text("生效增益 (Modifiers)", size=11, weight=ft.FontWeight.BOLD, opacity=0.7),
            ft.Container(
                content=self.buff_list,
                expand=True
            )
        ], spacing=5)

    async def load_data(self):
        """初始加载：获取队伍成员列表以配置菜单"""
        if not self.adapter: return
        
        # 简单查询一下有谁
        frame_data = await self.adapter.get_frame(0)
        if frame_data and frame_data["team"]:
            self.team_members = frame_data["team"]
            if self.config["target_id"] is None:
                self.config["target_id"] = self.team_members[0]["entity_id"]
                self.update_subtitle(f"({self.team_members[0]['name']})")
        
        self.refresh_settings_menu()
        await self.sync_frame(self.current_frame)

    async def sync_frame(self, frame_id: int):
        """同步帧数据：刷新面板数值"""
        await super().sync_frame(frame_id)
        if not self.adapter: return

        # 1. 获取帧快照
        data = await self.adapter.get_frame(frame_id)
        if not data: return

        # 2. 找到目标角色
        target_char = next((c for c in data["team"] if c["entity_id"] == self.config["target_id"]), None)
        if not target_char: return

        # 3. 渲染属性
        self.stat_grid.controls.clear()
        stats = target_char.get("stats", {})
        
        # 定义优先展示的关键属性
        core_stats = ["HP", "ATK", "DEF", "元素精通", "暴击率", "暴击伤害", "元素充能效率"]
        for stat_name in core_stats:
            val = stats.get(stat_name, 0)
            # 格式化显示
            display_val = f"{val*100:.1f}%" if "率" in stat_name or "伤害" in stat_name or "效率" in stat_name else f"{val:,.0f}"
            self.stat_grid.controls.append(
                ft.Row([
                    ft.Text(stat_name, size=11, opacity=0.6, expand=True),
                    ft.Text(display_val, size=11, weight=ft.FontWeight.BOLD),
                ])
            )

        # 4. 渲染 Buff
        self.buff_list.controls.clear()
        for mod in target_char.get("active_modifiers", []):
            self.buff_list.controls.append(
                ft.Container(
                    content=ft.Text(mod["name"], size=9, color=GenshinTheme.PRIMARY),
                    padding=ft.Padding(5, 3, 5, 3),
                    bgcolor="rgba(209, 162, 255, 0.1)",
                    border=ft.Border.all(1, "rgba(209, 162, 255, 0.3)"),
                    border_radius=5,
                    tooltip=f"{mod.get('stat', '')}: {mod.get('value', '')}"
                )
            )
        
        try:
            self.update()
        except: pass

    def get_settings_items(self):
        items = []
        if hasattr(self, 'team_members'):
            for char in self.team_members:
                items.append(
                    ft.PopupMenuItem(
                        content=ft.Text(f"观察: {char['name']}"), 
                        on_click=lambda e, cid=char['entity_id'], name=char['name']: self._switch_target(cid, name)
                    )
                )
        return items

    def _switch_target(self, entity_id, name):
        self.config["target_id"] = entity_id
        self.update_subtitle(f"({name})")
        self.page.run_task(self.sync_frame, self.current_frame)
