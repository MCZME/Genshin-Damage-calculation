import flet as ft
import json
import os
from ui.theme import GenshinTheme
from ui.components.artifact_editor import ArtifactEditor
from core.registry import CharacterClassMap, WeaponClassMap


class PropertyEditor(ft.Container):
    def __init__(self, state):
        super().__init__(expand=True)
        self.state = state
        self.content_area = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=24)
        self.content = self.content_area
        self.artifact_editor = ArtifactEditor(state)
        self.filter_element = "全部"
        self.filter_weapon = "全部"

    def did_mount(self):
        self.refresh()

    def refresh(self):
        self.content_area.controls.clear()
        selection = self.state.selection
        if not selection:
            self._render_team_overview()
        elif selection["type"] == "empty":
            self._render_character_picker()
        elif selection["type"] == "character":
            self._render_character_editor(selection["data"])
        elif selection["type"] == "target":
            self._render_target_editor(selection["data"])
        elif selection["type"] == "env":
            self._render_environment_editor(selection["data"])
        if self.page:
            try:
                self.update()
            except:
                pass

    def _render_team_overview(self):
        self.content_area.controls.append(
            ft.Text(
                "队伍配置总览 (TEAM CONFIGURATION)",
                size=14,
                weight=ft.FontWeight.W_900,
                opacity=0.5,
            )
        )
        active_members = [m for m in self.state.team if m is not None]
        if not active_members:
            self.content_area.controls.append(
                ft.Container(
                    content=ft.Text("暂无队员", italic=True, opacity=0.3),
                    alignment=ft.Alignment.CENTER,
                    padding=40,
                )
            )
            return
        grid = ft.GridView(runs_count=2, max_extent=450, spacing=16, run_spacing=16)
        for i, member in enumerate(self.state.team):
            if member is None:
                continue
            grid.controls.append(self._build_overview_card(i, member))
        self.content_area.controls.append(grid)

    def _build_overview_card(self, index, member):
        char = member["character"]
        weapon = member["weapon"]
        color = GenshinTheme.get_element_color(char["element"])
        set_counts = {}
        for slot in member["artifacts"].values():
            s_name = slot.get("set", "未装备")
            if s_name != "未装备":
                set_counts[s_name] = set_counts.get(s_name, 0) + 1
        set_summary = [
            f"4-{n}" if c >= 4 else f"2-{n}" for n, c in set_counts.items() if c >= 2
        ]
        total_stats = {}
        for slot_data in member["artifacts"].values():
            m_key, m_val = slot_data["main"], slot_data["value"]
            if m_key != "未定义":
                total_stats[m_key] = total_stats.get(m_key, 0.0) + m_val
            for sub in slot_data.get("subs", []):
                s_key, s_val = sub["key"], sub["value"]
                if s_key != "无":
                    total_stats[s_key] = total_stats.get(s_key, 0.0) + s_val
        stats_chips = []
        for key, val in total_stats.items():
            is_pct = key.endswith("%") or "伤害加成" in key or "暴击" in key
            stats_chips.append(
                ft.Container(
                    content=ft.Text(
                        f"{key}+{val:.1f}%" if is_pct else f"{key}+{int(val)}",
                        size=9,
                        weight=ft.FontWeight.BOLD,
                    ),
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    bgcolor="rgba(255,255,255,0.05)",
                    border_radius=6,
                )
            )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(
                                char["name"],
                                size=18,
                                weight=ft.FontWeight.W_900,
                                color=color,
                            ),
                            ft.Row(
                                [
                                    ft.Text(
                                        f"Lv.{char['level']}",
                                        size=11,
                                        weight=ft.FontWeight.BOLD,
                                        opacity=0.6,
                                    ),
                                    ft.VerticalDivider(
                                        width=1, color="rgba(255,255,255,0.1)"
                                    ),
                                    ft.Text(
                                        f"T {'/'.join(map(str, char['talents']))}",
                                        size=11,
                                        weight=ft.FontWeight.BOLD,
                                        opacity=0.6,
                                    ),
                                    ft.VerticalDivider(
                                        width=1, color="rgba(255,255,255,0.1)"
                                    ),
                                    ft.Text(
                                        f"C{char['constellation']}",
                                        size=11,
                                        weight=ft.FontWeight.W_900,
                                        color=color,
                                    ),
                                ],
                                spacing=10,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Divider(height=1, color="rgba(255,255,255,0.05)"),
                    ft.Row(
                        [
                            ft.Icon(
                                ft.Icons.SHIELD, size=14, color=ft.Colors.YELLOW_700
                            ),
                            ft.Text(
                                f"{weapon['name']} (Lv.{weapon['level']} 精炼{weapon['refinement']})",
                                size=12,
                                weight=ft.FontWeight.W_600,
                            ),
                        ],
                        spacing=8,
                    ),
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.LAYERS, size=14, color=color, opacity=0.7),
                            ft.Text(
                                ", ".join(set_summary) if set_summary else "无活跃套装",
                                size=11,
                                italic=True,
                                color=GenshinTheme.TEXT_SECONDARY,
                            ),
                        ],
                        spacing=8,
                    ),
                    ft.Row(controls=stats_chips, spacing=6, run_spacing=6, wrap=True),
                ],
                spacing=10,
            ),
            padding=20,
            bgcolor="rgba(255, 255, 255, 0.02)",
            border=ft.border.all(1, ft.Colors.with_opacity(0.1, color)),
            border_radius=20,
            on_click=lambda _, idx=index: self.state.select_character(idx),
        )

    # --- 2. 选人视图 (优化布局：导入按钮移至标题行) ---
    def _render_character_picker(self):
        header = ft.Row(
            [
                ft.Column(
                    [
                        ft.Text(
                            "角色仓库",
                            size=24,
                            weight=ft.FontWeight.W_900,
                            color=GenshinTheme.ON_SURFACE,
                        ),
                        ft.Text(
                            "SELECT CHARACTER",
                            size=10,
                            weight=ft.FontWeight.BOLD,
                            color=GenshinTheme.PRIMARY,
                            opacity=0.8,
                        ),
                    ],
                    spacing=0,
                    expand=True,
                ),
                ft.TextButton(
                    "导入预设",
                    icon=ft.Icons.CLOUD_DOWNLOAD,
                    on_click=self._handle_import_char,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        self.content_area.controls.append(
            ft.Container(
                content=header,
                padding=ft.padding.only(bottom=10),
                border=ft.border.only(
                    bottom=ft.BorderSide(1, "rgba(255,255,255,0.05)")
                ),
            )
        )

        elements = ["全部", "火", "水", "风", "雷", "草", "冰", "岩"]
        weapons = ["全部", "单手剑", "双手剑", "法器", "长柄武器", "弓"]
        filter_bar = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            self._build_filter_chip(
                                e,
                                self.filter_element,
                                lambda val: self._update_filter("element", val),
                            )
                            for e in elements
                        ],
                        spacing=8,
                        scroll=ft.ScrollMode.AUTO,
                    ),
                    ft.Row(
                        [
                            self._build_filter_chip(
                                w,
                                self.filter_weapon,
                                lambda val: self._update_filter("weapon", val),
                            )
                            for w in weapons
                        ],
                        spacing=8,
                        scroll=ft.ScrollMode.AUTO,
                    ),
                ],
                spacing=10,
            ),
            padding=ft.padding.only(bottom=10),
        )
        self.content_area.controls.append(filter_bar)

        grid = ft.GridView(
            runs_count=5,
            max_extent=110,
            child_aspect_ratio=0.72,
            spacing=12,
            run_spacing=12,
        )
        implemented_chars = list(CharacterClassMap.keys())
        for name, info in self.state.char_map.items():
            if not (
                self.filter_element == "全部" or info["element"] == self.filter_element
            ):
                continue
            if not (self.filter_weapon == "全部" or info["type"] == self.filter_weapon):
                continue
            is_implemented = name in implemented_chars
            color = (
                GenshinTheme.get_element_color(info["element"])
                if is_implemented
                else ft.Colors.GREY_700
            )
            grid.controls.append(
                self._build_char_card(name, info["element"], color, is_implemented)
            )
        self.content_area.controls.append(ft.Container(content=grid, height=500))

    def _handle_import_char(self, _):
        templates = self.state.list_templates("characters")
        lv = ft.ListView(expand=True, spacing=5, height=300)

        def confirm(fname):
            path = os.path.join("data/templates/characters", fname)
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            idx = self.state.selection["index"]
            self.state.team[idx] = data
            self.page.pop_dialog()
            self.state.select_character(idx)

        for t in templates:
            lv.controls.append(
                ft.ListTile(title=ft.Text(t), on_click=lambda _, n=t: confirm(n))
            )
        self.page.show_dialog(
            ft.AlertDialog(
                title=ft.Text("导入角色预设"), content=ft.Container(lv, width=300)
            )
        )

    def _render_character_editor(self, member):
        char = member["character"]
        weapon = member["weapon"]
        color = GenshinTheme.get_element_color(char["element"])
        hero_header = ft.Row(
            [
                ft.IconButton(
                    ft.Icons.ARROW_BACK_IOS_NEW,
                    icon_size=16,
                    icon_color=color,
                    on_click=lambda _: self.state.select_overview(),
                ),
                ft.Column(
                    [
                        ft.Text(
                            char["name"],
                            size=24,
                            weight=ft.FontWeight.W_900,
                            color=GenshinTheme.ON_SURFACE,
                        ),
                        ft.Text(
                            f"{char['element']} · {char['type']}",
                            size=10,
                            weight=ft.FontWeight.BOLD,
                            color=color,
                            opacity=0.8,
                        ),
                    ],
                    spacing=0,
                    expand=True,
                ),
                ft.ElevatedButton(
                    "保存模板",
                    icon=ft.Icons.SAVE,
                    bgcolor=color,
                    color=ft.Colors.WHITE,
                    on_click=lambda _: self._handle_export_char(member),
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self.content_area.controls.append(
            ft.Container(
                content=hero_header,
                padding=ft.padding.only(bottom=10),
                border=ft.border.only(
                    bottom=ft.BorderSide(1, "rgba(255,255,255,0.05)")
                ),
            )
        )
        main_config = ft.Row(
            [
                ft.Column(
                    [
                        self._build_section(
                            "核心状态",
                            [
                                ft.Row(
                                    [
                                        self._build_field(
                                            "等级",
                                            char["level"],
                                            lambda v: self._update_val(
                                                char, "level", v
                                            ),
                                        ),
                                        self._build_field(
                                            "命座",
                                            char["constellation"],
                                            lambda v: self._update_val(
                                                char, "constellation", v
                                            ),
                                        ),
                                    ]
                                ),
                                ft.Row(
                                    [
                                        self._build_field(
                                            "普攻",
                                            char["talents"][0],
                                            lambda v: self._update_talent(char, 0, v),
                                        ),
                                        self._build_field(
                                            "战技",
                                            char["talents"][1],
                                            lambda v: self._update_talent(char, 1, v),
                                        ),
                                        self._build_field(
                                            "爆发",
                                            char["talents"][2],
                                            lambda v: self._update_talent(char, 2, v),
                                        ),
                                    ]
                                ),
                            ],
                            color,
                        ),
                        self._build_section(
                            "战场空间",
                            [
                                ft.Row(
                                    [
                                        self._build_field(
                                            "X 坐标",
                                            member["position"]["x"],
                                            lambda v: self._update_val(
                                                member["position"],
                                                "x",
                                                v,
                                                is_float=True,
                                            ),
                                        ),
                                        self._build_field(
                                            "Z 坐标",
                                            member["position"]["z"],
                                            lambda v: self._update_val(
                                                member["position"],
                                                "z",
                                                v,
                                                is_float=True,
                                            ),
                                        ),
                                    ]
                                )
                            ],
                            color,
                        ),
                    ],
                    expand=1,
                    spacing=20,
                ),
                ft.Column(
                    [
                        self._build_section(
                            "武器装备",
                            [
                                ft.Container(
                                    content=ft.Row(
                                        [
                                            ft.Icon(
                                                ft.Icons.SHIELD,
                                                size=16,
                                                color=ft.Colors.YELLOW_700,
                                            ),
                                            ft.Text(
                                                weapon["name"],
                                                size=13,
                                                weight=ft.FontWeight.BOLD,
                                                expand=True,
                                            ),
                                            ft.Icon(
                                                ft.Icons.EDIT, size=14, opacity=0.5
                                            ),
                                        ],
                                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                    ),
                                    padding=12,
                                    bgcolor="rgba(255,255,255,0.03)",
                                    border_radius=8,
                                    on_click=lambda _: self._show_weapon_picker(
                                        char["type"], weapon
                                    ),
                                ),
                                ft.Row(
                                    [
                                        self._build_field(
                                            "等级",
                                            weapon["level"],
                                            lambda v: self._update_val(
                                                weapon, "level", v
                                            ),
                                        ),
                                        self._build_field(
                                            "精炼",
                                            weapon["refinement"],
                                            lambda v: self._update_val(
                                                weapon, "refinement", v
                                            ),
                                        ),
                                    ]
                                ),
                            ],
                            color,
                        )
                    ],
                    expand=1,
                    spacing=20,
                ),
            ],
            spacing=20,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
        self.content_area.controls.append(main_config)
        self.artifact_editor.set_character(member)
        self.content_area.controls.append(self.artifact_editor)

    def _handle_export_char(self, member):
        name_input = ft.TextField(
            label="角色预设名称",
            value=f"{member['character']['name']}_高配",
            dense=True,
        )

        def confirm(_):
            if name_input.value:
                self.state.save_character_template(member, name_input.value)
                self.page.pop_dialog()

        self.page.show_dialog(
            ft.AlertDialog(
                title=ft.Text("保存角色为模板"),
                content=name_input,
                actions=[ft.ElevatedButton("保存", on_click=confirm)],
            )
        )

    def _render_target_editor(self, target):
        color = ft.Colors.RED_ACCENT
        self._add_hero_header(
            target["name"], f"TARGET ID: {target['id']}", color, can_back=True
        )
        self.content_area.controls.append(
            ft.Row(
                [
                    self._build_section(
                        "基础与坐标",
                        [
                            ft.Row(
                                [
                                    self._build_field(
                                        "等级",
                                        target["level"],
                                        lambda v: self._update_val(target, "level", v),
                                    ),
                                    self._build_field(
                                        "X 坐标",
                                        target["position"]["x"],
                                        lambda v: self._update_val(
                                            target["position"], "x", v, is_float=True
                                        ),
                                    ),
                                    self._build_field(
                                        "Z 坐标",
                                        target["position"]["z"],
                                        lambda v: self._update_val(
                                            target["position"], "z", v, is_float=True
                                        ),
                                    ),
                                ]
                            )
                        ],
                        color,
                        expand=True,
                    )
                ]
            )
        )
        resists = target["resists"]
        res_grid = ft.Column(
            [
                ft.Row(
                    [
                        self._build_field(
                            e, v, lambda val, k=e: self._update_val(resists, k, val)
                        )
                        for e, v in list(resists.items())[:4]
                    ],
                    spacing=10,
                ),
                ft.Row(
                    [
                        self._build_field(
                            e, v, lambda val, k=e: self._update_val(resists, k, val)
                        )
                        for e, v in list(resists.items())[4:]
                    ],
                    spacing=10,
                ),
            ],
            spacing=10,
        )
        self.content_area.controls.append(
            self._build_section("抗性配置 (%)", [res_grid], color)
        )

    def _render_environment_editor(self, env):
        color = ft.Colors.CYAN_200
        self._add_hero_header("环境因素", "WORLD SETTINGS", color, can_back=True)
        self.content_area.controls.append(
            self._build_section(
                "全局参数",
                [
                    ft.Dropdown(
                        label="天气",
                        value=env.get("weather", "Clear"),
                        options=[
                            ft.dropdown.Option("Clear"),
                            ft.dropdown.Option("Rain"),
                        ],
                        dense=True,
                        bgcolor="rgba(255,255,255,0.02)",
                        on_select=lambda e: self._update_val(
                            env, "weather", e.control.value
                        ),
                    ),
                    ft.Dropdown(
                        label="场地",
                        value=env.get("field", "Neutral"),
                        options=[
                            ft.dropdown.Option("Neutral"),
                            ft.dropdown.Option("Ley Line Disorder"),
                        ],
                        dense=True,
                        bgcolor="rgba(255,255,255,0.02)",
                        on_select=lambda e: self._update_val(
                            env, "field", e.control.value
                        ),
                    ),
                ],
                color,
            )
        )

    def _add_hero_header(self, title, subtitle, color, can_back=False):
        items = []
        if can_back:
            items.append(
                ft.IconButton(
                    ft.Icons.ARROW_BACK_IOS_NEW,
                    icon_size=16,
                    icon_color=color,
                    on_click=lambda _: self.state.select_overview(),
                )
            )
        items.append(
            ft.Column(
                [
                    ft.Text(
                        title,
                        size=24,
                        weight=ft.FontWeight.W_900,
                        color=GenshinTheme.ON_SURFACE,
                    ),
                    ft.Text(
                        subtitle,
                        size=10,
                        weight=ft.FontWeight.BOLD,
                        color=color,
                        opacity=0.8,
                    ),
                ],
                spacing=0,
            )
        )
        self.content_area.controls.append(
            ft.Container(
                content=ft.Row(
                    items, spacing=15, vertical_alignment=ft.CrossAxisAlignment.CENTER
                ),
                padding=ft.padding.only(bottom=10),
                border=ft.border.only(
                    bottom=ft.BorderSide(1, "rgba(255,255,255,0.05)")
                ),
            )
        )

    def _build_section(self, title, controls, color, expand=False):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(title, size=10, weight=ft.FontWeight.W_900, opacity=0.3),
                    *controls,
                ],
                spacing=12,
            ),
            padding=20,
            bgcolor="rgba(255, 255, 255, 0.01)",
            border_radius=16,
            border=ft.border.only(left=ft.BorderSide(3, color)),
            expand=expand,
        )

    def _build_field(self, label, value, on_change_callback):
        return ft.TextField(
            label=label,
            value=str(value),
            width=80,
            dense=True,
            text_align=ft.TextAlign.CENTER,
            bgcolor="rgba(255, 255, 255, 0.02)",
            border_color="rgba(255, 255, 255, 0.1)",
            on_change=lambda e: on_change_callback(e.control.value),
            on_blur=lambda _: self.state.refresh(),
            input_filter=ft.InputFilter(
                allow=True, regex_string=r"[0-9\.\-]", replacement_string=""
            ),
        )

    def _build_filter_chip(self, label, current_val, on_click):
        is_active = label == current_val
        return ft.Container(
            content=ft.Text(
                label,
                size=11,
                weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.NORMAL,
            ),
            padding=ft.padding.symmetric(horizontal=12, vertical=6),
            bgcolor=ft.Colors.with_opacity(0.2, GenshinTheme.PRIMARY)
            if is_active
            else "rgba(255,255,255,0.03)",
            border_radius=20,
            on_click=lambda _: on_click(label),
        )

    def _build_char_card(self, name, element, color, is_implemented):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Stack(
                            [
                                ft.Container(
                                    content=ft.Text(
                                        element,
                                        size=40,
                                        weight=ft.FontWeight.W_900,
                                        color=ft.Colors.with_opacity(0.15, color),
                                    ),
                                    alignment=ft.Alignment.CENTER,
                                ),
                                ft.Icon(
                                    ft.Icons.PERSON
                                    if is_implemented
                                    else ft.Icons.LOCK_CLOCK,
                                    color=color,
                                    size=36,
                                ),
                            ],
                            alignment=ft.Alignment.CENTER,
                        ),
                        bgcolor=ft.Colors.with_opacity(0.05, color),
                        expand=True,
                        border_radius=ft.border_radius.only(top_left=12, top_right=12),
                    ),
                    ft.Container(
                        content=ft.Text(
                            name if is_implemented else f"{name}\n(待实现)",
                            size=10,
                            weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        bgcolor="rgba(0, 0, 0, 0.3)",
                        padding=ft.padding.symmetric(horizontal=4, vertical=6),
                        width=110,
                        alignment=ft.Alignment.CENTER,
                        border_radius=ft.border_radius.only(
                            bottom_left=12, bottom_right=12
                        ),
                    ),
                ],
                spacing=0,
            ),
            width=110,
            height=150,
            bgcolor="rgba(255, 255, 255, 0.02)",
            border_radius=12,
            opacity=1.0 if is_implemented else 0.4,
            on_click=(lambda _, n=name: self.state.add_character(n))
            if is_implemented
            else None,
            on_hover=(lambda e, c=color: self._handle_card_hover(e, c))
            if is_implemented
            else None,
        )

    def _handle_card_hover(self, e, color):
        if e.data == "true":
            e.control.scale = 1.05
            e.control.shadow = ft.BoxShadow(
                blur_radius=15, color=ft.Colors.with_opacity(0.2, color)
            )
        else:
            e.control.scale = 1.0
            e.control.shadow = None
        e.control.update()

    def _update_filter(self, filter_type, value):
        if filter_type == "element":
            self.filter_element = value
        else:
            self.filter_weapon = value
        self.refresh()

    def _update_val(self, obj, key, val, is_float=False):
        try:
            if is_float:
                obj[key] = float(val or 0.0)
            else:
                obj[key] = int(val or 0)
        except:
            pass

    def _update_talent(self, char_obj, idx, val):
        try:
            char_obj["talents"][idx] = int(val or 1)
        except:
            pass

    def _show_weapon_picker(self, weapon_type, weapon_ref):
        all_weapons = self.state.get_weapons(weapon_type)
        implemented_weapons = list(WeaponClassMap.keys())
        list_view = ft.ListView(expand=True, spacing=5, height=400)

        def select_and_close(name):
            weapon_ref["name"] = name
            self.page.pop_dialog()
            self.refresh()

        for w_name in all_weapons:
            is_implemented = w_name in implemented_weapons
            list_view.controls.append(
                ft.ListTile(
                    title=ft.Text(
                        w_name if is_implemented else f"{w_name} (待实现)",
                        size=13,
                        weight=ft.FontWeight.BOLD,
                        opacity=1.0 if is_implemented else 0.4,
                    ),
                    leading=ft.Icon(
                        ft.Icons.SHIELD_OUTLINED
                        if is_implemented
                        else ft.Icons.LOCK_CLOCK,
                        color=ft.Colors.YELLOW_700
                        if is_implemented
                        else ft.Colors.GREY_700,
                    ),
                    on_click=(lambda _, n=w_name: select_and_close(n))
                    if is_implemented
                    else None,
                    disabled=not is_implemented,
                )
            )
        dialog = ft.AlertDialog(
            title=ft.Text(f"选择{weapon_type}"),
            content=ft.Container(content=list_view, width=300),
            actions=[ft.TextButton("取消", on_click=lambda _: self.page.pop_dialog())],
        )
        self.page.show_dialog(dialog)
