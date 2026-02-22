import flet as ft
from ui.theme import GenshinTheme
from ui.reboot.components.artifact_slot import ArtifactSlot
from ui.reboot.components.property_slider import PropertySlider
from ui.reboot.components.asset_grid import AssetGrid
from ui.reboot.components.member_slot import MemberSlot
from ui.reboot.components.weapon_card import WeaponCard
from ui.state import AppState

class StrategicView(ft.Container):
    """
    重构版战略视图：采用原子化组件架构
    """
    def __init__(self, app_state: AppState = None):
        super().__init__()
        self.app_state = app_state or AppState()
        self.state = self.app_state.strategic_state
        self.current_element = self.state.current_member.get("element", "Neutral")
        self.expand = True
        self.bgcolor = GenshinTheme.BACKGROUND
        self.padding = 0 
        
        # 焦点与缓存管理
        self.all_sliders = []
        self.current_focused = None
        self.workbench_cache = {} 
        self.slot_controls = []

        self._build_ui()

    def _handle_view_click(self, e):
        """点击空白处清除所有焦点"""
        self._clear_all_focus()

    def _clear_all_focus(self, except_slider=None):
        """收起所有滑块的编辑态"""
        for slider in self.all_sliders:
            if slider != except_slider:
                slider.set_edit_mode(False)
        self.current_focused = except_slider

    def _handle_slider_focus(self, target_slider):
        """调度中心：当某个滑块申请编辑态时，关闭其他所有滑块"""
        self._clear_all_focus(except_slider=target_slider)

    def _build_ui(self):
        # 1. 透明交互地面
        self.ground = ft.Container(
            expand=True,
            on_click=self._handle_view_click,
        )
        self.ground.mouse_cursor = ft.MouseCursor.BASIC

        # 2. 顶部操作栏
        self.header = ft.Row([
            ft.Text("战略准备工作台", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ft.Row([
                ft.TextButton("读取配置", icon=ft.Icons.FOLDER_OPEN, on_click=self._handle_config_load_click),
                ft.ElevatedButton("保存当前配置", icon=ft.Icons.SAVE, bgcolor=GenshinTheme.PRIMARY, color=GenshinTheme.ON_PRIMARY, on_click=self._handle_config_save_click),
            ], spacing=10)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        # 3. 左侧编队边栏 (使用原子组件)
        self.slot_controls = [
            MemberSlot(
                i, self.state.team_data[i], 
                is_selected=(i == self.state.current_index),
                on_click=self._handle_member_select,
                on_remove=self._handle_remove_member,
                on_add=self._show_character_picker
            ) for i in range(4)
        ]
        self.sidebar = ft.Column(
            self.slot_controls, 
            width=180, 
            expand=True,
            spacing=10,
            alignment=ft.MainAxisAlignment.START
        )

        # 4. 动态一体化看板内容
        self.workbench_content = ft.Column(
            controls=self._build_workbench_controls(),
            expand=True,
            scroll=ft.ScrollMode.ADAPTIVE,
            spacing=30 
        )

        # 组装主布局容器
        self.main_layout = ft.Container(
            content=ft.Column([
                self.header,
                ft.Row([
                    ft.Container(content=self.sidebar, width=180),
                    ft.VerticalDivider(width=1, color=ft.Colors.with_opacity(0.1, GenshinTheme.ON_SURFACE)),
                    self.workbench_content
                ], expand=True)
            ], spacing=10),
            padding=15,
            expand=True
        )

        self.content = ft.Stack([
            self.ground,
            self.main_layout
        ], expand=True)

    def _build_workbench_controls(self):
        """构建上半区配置与下半区圣遗物的平铺列表"""
        self.all_sliders = []
        member = self.state.current_member
        
        if member.get("id") is None:
            return [
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.PERSON_ADD_ALT_1, size=64, color=ft.Colors.WHITE_24),
                        ft.Text("请在左侧编队中选择或添加一位角色", size=18, weight=ft.FontWeight.W_500, color=ft.Colors.WHITE_54),
                        ft.Text("角色配置与圣遗物装配面板将在此处显示", size=13, color=ft.Colors.WHITE_24),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
                    alignment=ft.Alignment.CENTER,
                    expand=True,
                    padding=100
                )
            ]
        
        def create_managed_slider(label, value, **kwargs):
            s = PropertySlider(
                label=label, value=value, 
                on_focus=self._handle_slider_focus, 
                **kwargs
            )
            self.all_sliders.append(s)
            return s

        # --- 上半区：角色与武器核心配置 ---
        upper_section = ft.Row([
            ft.Column([
                ft.Row([
                    ft.Text("角色基础属性", size=16, weight=ft.FontWeight.BOLD, opacity=0.8),
                    ft.Row([
                        ft.IconButton(ft.Icons.DOWNLOAD, icon_size=16, tooltip="保存为角色模版", on_click=self._handle_char_save_click),
                        ft.IconButton(ft.Icons.UPLOAD, icon_size=16, tooltip="读取角色模版", on_click=self._handle_char_load_click),
                    ], spacing=0)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

                ft.Row([
                    create_managed_slider(
                        "等级", value=int(member['level']), 
                        discrete_values=[1, 20, 40, 50, 60, 70, 80, 90, 95, 100],
                        element=member['element'],
                        on_change=lambda v: self._handle_stat_change("level", str(v))
                    ),
                    create_managed_slider(
                        "命之座", value=int(member['constellation']), 
                        min_val=0, max_val=6, divisions=6,
                        element=member['element'],
                        on_change=lambda v: self._handle_stat_change("constellation", str(v))
                    ),
                ], spacing=20),
                ft.Divider(height=10, color="transparent"),
                ft.Text("天赋等级配置", size=16, weight=ft.FontWeight.BOLD, opacity=0.8),
                ft.Row([
                    create_managed_slider("普通攻击", value=int(member['talents']['na']), min_val=1, max_val=10, divisions=9, element=member['element'], on_change=lambda v: self._handle_talent_change("na", str(v))),
                    create_managed_slider("元素战技", value=int(member['talents']['e']), min_val=1, max_val=10, divisions=9, element=member['element'], on_change=lambda v: self._handle_talent_change("e", str(v))),
                    create_managed_slider("元素爆发", value=int(member['talents']['q']), min_val=1, max_val=10, divisions=9, element=member['element'], on_change=lambda v: self._handle_talent_change("q", str(v))),
                ], spacing=15)
            ], expand=True, spacing=10),
            
            ft.VerticalDivider(width=1, color=ft.Colors.WHITE_10),
            
            # 武器配置卡 (原子组件)
            WeaponCard(
                member, create_managed_slider,
                on_picker_click=self._show_weapon_picker,
                on_stat_change=self._handle_weapon_stat_change
            )
        ], spacing=30, vertical_alignment=ft.CrossAxisAlignment.START)

        # --- 下半区：圣遗物地平线 ---
        lower_section = ft.Column([
            ft.Row([
                ft.Text("圣遗物装配中心", size=16, weight=ft.FontWeight.BOLD, opacity=0.8),
                ft.Row([
                    ft.TextButton("保存套装", icon=ft.Icons.SAVE_ALT, on_click=self._handle_arti_save_click),
                    ft.TextButton("加载套装", icon=ft.Icons.UPLOAD_FILE, on_click=self._handle_arti_load_click),
                ], spacing=10),
                ft.Text("(套装效果将根据部件名称自动判定)", size=12, italic=True, color=GenshinTheme.TEXT_SECONDARY),
            ], spacing=20, alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),

            ft.Row(
                [ArtifactSlot(slot, member['artifacts'][slot], element=member['element']) for slot in ["Flower", "Plume", "Sands", "Goblet", "Circlet"]],
                scroll=ft.ScrollMode.ADAPTIVE,
                spacing=15,
            )
        ], spacing=15)

        return [
            upper_section, 
            ft.Divider(height=1, color=ft.Colors.WHITE_10), 
            lower_section,
            ft.Container(height=20) 
        ]

    def _show_character_picker(self, index: int):
        """弹出全角色 AssetGrid 选择器"""
        mock_characters = []
        for name, info in self.app_state.char_map.items():
            mock_characters.append({
                "id": info["id"],
                "name": name,
                "rarity": info.get("rarity", 5),
                "element": info["element"],
                "type": info["type"],
                "is_implemented": name in self.app_state.implemented_chars
            })

        def on_char_select(char_id):
            selected_char = next(c for c in mock_characters if c['id'] == char_id)
            self._handle_add_member(index, selected_char)
            self.page.pop_dialog()

        picker_grid = AssetGrid(mock_characters, on_select=on_char_select)
        
        dialog = ft.AlertDialog(
            title=ft.Text("选择角色", size=18, weight=ft.FontWeight.BOLD),
            content=ft.Container(picker_grid, width=500, height=400),
            bgcolor=GenshinTheme.SURFACE,
        )
        self.page.show_dialog(dialog)

    def _handle_add_member(self, index: int, char_data: dict):
        self.state.add_member(index, char_data)
        self.app_state.events.notify("strategic")

    def _handle_remove_member(self, index: int):
        self.state.remove_member(index)
        self.app_state.events.notify("strategic")

    def _refresh_all(self):
        """完全同步的状态刷新"""
        self.workbench_cache.clear()
        for i in range(4):
            self.slot_controls[i].update_state(self.state.team_data[i], (i == self.state.current_index))
        self._handle_member_select(self.state.current_index)

    def _handle_member_select(self, index: int):
        """同步全局角色选中态与工作台渲染，并精准刷新 UI"""
        self.state.select_member(index)
        self.current_element = self.state.current_member.get("element", "Neutral")

        # 局部刷新侧边栏
        for i in range(4):
            self.slot_controls[i].update_state(self.state.team_data[i], (i == self.state.current_index))
        
        # 切换中央工作台
        if index not in self.workbench_cache:
            self.workbench_cache[index] = self._build_workbench_controls()
            
        self.workbench_content.controls = self.workbench_cache[index]
        
        try:
            self.sidebar.update()
            self.workbench_content.update()
        except: pass

    def _handle_stat_change(self, key: str, new_val: str):
        self.state.current_member[key] = new_val
        self.app_state.events.notify("strategic")

    def _handle_talent_change(self, key: str, new_val: str):
        """处理天赋等级变更"""
        self.state.current_member['talents'][key] = new_val
        self.app_state.events.notify("strategic")

    def _handle_weapon_change(self, weapon_data: dict):
        # 更新当前成员的武器，触发整体刷新
        self.state.current_member['weapon']['id'] = weapon_data['id']
        self.app_state.events.notify("strategic")

    def _handle_weapon_stat_change(self, key: str, val: str):
        """处理武器等级/精炼变更，同步刷新侧边栏"""
        self.state.current_member['weapon'][key] = val
        self.app_state.events.notify("strategic")

    def _show_weapon_picker(self):
        """弹出武器库选择器"""
        weapon_type = self.state.current_member.get('type', '单手剑')
        repo_weapons = self.app_state.weapon_map.get(weapon_type, [])
        
        mock_weapons = []
        seen_names = set() 
        for w_dict in repo_weapons:
            name = w_dict["name"]
            if name in seen_names: continue
            seen_names.add(name)
            
            mock_weapons.append({
                "id": name, 
                "name": name,
                "rarity": w_dict["rarity"],
                "type": weapon_type, 
                "element": self.state.current_member.get('element', '物理'),
                "is_implemented": name in self.app_state.implemented_weapons
            })

        def on_weapon_select(wid):
            selected_w = next(w for w in mock_weapons if w['id'] == wid)
            self._handle_weapon_change(selected_w)
            self.page.pop_dialog()

        picker_grid = AssetGrid(
            mock_weapons, on_select=on_weapon_select, 
            allow_filter_type=False, allow_filter_element=False
        )
        
        dialog = ft.AlertDialog(
            title=ft.Text("选择武器装备", size=18, weight=ft.FontWeight.BOLD),
            content=ft.Container(picker_grid, width=500, height=400),
            bgcolor=GenshinTheme.SURFACE,
        )
        self.page.show_dialog(dialog)

    async def _handle_config_load_click(self, e):
        if await self.page.persistence.load_config():
            self.app_state.events.notify("strategic")

    async def _handle_config_save_click(self, e):
        await self.page.persistence.save_config()

    async def _handle_char_save_click(self, e):
        await self.page.persistence.save_character_template(self.state.current_index)

    async def _handle_char_load_click(self, e):
        if await self.page.persistence.load_character_template(self.state.current_index):
            self.app_state.events.notify("strategic")

    async def _handle_arti_save_click(self, e):
        await self.page.persistence.save_artifact_set(self.state.current_index)

    async def _handle_arti_load_click(self, e):
        if await self.page.persistence.load_artifact_set(self.state.current_index):
            self.app_state.events.notify("strategic")
