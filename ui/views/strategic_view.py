import flet as ft
from ui.states.strategic_state import StrategicState
from ui.theme import GenshinTheme
from ui.components.strategic.artifact_slot import ArtifactSlot
from ui.components.strategic.property_slider import PropertySlider
from ui.components.common.asset_grid import AssetGrid
from ui.components.strategic.member_slot import MemberSlot
from ui.components.strategic.weapon_card import WeaponCard
from ui.states.app_state import AppState

class StrategicView:
    """
    战略准备工作台 (MVVM V5.0)
    已完全解耦字典操作，通过 ViewModel 和 ActiveProxy 实现高性能响应。
    """
    def __init__(self, state: AppState):
        self.app_state = state
        self.library_vm = state.library_vm

    @ft.component
    def build(self, state: StrategicState):
        # 1. 局部 UI 状态管理 (仅用于遮罩层控制)
        picker_type, set_picker_type = ft.use_state(None)
        picker_index, set_picker_index = ft.use_state(0)

        # 2. 绑定核心 VM (直接从传入的 state 获取以激活 Flet 响应式)
        proxy = state.active_character_proxy
        team_vms = state.team_vms
        current_index = state.current_index

        # 3. 内部组件工厂
        def create_managed_slider(label, value, on_change, **kwargs):
            return PropertySlider(
                label=label, value=value, 
                element=proxy.element,
                on_change=on_change,
                **kwargs
            )

        # 4. 布局构建
        # 4.1 顶部操作栏
        header = ft.Row([
            ft.Text("战略准备工作台", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        # 4.2 左侧编队边栏
        sidebar = ft.Column([
            MemberSlot(
                vm=team_vms[i],
                index=i, 
                is_selected=(i == current_index),
                on_click=state.select_member,
                on_remove=state.remove_member,
                on_add=lambda idx: [set_picker_index(idx), set_picker_type("character")]
            ) for i in range(4)
        ], width=180, expand=True, spacing=10, alignment=ft.MainAxisAlignment.START)

        # 4.3 中央工作台
        if not proxy.is_active:
            workbench_content = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.PERSON_ADD_ALT_1, size=64, color=ft.Colors.WHITE_24),
                    ft.Text("请在左侧编队中选择或添加一位角色", size=18, weight=ft.FontWeight.W_500, color=ft.Colors.WHITE_54),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
                alignment=ft.Alignment.CENTER, expand=True
            )
        else:
            # 角色详情区域 (绑定到 Proxy)
            upper_section = ft.Row([
                ft.Column([
                    ft.Row([
                        ft.Text("角色基础属性", size=16, weight=ft.FontWeight.BOLD, opacity=0.8),
                        ft.Row([
                            ft.IconButton(ft.Icons.DOWNLOAD, icon_size=16, tooltip="保存为角色模版", 
                                         on_click=lambda _: self.app_state.page.run_task(self.app_state.page.persistence.save_character_template, current_index)),
                            ft.IconButton(ft.Icons.UPLOAD, icon_size=16, tooltip="读取角色模版", 
                                         on_click=lambda _: self.app_state.page.run_task(self.app_state.page.persistence.load_character_template, current_index)),
                        ], spacing=0)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

                    ft.Row([
                        create_managed_slider("等级", proxy.level, proxy.set_level, discrete_values=[1, 20, 40, 50, 60, 70, 80, 90, 95, 100]),
                        create_managed_slider("命之座", proxy.constellation, proxy.set_constellation, min_val=0, max_val=6, divisions=6)
                    ], spacing=20),
                    ft.Divider(height=10, color="transparent"),
                    ft.Text("天赋等级配置", size=16, weight=ft.FontWeight.BOLD, opacity=0.8),
                    ft.Row([
                        create_managed_slider("普攻", proxy.talent_na, proxy.set_talent_na, min_val=1, max_val=10, divisions=9),
                        create_managed_slider("战技", proxy.talent_e, proxy.set_talent_e, min_val=1, max_val=10, divisions=9),
                        create_managed_slider("爆发", proxy.talent_q, proxy.set_talent_q, min_val=1, max_val=10, divisions=9),
                    ], spacing=15)
                ], expand=True, spacing=10),
                
                ft.VerticalDivider(width=1, color=ft.Colors.WHITE_10),
                
                WeaponCard(
                    vm=proxy.weapon,
                    element=proxy.element,
                    on_picker_click=lambda: set_picker_type("weapon")
                )
            ], spacing=30, vertical_alignment=ft.CrossAxisAlignment.START)

            # 圣遗物矩阵
            set_options = self.library_vm.artifact_set_options
            artifact_slots_list = [
                ArtifactSlot(
                    vm=proxy.artifacts[slot],
                    set_options=set_options,
                    element=proxy.element
                ) for slot in ["Flower", "Plume", "Sands", "Goblet", "Circlet"]
            ]

            lower_section = ft.Column([
                ft.Row([
                    ft.Text("圣遗物装配中心", size=16, weight=ft.FontWeight.BOLD, opacity=0.8),
                    ft.Row([
                        ft.TextButton("保存套装", icon=ft.Icons.SAVE_ALT, on_click=lambda _: self.app_state.page.run_task(self.app_state.page.persistence.save_artifact_set, current_index)),
                        ft.TextButton("加载套装", icon=ft.Icons.UPLOAD_FILE, on_click=lambda _: self.app_state.page.run_task(self.app_state.page.persistence.load_artifact_set, current_index)),
                    ], spacing=10),
                ], spacing=20, alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Row(artifact_slots_list, scroll=ft.ScrollMode.ADAPTIVE, spacing=15)
            ], spacing=15)

            workbench_content = ft.Column([
                upper_section, ft.Divider(height=1, color=ft.Colors.WHITE_10), lower_section,
                ft.Container(height=20) 
            ], expand=True, scroll=ft.ScrollMode.ADAPTIVE, spacing=30)

        # 5. 遮罩层构建 (使用 LibraryVM 驱动)
        overlay_content = None
        if picker_type == "character":
            def finish_char_select(char_id):
                selected_opt = next(c for c in self.library_vm.character_options if c.id == char_id)
                # 核心修复：使用 build 方法传入的 state 局部变量
                state.add_member(picker_index, {
                    "id": selected_opt.id, "name": selected_opt.name, 
                    "element": selected_opt.element, "type": selected_opt.type, 
                    "rarity": selected_opt.rarity
                })
                set_picker_type(None)

            overlay_content = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("选择角色", size=18, weight=ft.FontWeight.W_800, color=GenshinTheme.PRIMARY),
                        ft.IconButton(ft.Icons.CLOSE, on_click=lambda _: set_picker_type(None))
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    AssetGrid(self.library_vm.character_options, on_select=finish_char_select)
                ], spacing=15),
                width=650, height=550, bgcolor=GenshinTheme.SURFACE, border_radius=16, padding=20
            )

        elif picker_type == "weapon":
            # 暂时从 proxy 拿数据源，保持一致性
            char_weapon_type = proxy.target.model.raw_data.get("type", "单手剑") 
            weapon_options = self.library_vm.get_weapon_options(char_weapon_type)

            def finish_weapon_select(wid):
                proxy.weapon.set_weapon_id(wid)
                set_picker_type(None)

            overlay_content = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("选择武器", size=18, weight=ft.FontWeight.W_800, color=GenshinTheme.PRIMARY),
                        ft.IconButton(ft.Icons.CLOSE, on_click=lambda _: set_picker_type(None))
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    AssetGrid(weapon_options, on_select=finish_weapon_select, allow_filter_type=False, allow_filter_element=False)
                ], spacing=15),
                width=650, height=550, bgcolor=GenshinTheme.SURFACE, border_radius=16, padding=20
            )

        # 6. 最终布局
        return ft.Container(
            content=ft.Stack([
                # 背景层：点击清除焦点
                ft.GestureDetector(
                    content=ft.Container(expand=True, bgcolor="transparent"),
                    on_tap=lambda _: proxy.notify() # 触发一次重绘来收起所有 slider
                ),
                ft.Container(
                    content=ft.Column([
                        header,
                        ft.Row([
                            ft.Container(content=sidebar, width=180),
                            ft.VerticalDivider(width=1, color=ft.Colors.with_opacity(0.1, GenshinTheme.ON_SURFACE)),
                            ft.Container(content=workbench_content, expand=True)
                        ], expand=True)
                    ], spacing=10),
                    padding=15, expand=True
                ),
                ft.Container(
                    content=ft.Stack([
                        ft.Container(bgcolor="rgba(0,0,0,0.8)", on_click=lambda _: set_picker_type(None)),
                        ft.Container(content=overlay_content, alignment=ft.Alignment.CENTER),
                    ]),
                    visible=overlay_content is not None, expand=True
                )
            ]),
            expand=True, bgcolor=GenshinTheme.BACKGROUND
        )
