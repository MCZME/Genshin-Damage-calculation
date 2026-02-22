import flet as ft
from ui.theme import GenshinTheme
from ui.services.ui_formatter import UIFormatter

class MemberSlot(ft.Container):
    """
    编队成员槽位组件 (原子化重构版)。
    支持显示角色头像、基础信息、武器、天赋及圣遗物摘要。
    """
    def __init__(
        self, 
        index: int, 
        member: dict, 
        is_selected: bool = False,
        on_click = None,
        on_remove = None,
        on_add = None
    ):
        super().__init__()
        self.index = index
        self.member = member
        self.is_selected = is_selected
        self.on_click_callback = on_click
        self.on_remove_callback = on_remove
        self.on_add_callback = on_add
        
        self._build_ui()

    def _build_ui(self):
        is_empty = self.member.get("id") is None
        elem_color = GenshinTheme.get_element_color(self.member.get("element", "Neutral"))

        if is_empty:
            self.content = ft.Column([
                ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE, color=ft.Colors.WHITE_24, size=28),
                ft.Text("添加角色", size=11, color=ft.Colors.WHITE_24, weight=ft.FontWeight.W_500)
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6)
            
            self.alignment = ft.Alignment.CENTER
            self.expand = True
            self.bgcolor = ft.Colors.with_opacity(0.03, ft.Colors.WHITE)
            self.border_radius = 12
            self.border = ft.Border.all(1, ft.Colors.with_opacity(0.12, ft.Colors.WHITE))
            self.on_click = lambda _: self.on_add_callback(self.index) if self.on_add_callback else None
            self.animate = ft.Animation(300, ft.AnimationCurve.DECELERATE)
            self.mouse_cursor = ft.MouseCursor.CLICK
            return

        # ── 数据准备 ──────────────────────────────────
        talents = self.member.get('talents', {'na': '1', 'e': '1', 'q': '1'})
        elem_name = self.member.get('element', 'Neutral')
        weapon = self.member.get('weapon', {})
        weapon_id = weapon.get('id')
        weapon_text = weapon_id.upper() if weapon_id else "未装备"
        weapon_ref = weapon.get('refinement', '1')
        artifact_sets = UIFormatter.format_artifact_sets(self.member)

        # ── 视觉参数 ──────────────────────────────────
        bg_opacity   = 0.28 if self.is_selected else 0.10
        text_alpha   = 1.0  if self.is_selected else 0.75
        border_w     = 2    if self.is_selected else 1
        border_alpha = 0.65 if self.is_selected else 0.12

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
                self.member.get("name", "?")[0],
                size=15, weight=ft.FontWeight.W_900, color=ft.Colors.WHITE
            ),
            width=36, height=36,
            bgcolor=ft.Colors.with_opacity(0.3, elem_color),
            border_radius=18,
            alignment=ft.Alignment.CENTER,
            border=ft.Border.all(1.5, ft.Colors.with_opacity(0.6 if self.is_selected else 0.25, elem_color))
        )
        name_col = ft.Column([
            ft.Text(
                self.member.get("name", "未选定"),
                size=13, weight=ft.FontWeight.W_900 if self.is_selected else ft.FontWeight.BOLD,
                color=ft.Colors.with_opacity(text_alpha, ft.Colors.WHITE),
                no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS,
            ),
            ft.Text(
                f"Lv.{self.member.get('level', '90')}  C{self.member.get('constellation', '0')}",
                size=10, color=ft.Colors.with_opacity(0.5, ft.Colors.WHITE),
            ),
        ], spacing=1, expand=True)

        # 移除按钮
        remove_icon = ft.Container(
            content=ft.Icon(ft.Icons.CLOSE, size=12,
                            color=ft.Colors.with_opacity(0.28, ft.Colors.WHITE)),
            width=22, height=22,
            border_radius=11,
            alignment=ft.Alignment.CENTER,
            on_click=self._on_remove_click,
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
        weapon_type = self.member.get('type', '单手剑')
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
        self.body = ft.Container(
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

        self.content = ft.Stack([
            ft.Container(expand=True, gradient=bg_gradient, border_radius=12),
            self.body,
        ])
        
        self.expand = True
        self.border_radius = 12
        self.border = ft.Border.all(border_w, ft.Colors.with_opacity(border_alpha, elem_color))
        self.shadow = GenshinTheme.get_element_glow(elem_name, 0.55) if self.is_selected else None
        self.on_click = lambda _: self.on_click_callback(self.index) if self.on_click_callback else None
        self.offset = ft.Offset(0.04, 0) if self.is_selected else ft.Offset(0, 0)
        self.animate = ft.Animation(300, ft.AnimationCurve.DECELERATE)
        self.animate_offset = ft.Animation(300, ft.AnimationCurve.EASE_OUT_BACK)
        self.mouse_cursor = ft.MouseCursor.CLICK

    def _on_remove_click(self, e):
        # 阻止冒泡：点击删除按钮时不触发槽位的点击选择
        e.control.page = self.page # 确保 e 有 page 属性（Flet 事件冒泡处理）
        if self.on_remove_callback:
            self.on_remove_callback(self.index)

    def _build_mini_talent_chip(self, label: str, val):
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

    def update_state(self, member: dict, is_selected: bool):
        """精准同步数据与选中态"""
        self.member = member
        self.is_selected = is_selected
        self._build_ui()
        try: self.update()
        except: pass
