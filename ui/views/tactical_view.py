import flet as ft
from ui.theme import GenshinTheme


class TacticalView(ft.Row):
    """
    战术编排视图：动作序列编辑器
    """

    def __init__(self, state):
        super().__init__(expand=True, spacing=0)
        self.state = state
        self.selected_index = None
        self._build_ui()

    def _build_ui(self):
        # 1. 序列主面板 (左)
        self.timeline = ft.ReorderableListView(
            expand=True,
            spacing=10,
            padding=ft.padding.all(5),
            on_reorder=self._handle_reorder,
        )

        self.library_container = ft.Row(spacing=10, scroll=ft.ScrollMode.AUTO)

        self.left_col = ft.Column(
            [
                ft.Row(
                    [
                        ft.Text(
                            "指令时间轴 (TIMELINE)",
                            size=12,
                            weight=ft.FontWeight.W_900,
                            opacity=0.5,
                        ),
                        ft.IconButton(
                            ft.Icons.DELETE_SWEEP_OUTLINED,
                            icon_size=18,
                            opacity=0.3,
                            on_click=lambda _: self._clear_sequence(),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                # 动作库入口区
                ft.Container(
                    content=self.library_container,
                    height=70,
                    bgcolor="rgba(255,255,255,0.02)",
                    border_radius=12,
                    padding=10,
                ),
                # 滚动时间轴
                ft.Container(
                    content=self.timeline,
                    expand=True,
                    bgcolor="rgba(0,0,0,0.1)",
                    border_radius=16,
                    padding=10,
                ),
            ],
            expand=3,
            spacing=15,
        )

        # 2. 详情检视器 (右)
        self.inspector_content = ft.Column(spacing=20)
        self.inspector = ft.Container(
            content=self.inspector_content,
            expand=2,
            padding=24,
            bgcolor="rgba(255,255,255,0.01)",
            border_radius=16,
            margin=ft.margin.only(left=16),
            border=ft.border.only(left=ft.BorderSide(1, "rgba(255,255,255,0.05)")),
        )

        self.controls = [self.left_col, self.inspector]

    def did_mount(self):
        self.refresh()

    def refresh(self):
        # 安全检查：防止挂载前访问 .page 导致 RuntimeError
        try:
            if not self.page:
                return
        except:
            return

        self._render_library()
        self._render_timeline()
        self._render_inspector()

        try:
            self.update()
        except:
            pass

    def _render_library(self):
        """渲染动作库 (根据当前队伍)"""
        self.library_container.controls.clear()
        active_members = [m for m in self.state.team if m is not None]

        if not active_members:
            self.library_container.controls.append(
                ft.Text("请先在战略阶段添加角色", size=11, italic=True, opacity=0.3)
            )
            return

        for member in active_members:
            char = member["character"]
            color = GenshinTheme.get_element_color(char["element"])

            # 基础动作：E, Q, A
            for act_label, act_id in [
                ("E", "elemental_skill"),
                ("Q", "elemental_burst"),
                ("A", "normal_attack"),
            ]:
                self.library_container.controls.append(
                    ft.Container(
                        content=ft.Text(act_label, size=11, weight=ft.FontWeight.BOLD),
                        width=40,
                        height=40,
                        bgcolor=ft.Colors.with_opacity(0.1, color),
                        border=ft.border.all(1, ft.Colors.with_opacity(0.3, color)),
                        border_radius=8,
                        alignment=ft.Alignment.CENTER,
                        on_click=lambda _, c=char["name"], a=act_id: self._add_action(
                            c, a
                        ),
                    )
                )

    def _render_timeline(self):
        """渲染时间轴列表"""
        self.timeline.controls.clear()
        for i, action in enumerate(self.state.action_sequence):
            is_selected = self.selected_index == i
            # 简单磁贴展示
            self.timeline.controls.append(
                ft.Container(
                    key=str(i),
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.DRAG_INDICATOR, size=16, opacity=0.2),
                            ft.Text(
                                action["char_name"], size=12, weight=ft.FontWeight.BOLD
                            ),
                            ft.Text(
                                action["action_id"].upper(),
                                size=11,
                                opacity=0.6,
                                expand=True,
                            ),
                            ft.IconButton(
                                ft.Icons.DELETE_OUTLINE,
                                icon_size=16,
                                opacity=0.3,
                                on_click=lambda _, idx=i: self._remove_action(idx),
                            ),
                        ]
                    ),
                    padding=12,
                    bgcolor="rgba(255,255,255,0.05)"
                    if is_selected
                    else "rgba(255,255,255,0.02)",
                    border_radius=10,
                    on_click=lambda _, idx=i: self._select_action(idx),
                )
            )

    def _render_inspector(self):
        """渲染指令编辑器"""
        self.inspector_content.controls.clear()
        if self.selected_index is None or self.selected_index >= len(
            self.state.action_sequence
        ):
            self.inspector_content.controls.append(
                ft.Column(
                    [
                        ft.Icon(ft.Icons.AUTO_FIX_HIGH, size=40, opacity=0.1),
                        ft.Text(
                            "选择一个动作进行编辑", size=12, italic=True, opacity=0.3
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )
            return

        action = self.state.action_sequence[self.selected_index]
        self.inspector_content.controls.extend(
            [
                ft.Text(
                    f"编辑: {action['char_name']}", size=14, weight=ft.FontWeight.BOLD
                ),
                ft.Text(action["action_id"].upper(), size=11, opacity=0.5),
                ft.Divider(height=1, color="rgba(255,255,255,0.05)"),
                # 此处预留参数编辑器
                ft.TextField(label="执行时间偏移 (s)", value="0", dense=True),
                ft.Switch(label="是否命中目标", value=True),
            ]
        )

    def _add_action(self, char_name, action_id):
        self.state.action_sequence.append(
            {"char_name": char_name, "action_id": action_id, "params": {}}
        )
        self.state.refresh()

    def _remove_action(self, index):
        self.state.action_sequence.pop(index)
        self.selected_index = None
        self.state.refresh()

    def _select_action(self, index):
        self.selected_index = index
        self.refresh()

    def _handle_reorder(self, e):
        old_idx = e.old_index
        new_idx = e.new_index
        if old_idx < new_idx:
            new_idx -= 1
        item = self.state.action_sequence.pop(old_idx)
        self.state.action_sequence.insert(new_idx, item)
        self.state.refresh()

    def _clear_sequence(self):
        self.state.action_sequence.clear()
        self.selected_index = None
        self.state.refresh()
