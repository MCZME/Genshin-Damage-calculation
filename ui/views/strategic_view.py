import flet as ft
from ui.state import AppState
from ui.components.universe_canvas import UniverseCanvas
from ui.components.character_picker import CharacterPicker
from ui.components.mutation_inspector import MutationInspector
from ui.components.property_editor import PropertyEditor


class StrategicView(ft.Container):
    """
    策略筹备阶段视图。
    """

    def __init__(self, state: AppState):
        super().__init__(expand=True)
        self.state = state
        self.canvas = None
        self.team_list = ft.ListView(expand=True, spacing=10)
        self.target_list = ft.ListView(expand=True, spacing=10)  # <-- 新增目标列表
        self.inspector = MutationInspector(self.state)
        self.editor = PropertyEditor(self.state)
        self._build_ui()

    def _build_ui(self):
        # 1. 左侧列表
        self.left_sidebar = ft.Container(
            width=280,
            bgcolor="#111111",
            padding=20,
            content=ft.Column(
                [
                    ft.Text("TEAM", size=10, weight="bold", opacity=0.4),
                    ft.Container(content=self.team_list, height=350),  # 限制高度
                    ft.ElevatedButton(
                        "添加角色",
                        icon=ft.Icons.ADD,
                        on_click=self._open_picker,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                        width=240,
                    ),
                    ft.Container(
                        content=ft.Text("TARGETS", size=10, weight="bold", opacity=0.4),
                        padding=ft.Padding(0, 20, 0, 0),
                    ),
                    self.target_list,  # <-- 挂载目标列表
                ]
            ),
        )
        self._render_team()
        self._render_targets()

        # 2. 中间内容区 (适配 Flet 0.80+ Tabs 架构)
        def on_node_select(node):
            self.state.selected_node = node
            self.inspector.refresh()
            self.state.refresh()

        self.canvas = UniverseCanvas(
            self.state.universe_root, on_node_select=on_node_select
        )

        self.tab_views = ft.TabBarView(
            [
                self.editor,  # <-- 挂载属性编辑器
                ft.Container(content=self.canvas.container, expand=True),
            ]
        )

        self.tab_bar = ft.TabBar(
            tabs=[
                ft.Tab(label="属性配置", icon=ft.Icons.SETTINGS_OUTLINED),
                ft.Tab(label="分支宇宙", icon=ft.Icons.ACCOUNT_TREE_OUTLINED),
            ]
        )

        self.tabs_control = ft.Tabs(
            length=2,
            selected_index=1,
            content=ft.Column(
                [self.tab_bar, ft.Container(content=self.tab_views, expand=True)],
                expand=True,
            ),
            expand=True,
        )

        self.middle_content = ft.Container(
            content=self.tabs_control, expand=True, padding=20
        )

        # 3. 右侧检视区
        self.right_sidebar = ft.Container(
            width=350, bgcolor="#111111", padding=20, content=self.inspector
        )

        # 组装整体视图
        self.content = ft.Row(
            [
                self.left_sidebar,
                ft.VerticalDivider(width=1, color="#222222"),
                self.middle_content,
                ft.VerticalDivider(width=1, color="#222222"),
                self.right_sidebar,
            ],
            expand=True,
            spacing=0,
        )

    def _render_team(self):
        self.team_list.controls.clear()
        for char in self.state.team:
            c = char["character"]
            is_active = self.state.active_subject == char

            self.team_list.controls.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(
                                ft.Icons.PERSON,
                                color=ft.Colors.CYAN_700
                                if not is_active
                                else ft.Colors.ORANGE_ACCENT,
                                size=20,
                            ),
                            ft.Text(
                                c["name"],
                                weight="bold",
                                size=13,
                                color=ft.Colors.WHITE
                                if not is_active
                                else ft.Colors.ORANGE_ACCENT,
                            ),
                            ft.IconButton(
                                ft.Icons.CLOSE,
                                icon_size=14,
                                on_click=lambda _, ch=char: self._remove_character(ch),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    padding=10,
                    bgcolor="#1a1a1a" if not is_active else "#252525",
                    border_radius=8,
                    on_click=lambda _, ch=char: self._select_subject(ch),
                )
            )
        try:
            self.team_list.update()
        except:
            pass

    def _render_targets(self):
        self.target_list.controls.clear()
        for target in self.state.targets:
            is_active = self.state.active_subject == target
            self.target_list.controls.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(
                                ft.Icons.G_TRANSLATE,
                                color=ft.Colors.RED_700
                                if not is_active
                                else ft.Colors.ORANGE_ACCENT,
                                size=20,
                            ),
                            ft.Text(
                                target["name"],
                                weight="bold",
                                size=13,
                                color=ft.Colors.WHITE
                                if not is_active
                                else ft.Colors.ORANGE_ACCENT,
                            ),
                        ]
                    ),
                    padding=10,
                    bgcolor="#1a1a1a" if not is_active else "#252525",
                    border_radius=8,
                    on_click=lambda _, t=target: self._select_subject(t),
                )
            )
        try:
            self.target_list.update()
        except:
            pass

    def _select_subject(self, subject):
        self.state.active_subject = subject
        self._render_team()
        self._render_targets()
        self.editor.refresh()
        self.tabs_control.selected_index = 0
        self.page.update()

    def _open_picker(self, e):
        def on_select(name):
            self._add_character(name)

        picker = CharacterPicker(self.state, on_select=on_select)
        self.page.show_dialog(picker)

    def _add_character(self, name):
        new_char = self.state._create_placeholder_char()
        new_char["character"]["name"] = name
        info = self.state.char_map.get(name, {})
        new_char["character"]["element"] = info.get("element", "物理")
        self.state.team.append(new_char)
        self._render_team()
        self._select_subject(new_char)  # 添加后自动选中

    def _remove_character(self, char):
        self.state.team.remove(char)
        if self.state.active_subject == char:
            self.state.active_subject = None
            self.editor.refresh()
        self._render_team()

    def update_canvas(self):
        if self.canvas:
            self.canvas.update_root(self.state.universe_root)
