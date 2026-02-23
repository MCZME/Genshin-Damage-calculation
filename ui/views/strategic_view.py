import flet as ft
from ui.theme import GenshinTheme
from ui.components.artifact_slot import ArtifactSlot
from ui.components.property_slider import PropertySlider
from ui.components.asset_grid import AssetGrid
from ui.components.member_slot import MemberSlot
from ui.components.weapon_card import WeaponCard
from ui.states.app_state import AppState

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
        self.slot_controls = []

        # 核心：单工作台持久化引用
        self.lvl_slider = None
        self.const_slider = None
        self.na_slider = None
        self.e_slider = None
        self.q_slider = None
        self.weapon_card = None
        self.artifact_slots = {} # slot_name -> ArtifactSlot

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

        # 4. 静态工作台构建 (仅构建一次)
        self.workbench_panel = self._init_static_workbench()
        
        # 使用 AnimatedSwitcher 处理“空位”与“工作台”切换
        self.workbench_switcher = ft.AnimatedSwitcher(
            content=self.workbench_panel,
            expand=True,
            transition=ft.AnimatedSwitcherTransition.FADE,
            duration=300
        )

        # 组装主布局容器
        self.main_layout = ft.Container(
            content=ft.Column([
                self.header,
                ft.Row([
                    ft.Container(content=self.sidebar, width=180),
                    ft.VerticalDivider(width=1, color=ft.Colors.with_opacity(0.1, GenshinTheme.ON_SURFACE)),
                    ft.Container(content=self.workbench_switcher, expand=True)
                ], expand=True)
            ], spacing=10),
            padding=15,
            expand=True
        )

        self.content = ft.Stack([
            self.ground,
            self.main_layout
        ], expand=True)
        
        # 初始化显示
        self._sync_workbench_data()

    def _init_static_workbench(self) -> ft.Control:
        """初始化一套永久存在的控件树"""
        self.all_sliders = []
        
        # 使用 StrategicState 提供的标准空模板进行初始化
        base_mock = self.state._create_empty_member()
        
        def create_managed_slider(label, value, **kwargs):
            s = PropertySlider(
                label=label, value=value, 
                on_focus=self._handle_slider_focus, 
                **kwargs
            )
            self.all_sliders.append(s)
            return s

        # --- 上半区：角色基础属性 ---
        self.lvl_slider = create_managed_slider("等级", 90, discrete_values=[1, 20, 40, 50, 60, 70, 80, 90, 95, 100])
        self.const_slider = create_managed_slider("命之座", 0, min_val=0, max_val=6, divisions=6)
        
        self.na_slider = create_managed_slider("普通攻击", 10, min_val=1, max_val=10, divisions=9)
        self.e_slider = create_managed_slider("元素战技", 10, min_val=1, max_val=10, divisions=9)
        self.q_slider = create_managed_slider("元素爆发", 10, min_val=1, max_val=10, divisions=9)

        # 绑定事件
        self.lvl_slider.on_change_callback = lambda v: self._handle_stat_change("level", str(v))
        self.const_slider.on_change_callback = lambda v: self._handle_stat_change("constellation", str(v))
        self.na_slider.on_change_callback = lambda v: self._handle_talent_change("na", str(v))
        self.e_slider.on_change_callback = lambda v: self._handle_talent_change("e", str(v))
        self.q_slider.on_change_callback = lambda v: self._handle_talent_change("q", str(v))

        upper_section = ft.Row([
            ft.Column([
                ft.Row([
                    ft.Text("角色基础属性", size=16, weight=ft.FontWeight.BOLD, opacity=0.8),
                    ft.Row([
                        ft.IconButton(ft.Icons.DOWNLOAD, icon_size=16, tooltip="保存为角色模版", on_click=self._handle_char_save_click),
                        ft.IconButton(ft.Icons.UPLOAD, icon_size=16, tooltip="读取角色模版", on_click=self._handle_char_load_click),
                    ], spacing=0)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

                ft.Row([self.lvl_slider, self.const_slider], spacing=20),
                ft.Divider(height=10, color="transparent"),
                ft.Text("天赋等级配置", size=16, weight=ft.FontWeight.BOLD, opacity=0.8),
                ft.Row([self.na_slider, self.e_slider, self.q_slider], spacing=15)
            ], expand=True, spacing=10),
            
            ft.VerticalDivider(width=1, color=ft.Colors.WHITE_10),
        ], spacing=30, vertical_alignment=ft.CrossAxisAlignment.START)

        # 武器配置卡
        self.weapon_card = WeaponCard(
            base_mock, 
            create_managed_slider,
            on_picker_click=self._show_weapon_picker,
            on_stat_change=self._handle_weapon_stat_change
        )
        upper_section.controls.append(self.weapon_card)

        # --- 下半区：圣遗物 ---
        self.artifact_slots = {
            slot: ArtifactSlot(slot, base_mock['artifacts'][slot], on_change=lambda: self.app_state.events.notify("strategic"))
            for slot in ["Flower", "Plume", "Sands", "Goblet", "Circlet"]
        }

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
                list(self.artifact_slots.values()),
                scroll=ft.ScrollMode.ADAPTIVE,
                spacing=15,
            )
        ], spacing=15)

        return ft.Column(
            controls=[
                upper_section, 
                ft.Divider(height=1, color=ft.Colors.WHITE_10), 
                lower_section,
                ft.Container(height=20) 
            ],
            expand=True,
            scroll=ft.ScrollMode.ADAPTIVE,
            spacing=30 
        )

    def _sync_workbench_data(self):
        """核心：将内存状态同步到静态控件（不重建）"""
        member = self.state.current_member
        
        # 处理空状态
        if member.get("id") is None:
            self.workbench_switcher.content = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.PERSON_ADD_ALT_1, size=64, color=ft.Colors.WHITE_24),
                    ft.Text("请在左侧编队中选择或添加一位角色", size=18, weight=ft.FontWeight.W_500, color=ft.Colors.WHITE_54),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
                alignment=ft.Alignment.CENTER, expand=True
            )
            return

        # 切换回正常面板
        self.workbench_switcher.content = self.workbench_panel
        
        # 1. 同步角色滑块
        elem = member['element']
        self.lvl_slider.update_state(int(member['level']), elem, skip_update=True)
        self.const_slider.update_state(int(member['constellation']), elem, skip_update=True)
        self.na_slider.update_state(int(member['talents']['na']), elem, skip_update=True)
        self.e_slider.update_state(int(member['talents']['e']), elem, skip_update=True)
        self.q_slider.update_state(int(member['talents']['q']), elem, skip_update=True)
        
        # 2. 同步武器卡
        self.weapon_card.update_state(member, skip_update=True)
        
        # 3. 同步圣遗物槽位
        for slot_name, slot_ctrl in self.artifact_slots.items():
            slot_ctrl.update_state(member['artifacts'][slot_name], elem, skip_update=True)

    def _handle_member_select(self, index: int):
        """同步全局角色选中态与工作台渲染，并精准刷新 UI"""
        self.state.select_member(index)
        self.current_element = self.state.current_member.get("element", "Neutral")

        # 1. 批量更新侧边栏 (不刷新)
        for i in range(4):
            self.slot_controls[i].update_state(self.state.team_data[i], (i == self.state.current_index), skip_update=True)
        
        # 2. 同步工作台数据 (不刷新)
        self._sync_workbench_data()
        
        # 3. 发起一次总重绘
        try:
            self.sidebar.update()
            self.workbench_switcher.update()
        except: pass

    def _refresh_all(self):
        """完全同步的状态刷新"""
        self._handle_member_select(self.state.current_index)

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
