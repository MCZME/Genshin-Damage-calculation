import flet as ft
from ui.theme import GenshinTheme
from ui.reboot.components.artifact_slot import ArtifactSlot
from ui.reboot.components.property_slider import PropertySlider
from ui.reboot.components.asset_grid import AssetGrid
from ui.state import AppState

class StrategicView(ft.Container):
    """
    重构版战略视图：完全摒弃左右栏旧架构，全屏响应式布局
    """
    def __init__(self, app_state: AppState = None):
        super().__init__()
        self.app_state = app_state or AppState()
        self.state = self.app_state.strategic_state
        self.current_element = self.state.current_member.get("element", "Neutral")
        self.expand = True
        self.bgcolor = GenshinTheme.BACKGROUND
        self.padding = 0 
        
        # 焦点管理
        self.all_sliders = []
        self.current_focused = None




        self._build_ui()

    def did_mount(self):
        pass



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
        # 每次构建前清空滑块追踪列表
        self.all_sliders = []
        
        # 1. 透明交互地面 (负责拦截空白点击并保持基础光标)
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

        # 3. 左侧编队边栏 (持久化缓存)
        self.slot_controls = [self._build_member_slot(i) for i in range(4)]
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
                    # 侧边栏：锁定宽度，允许纵向对齐起效
                    ft.Container(content=self.sidebar, width=180),
                    ft.VerticalDivider(width=1, color=ft.Colors.with_opacity(0.1, GenshinTheme.ON_SURFACE)),
                    # 工作台：占据剩余所有宽度
                    self.workbench_content
                ], expand=True)
            ], spacing=10),
            padding=15,
            expand=True
        )

        # 5. 使用 Stack 叠加地面与内容
        # 确保 ground 在底层，main_layout 在顶层但其空白处透传点击给 ground（Flet 容器透明背景默认透传）
        self.content = ft.Stack([
            self.ground,
            self.main_layout
        ], expand=True)

    def _build_workbench_controls(self):
        """构建上半区配置与下半区圣遗物的平铺列表"""
        # 性能修复：重置滑块追踪列表，防止切换角色时旧句柄堆积导致焦点管理变慢
        self.all_sliders = []
        member = self.state.current_member
        
        # 拦截：如果当前槽位未配置角色，显示引导占位内容
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
        
        # 局部工厂函数：创建带焦点管理的滑块
        def create_managed_slider(label, value, **kwargs):
            s = PropertySlider(
                label=label, value=value, 
                on_focus=self._handle_slider_focus, 
                **kwargs
            )
            self.all_sliders.append(s)
            return s

        # --- 上半区：角色与武器核心配置 (Workbench) ---
        upper_section = ft.Row([
            # 角色基础
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
            
            # 武器配置
            self._build_integrated_weapon_card(member, create_managed_slider)
        ], spacing=30, vertical_alignment=ft.CrossAxisAlignment.START)

        # --- 下半区：圣遗物地平线 (Horizon) ---
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

    def _build_integrated_weapon_card(self, member, slider_factory):
        """一体化武器配置卡"""
        w = member.get('weapon', {"id": None, "level": "90", "refinement": "1"})
        is_empty = w.get('id') is None
        
        # 武器图标预览
        weapon_type = member.get('type', '单手剑')
        weapon_icon = GenshinTheme.get_weapon_icon(weapon_type)
        
        weapon_icon_container = ft.Container(
            content=ft.Icon(ft.Icons.SHIELD if is_empty else weapon_icon, size=30, color=ft.Colors.WHITE_24),
            width=80, height=80,
            bgcolor=ft.Colors.BLACK26,
            border_radius=8,
            border=ft.Border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
            alignment=ft.Alignment.CENTER,
            on_click=lambda _: self._show_weapon_picker()
        )
        weapon_icon_container.mouse_cursor = ft.MouseCursor.CLICK
        
        # 组装 Row
        controls_row = ft.Row([
            weapon_icon_container,
            # 武器参数
            ft.Column([
                ft.Text(w['id'].upper() if not is_empty else "未装备武器", size=12, weight=ft.FontWeight.BOLD),
                slider_factory("精炼", value=int(w['refinement']), min_val=1, max_val=5, divisions=4, element=member['element'], on_change=lambda v: self._handle_weapon_stat_change("refinement", str(v))),
                slider_factory("等级", value=int(w['level']), discrete_values=[1, 20, 40, 50, 60, 70, 80, 90], element=member['element'], on_change=lambda v: self._handle_weapon_stat_change("level", str(v))),
            ], spacing=5)
        ], spacing=15)
        
        return ft.Container(
            content=ft.Column([
                ft.Text("武器装备", size=14, weight=ft.FontWeight.BOLD, opacity=0.6),
                controls_row
            ], spacing=10),
            padding=ft.Padding(20, 15, 20, 15),
            bgcolor=ft.Colors.with_opacity(0.02, ft.Colors.WHITE),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.05, ft.Colors.WHITE)),
            border_radius=12,
            width=380
        )

    def _build_member_slot(self, index: int):
        member = self.state.team_data[index]
        is_empty = member.get("id") is None
        is_selected = (index == self.state.current_index)
        elem_color = GenshinTheme.get_element_color(member.get("element", "Neutral"))

        if is_empty:
            c = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE, color=ft.Colors.WHITE_24, size=28),
                    ft.Text("添加角色", size=11, color=ft.Colors.WHITE_24, weight=ft.FontWeight.W_500)
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                alignment=ft.Alignment.CENTER,
                expand=True,
                bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.WHITE),
                border_radius=12,
                border=ft.Border.all(1, ft.Colors.with_opacity(0.12, ft.Colors.WHITE)),
                on_click=lambda _: self._show_character_picker(index),
                animate=ft.Animation(300, ft.AnimationCurve.DECELERATE),
            )
            c.mouse_cursor = ft.MouseCursor.CLICK
            return c

        # ── 数据准备 ──────────────────────────────────
        talents = member.get('talents', {'na': '1', 'e': '1', 'q': '1'})
        elem_name = member.get('element', 'Neutral')
        weapon = member.get('weapon', {})
        weapon_id = weapon.get('id')
        weapon_text = weapon_id.upper() if weapon_id else "未装备"
        weapon_ref = weapon.get('refinement', '1')
        artifact_sets = self._get_artifact_sets(member)

        # ── 视觉参数 ──────────────────────────────────
        bg_opacity   = 0.28 if is_selected else 0.10
        text_alpha   = 1.0  if is_selected else 0.75
        border_w     = 2    if is_selected else 1
        border_alpha = 0.65 if is_selected else 0.12

        # 元素色渐变底
        bg_gradient = ft.LinearGradient(
            begin=ft.Alignment(-1, -1),
            end=ft.Alignment(1, 1),
            colors=[
                ft.Colors.with_opacity(bg_opacity, elem_color),
                ft.Colors.with_opacity(bg_opacity * 0.3, elem_color),
            ]
        )

        # ── 顶行：小头像 + 名字 + 等级/命座 ──────────────
        avatar = ft.Container(
            content=ft.Text(
                member.get("name", "?")[0],
                size=15, weight=ft.FontWeight.W_900, color=ft.Colors.WHITE
            ),
            width=36, height=36,
            bgcolor=ft.Colors.with_opacity(0.3, elem_color),
            border_radius=18,
            alignment=ft.Alignment.CENTER,
            border=ft.Border.all(1.5, ft.Colors.with_opacity(0.6 if is_selected else 0.25, elem_color))
        )
        name_col = ft.Column([
            ft.Text(
                member.get("name", "未选定"),
                size=13, weight=ft.FontWeight.W_900 if is_selected else ft.FontWeight.BOLD,
                color=ft.Colors.with_opacity(text_alpha, ft.Colors.WHITE),
                no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS,
            ),
            ft.Text(
                f"Lv.{member.get('level', '90')}  C{member.get('constellation', '0')}",
                size=10, color=ft.Colors.with_opacity(0.5, ft.Colors.WHITE),
            ),
        ], spacing=1, expand=True)

        # 移除按钮：嵌入 top_row 末尾，明确尺寸防止覆盖整个槽位
        remove_icon = ft.Container(
            content=ft.Icon(ft.Icons.CLOSE, size=12,
                            color=ft.Colors.with_opacity(0.28, ft.Colors.WHITE)),
            width=22, height=22,
            border_radius=11,
            alignment=ft.Alignment.CENTER,
            on_click=lambda _: self._handle_remove_member(index),
        )
        remove_icon.mouse_cursor = ft.MouseCursor.CLICK

        top_row = ft.Row(
            [avatar, name_col, remove_icon],
            spacing=9,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # ── 天赋行 ─────────────────────────────────────
        talent_row = ft.Row([
            self._build_mini_talent_chip("A", talents['na']),
            self._build_mini_talent_chip("E", talents['e']),
            self._build_mini_talent_chip("Q", talents['q']),
        ], spacing=5)

        # ── 武器行 ─────────────────────────────────────
        weapon_type = member.get('type', '单手剑')
        weapon_icon = GenshinTheme.get_weapon_icon(weapon_type)
        
        weapon_row = ft.Row([
            ft.Icon(weapon_icon, size=11, color=ft.Colors.with_opacity(0.45, ft.Colors.WHITE)),
            ft.Text(
                f"{weapon_text[:10]}  Lv.{weapon.get('level', '90')}  R{weapon_ref}" if weapon_id else weapon_text,
                size=10, color=ft.Colors.with_opacity(0.65, ft.Colors.WHITE),
                no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS, expand=True,
            ),
        ], spacing=5)

        # ── 套装行 ─────────────────────────────────────
        set_label = artifact_sets if artifact_sets else "未配置圣遗物"
        artifact_row = ft.Row([
            ft.Icon(ft.Icons.AUTO_AWESOME, size=11, color=ft.Colors.with_opacity(0.45, ft.Colors.WHITE)),
            ft.Text(
                set_label,
                size=10, color=ft.Colors.with_opacity(0.65, ft.Colors.WHITE),
                no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS, expand=True,
            ),
        ], spacing=5)

        # ── 分隔线 ─────────────────────────────────────
        divider = ft.Container(
            height=1,
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
            margin=ft.margin.symmetric(vertical=2),
        )

        # ── 组装 ──────────────────────────────────────
        body = ft.Container(
            content=ft.Column([
                top_row,
                divider,
                talent_row,
                weapon_row,
                artifact_row,
            ], spacing=5, alignment=ft.MainAxisAlignment.START),
            padding=ft.Padding(11, 11, 11, 10),
            expand=True,
        )

        c = ft.Container(
            content=ft.Stack([
                ft.Container(expand=True, gradient=bg_gradient, border_radius=12),
                body,
            ]),
            expand=True,
            border_radius=12,
            border=ft.Border.all(border_w, ft.Colors.with_opacity(border_alpha, elem_color)),
            shadow=GenshinTheme.get_element_glow(elem_name, 0.55) if is_selected else None,
            on_click=lambda e, i=index: self._handle_member_select(i),
            offset=ft.Offset(0.04, 0) if is_selected else ft.Offset(0, 0),
            animate=ft.Animation(300, ft.AnimationCurve.DECELERATE),
            animate_offset=ft.Animation(300, ft.AnimationCurve.EASE_OUT_BACK),
        )
        c.mouse_cursor = ft.MouseCursor.CLICK
        return c

    @staticmethod
    def _get_artifact_sets(member: dict) -> str:
        """从圣遗物数据推断套装组合，返回简短描述字符串。"""
        artifacts = member.get('artifacts', {})
        counts: dict[str, int] = {}
        for slot_data in artifacts.values():
            name = slot_data.get('name', '').strip()
            if name:
                counts[name] = counts.get(name, 0) + 1

        # 按件数降序排列，只取 2 件及以上的，最多显示两个套装
        sets = sorted([(n, c) for n, c in counts.items() if c >= 2], key=lambda x: -x[1])
        if not sets:
            return ""
        parts = [f"{n[:4]}·{c}件" for n, c in sets[:2]]
        return "  ".join(parts)


    def _build_mini_talent_chip(self, label: str, val):
        """构建天赋标签：黑色半透明底，确保在任何元素色渐变背景上都可读"""
        return ft.Container(
            content=ft.Column([
                ft.Text(label, size=9, weight=ft.FontWeight.W_900, color=ft.Colors.with_opacity(0.55, ft.Colors.WHITE)),
                ft.Text(str(val), size=13, weight=ft.FontWeight.W_900, color=ft.Colors.WHITE),
            ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=ft.Colors.with_opacity(0.35, ft.Colors.BLACK),
            padding=ft.Padding(7, 4, 7, 4),
            border_radius=6,
            border=ft.Border.all(1, ft.Colors.with_opacity(0.15, ft.Colors.WHITE)),
        )

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
        self._refresh_all()

    def _handle_remove_member(self, index: int):
        self.state.remove_member(index)
        self._refresh_all()

    def _refresh_all(self):
        """全量同步刷新逻辑：通常用于增删成员后"""
        # 清除所有缓存，强制重绘
        self.workbench_cache.clear()
        self.slot_controls = [self._build_member_slot(i) for i in range(4)]
        self.sidebar.controls = self.slot_controls
        self._handle_member_select(self.state.current_index)

    def _handle_member_select(self, index: int):
        """同步全局角色选中态与工作台渲染，并精准刷新 UI"""
        # 1. 更新内部状态
        # 如果点击的是已选中的，仅刷新当前项防止 UI 树抖动
        old_index = self.state.current_index
        self.state.select_member(index)
        self.current_element = self.state.current_member.get("element", "Neutral")

        # 2. 局部刷新侧边栏 (不重建，仅更新索引指向)
        # 如果 Slot 结构发生大的变化（比如从 Empty 变成 Character），则需要重构该 Slot
        # 但目前我们先简单地全量更新引用，Flet 会处理 diff
        self.sidebar.controls = [self._build_member_slot(i) for i in range(4)]
        
        # 3. 极速切换中央工作台 (从缓存提取)
        if index not in self.workbench_cache:
            self.workbench_cache[index] = self._build_workbench_controls()
            
        self.workbench_content.controls = self.workbench_cache[index]
        
        # 4. 性能优化：局部 update
        try:
            self.sidebar.update()
            self.workbench_content.update()
        except:
            pass

    def _handle_stat_change(self, key: str, new_val: str):
        # 处理基础属性(等级/命座)变更
        self.state.current_member[key] = new_val
        self._refresh_current_slot()
        # 属性变更后不需要重绘整个 WB, 因为 WB 内部 Slider 已经自更新

    def _handle_talent_change(self, key: str, new_val: str):
        """处理天赋等级变更"""
        self.state.current_member['talents'][key] = new_val
        self._refresh_current_slot()

    def _handle_weapon_change(self, weapon_data: dict):
        # 更新当前成员的武器，触发整体刷新
        self.state.current_member['weapon']['id'] = weapon_data['id']
        self._refresh_all()


    def _handle_weapon_stat_change(self, key: str, val: str):
        """处理武器等级/精炼变更，同步刷新侧边栏"""
        self.state.current_member['weapon'][key] = val
        self._refresh_current_slot()

    def _refresh_current_slot(self):
        """只重建当前选中槽位，比全量刷新更轻量"""
        idx = self.state.current_index
        self.sidebar.controls[idx] = self._build_member_slot(idx)
        try:
            self.sidebar.update()
        except: pass

    def _show_weapon_picker(self):
        """弹出武器库选择器"""
        weapon_type = self.state.current_member.get('type', '单手剑')
        # 改为使用预先加载好的缓存
        repo_weapons = self.app_state.weapon_map.get(weapon_type, [])
        
        mock_weapons = []
        seen_names = set() # 增加前端去重，防止数据库脏数据导致 UI 崩溃
        for w_dict in repo_weapons:
            name = w_dict["name"]
            if name in seen_names:
                continue
            seen_names.add(name)
            
            mock_weapons.append({
                "id": name, # 武器 id 即其名称
                "name": name,
                "rarity": w_dict["rarity"],
                "type": weapon_type, # 补全武器类型，用于 AssetGrid 过滤
                "element": self.state.current_member.get('element', '物理'), # 用于显示武器图标的主题色
                "is_implemented": name in self.app_state.implemented_weapons
            })

        def on_weapon_select(wid):
            selected_w = next(w for w in mock_weapons if w['id'] == wid)
            self._handle_weapon_change(selected_w)
            self.page.pop_dialog()

        picker_grid = AssetGrid(
            mock_weapons, 
            on_select=on_weapon_select, 
            allow_filter_type=False, 
            allow_filter_element=False
        )
        
        dialog = ft.AlertDialog(
            title=ft.Text("选择武器装备", size=18, weight=ft.FontWeight.BOLD),
            content=ft.Container(picker_grid, width=500, height=400),
            bgcolor=GenshinTheme.SURFACE,
        )
        self.page.show_dialog(dialog)

    # --- 模板操作触发点 (通过 PersistenceManager) ---
    async def _handle_config_load_click(self, e):
        if await self.page.persistence.load_config():
            self._refresh_all()

    async def _handle_config_save_click(self, e):
        await self.page.persistence.save_config()

    async def _handle_char_save_click(self, e):
        await self.page.persistence.save_character_template(self.state.current_index)

    async def _handle_char_load_click(self, e):
        if await self.page.persistence.load_character_template(self.state.current_index):
            self._refresh_all()

    async def _handle_arti_save_click(self, e):
        await self.page.persistence.save_artifact_set(self.state.current_index)

    async def _handle_arti_load_click(self, e):
        if await self.page.persistence.load_artifact_set(self.state.current_index):
            self._refresh_all()

    def _show_toast(self, text: str):
        if self.page:
            self.page.snack_bar = ft.SnackBar(ft.Text(text))
            self.page.snack_bar.open = True
            self.page.update()

    def _refresh_all(self):
        """完全同步的状态刷新"""
        self.workbench_content.controls = self._build_workbench_controls()
        self.slot_controls = [self._build_member_slot(i) for i in range(4)]
        self.sidebar.controls = self.slot_controls
        self.update()
