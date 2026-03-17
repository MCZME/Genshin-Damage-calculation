from __future__ import annotations
import flet as ft
from typing import Any, TYPE_CHECKING
from ui.states.strategic_state import StrategicState
from ui.theme import GenshinTheme
from ui.components.strategic.artifact_slot import ArtifactSlot
from ui.components.strategic.property_slider import PropertySlider
from ui.components.common.asset_grid import AssetGrid
from ui.components.strategic.member_slot import MemberSlot
from ui.components.strategic.weapon_card import WeaponCard

if TYPE_CHECKING:
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
        # 使用 cast 解决 Flet use_state 不支持下标泛型导致的类型推断失败问题
        from typing import cast
        picker_type, set_picker_type = ft.use_state(cast(str | None, None))
        picker_index, set_picker_index = ft.use_state(0)
        # [V4.6] 活跃滑块键：同一时刻只有一个滑块可以处于编辑态
        focused_slider, set_focused_slider = ft.use_state(cast(str | None, None))

        # 2. 绑定核心 VM (直接从传入的 state 获取以激活 Flet 响应式)
        proxy = state.active_character_proxy
        team_vms = state.team_vms
        current_index = state.current_index

        # 3. 内部组件工厂
        def create_managed_slider(label: str, value: Any, on_change: Any, key: str = "", **kwargs):
            return PropertySlider(
                label=label,
                value=value,
                element=proxy.element,
                on_change=on_change,
                slider_key=key,
                focused_key=focused_slider or "",
                on_focus=lambda: set_focused_slider(key),
                **kwargs
            )

        # 4. 布局构建
        # 4.1 顶部操作栏
        header = ft.Row(
            controls=[
                ft.Text("战略准备工作台", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ], 
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        # 4.2 左侧编队边栏
        sidebar_controls: list[ft.Control] = [
            MemberSlot(
                vm=team_vms[i],
                index=i, 
                is_selected=(i == current_index),
                on_click=state.select_member,
                on_remove=state.remove_member,
                on_add=lambda idx: [set_picker_index(idx), set_picker_type("character")]
            ) for i in range(4)
        ]
        sidebar = ft.Column(controls=sidebar_controls, width=180, expand=True, spacing=10, alignment=ft.MainAxisAlignment.START)

        # 4.3 中央工作台
        if not proxy.is_active:
            workbench_content = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.PERSON_ADD_ALT_1, size=64, color=ft.Colors.WHITE_24),
                        ft.Text("请在左侧编队中选择或添加一位角色", size=18, weight=ft.FontWeight.W_500, color=ft.Colors.WHITE_54),
                    ], 
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
                    spacing=15
                ),
                alignment=ft.Alignment.CENTER, 
                expand=True
            )
        else:
            # 角色详情区域 (绑定到 Proxy)
            # 安全获取页面与持久化管理器 (避免 Pylance 报错)
            page = self.app_state.page
            persistence = getattr(page, "persistence", None)

            def save_template():
                if page and persistence:
                    page.run_task(persistence.save_character_template, current_index)

            def load_template():
                if page and persistence:
                    page.run_task(persistence.load_character_template, current_index)

            upper_section_left_controls: list[ft.Control] = [
                ft.Row(
                    controls=[
                        ft.Text("角色基础属性", size=16, weight=ft.FontWeight.BOLD, opacity=0.8),
                        ft.Row(
                            controls=[
                                ft.IconButton(ft.Icons.DOWNLOAD, icon_size=16, tooltip="保存为角色模版", 
                                             on_click=lambda _: save_template()),
                                ft.IconButton(ft.Icons.UPLOAD, icon_size=16, tooltip="读取角色模版", 
                                             on_click=lambda _: load_template()),
                            ], 
                            spacing=0
                        )
                    ], 
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),

                ft.Row(
                    controls=[
                        create_managed_slider("等级", proxy.level, proxy.set_level, key="level", discrete_values=[1, 20, 40, 50, 60, 70, 80, 90, 95, 100]),
                        create_managed_slider("命之座", proxy.constellation, proxy.set_constellation, key="constellation", min_val=0, max_val=6, divisions=6)
                    ],
                    spacing=20
                ),
                ft.Divider(height=10, color="transparent"),
                ft.Text("天赋等级配置", size=16, weight=ft.FontWeight.BOLD, opacity=0.8),
                ft.Row(
                    controls=[
                        create_managed_slider("普攻", proxy.talent_na, proxy.set_talent_na, key="talent_na", min_val=1, max_val=10, divisions=9),
                        create_managed_slider("战技", proxy.talent_e, proxy.set_talent_e, key="talent_e", min_val=1, max_val=10, divisions=9),
                        create_managed_slider("爆发", proxy.talent_q, proxy.set_talent_q, key="talent_q", min_val=1, max_val=10, divisions=9),
                    ],
                    spacing=15
                )
            ]

            # 获取武器 VM 并进行非空校验
            weapon_vm = proxy.weapon
            if not weapon_vm:
                # 理论上不应发生，因为 is_active 保证了成员存在
                return ft.Container(content=ft.Text("武器数据异常"))

            from typing import cast
            upper_section_controls = cast(list[ft.Control], [
                ft.Column(controls=upper_section_left_controls, expand=True, spacing=10),
                ft.VerticalDivider(width=1, color=ft.Colors.WHITE_10),
                WeaponCard(
                    vm=weapon_vm,
                    element=proxy.element,
                    on_picker_click=lambda: set_picker_type("weapon")
                )
            ])

            upper_section = ft.Row(
                controls=upper_section_controls, 
                spacing=30, 
                vertical_alignment=ft.CrossAxisAlignment.START
            )

            # 圣遗物矩阵
            set_options = self.library_vm.artifact_set_options
            artifact_slots_list: list[ft.Control] = [
                ArtifactSlot(
                    vm=proxy.artifacts[slot],
                    set_options=set_options,
                    element=proxy.element
                ) for slot in ["Flower", "Plume", "Sands", "Goblet", "Circlet"]
            ]

            def save_artifact():
                if page and persistence:
                    page.run_task(persistence.save_artifact_set, current_index)

            def load_artifact():
                if page and persistence:
                    page.run_task(persistence.load_artifact_set, current_index)

            lower_section = ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text("圣遗物装配中心", size=16, weight=ft.FontWeight.BOLD, opacity=0.8),
                            ft.Row(
                                controls=[
                                    ft.TextButton("保存套装", icon=ft.Icons.SAVE_ALT, on_click=lambda _: save_artifact()),
                                    ft.TextButton("加载套装", icon=ft.Icons.UPLOAD_FILE, on_click=lambda _: load_artifact()),
                                ], 
                                spacing=10
                            ),
                        ], 
                        spacing=20, 
                        alignment=ft.MainAxisAlignment.START, 
                        vertical_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    ft.Row(controls=artifact_slots_list, scroll=ft.ScrollMode.ADAPTIVE, spacing=15)
                ], 
                spacing=15
            )

            workbench_content = ft.Column(
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

        # 5. 遮罩层构建 (使用 LibraryVM 驱动)
        overlay_content = None
        if picker_type == "character":
            def finish_char_select(char_id: str):
                selected_opt = next(c for c in self.library_vm.character_options if c.id == char_id)
                state.add_member(picker_index, {
                    "id": selected_opt.id, "name": selected_opt.name, 
                    "element": selected_opt.element, "type": selected_opt.type, 
                    "rarity": selected_opt.rarity
                })
                set_picker_type(None)

            overlay_content = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text("选择角色", size=18, weight=ft.FontWeight.W_800, color=GenshinTheme.PRIMARY),
                                ft.IconButton(ft.Icons.CLOSE, on_click=lambda _: set_picker_type(None))
                            ], 
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        AssetGrid(self.library_vm.character_options, on_select=finish_char_select)
                    ], 
                    spacing=15
                ),
                width=650, height=550, bgcolor=GenshinTheme.SURFACE, border_radius=16, padding=20
            )

        elif picker_type == "weapon":
            target_vm = proxy.target
            weapon_vm = proxy.weapon
            
            if target_vm and weapon_vm and target_vm.model:
                char_weapon_type = target_vm.model.raw_data.get("type", "单手剑")
                weapon_options = self.library_vm.get_weapon_options(char_weapon_type)

                def finish_weapon_select(wid: str):
                    if weapon_vm:
                        weapon_vm.set_weapon_id(wid)
                    set_picker_type(None)

                overlay_content = ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text("选择武器", size=18, weight=ft.FontWeight.W_800, color=GenshinTheme.PRIMARY),
                                    ft.IconButton(ft.Icons.CLOSE, on_click=lambda _: set_picker_type(None))
                                ], 
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                            ),
                            AssetGrid(weapon_options, on_select=finish_weapon_select, allow_filter_type=False, allow_filter_element=False)
                        ], 
                        spacing=15
                    ),
                    width=650, height=550, bgcolor=GenshinTheme.SURFACE, border_radius=16, padding=20
                )
            else:
                overlay_content = None

        # 6. 最终布局
        return ft.Container(
            content=ft.Stack(
                controls=[
                    # 背景层：点击清除焦点
                    ft.GestureDetector(
                        content=ft.Container(expand=True, bgcolor="transparent"),
                        on_tap=lambda _: proxy.notify()
                    ),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                header,
                                ft.Row(
                                    controls=[
                                        ft.Container(content=sidebar, width=180),
                                        ft.VerticalDivider(width=1, color=ft.Colors.with_opacity(0.1, GenshinTheme.ON_SURFACE)),
                                        ft.Container(content=workbench_content, expand=True)
                                    ], 
                                    expand=True
                                )
                            ], 
                            spacing=10
                        ),
                        padding=15, 
                        expand=True
                    ),
                    ft.Container(
                        content=ft.Stack(
                            controls=[
                                ft.Container(bgcolor="rgba(0,0,0,0.8)", on_click=lambda _: set_picker_type(None)),
                                ft.Container(content=overlay_content, alignment=ft.Alignment.CENTER),
                            ]
                        ),
                        visible=overlay_content is not None, 
                        expand=True
                    )
                ]
            ),
            expand=True, 
            bgcolor=GenshinTheme.BACKGROUND
        )
