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

        # ── 持久化控件引用 (用于非破坏性更新) ──────────────────
        self.avatar_text = ft.Text(self.member.get("name", "?")[0], size=15, weight=ft.FontWeight.W_900, color=ft.Colors.WHITE)
        self.name_text = ft.Text(self.member.get("name", "未选定"), size=13, weight=ft.FontWeight.BOLD, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS)
        self.lvl_text = ft.Text(f"Lv.{self.member.get('level', '90')}  C{self.member.get('constellation', '0')}", size=10, color=ft.Colors.with_opacity(0.5, ft.Colors.WHITE))
        
        self.t_a_val = ft.Text(str(self.member.get('talents', {}).get('na', '1')), size=13, weight=ft.FontWeight.W_900, color=ft.Colors.WHITE)
        self.t_e_val = ft.Text(str(self.member.get('talents', {}).get('e', '1')), size=13, weight=ft.FontWeight.W_900, color=ft.Colors.WHITE)
        self.t_q_val = ft.Text(str(self.member.get('talents', {}).get('q', '1')), size=13, weight=ft.FontWeight.W_900, color=ft.Colors.WHITE)
        
        self.weapon_icon_ctrl = ft.Icon(GenshinTheme.get_weapon_icon(self.member.get('type', '单手剑')), size=11, color=ft.Colors.with_opacity(0.45, ft.Colors.WHITE))
        self.weapon_text_ctrl = ft.Text("", size=10, color=ft.Colors.with_opacity(0.65, ft.Colors.WHITE), no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS, expand=True)
        self.artifact_text_ctrl = ft.Text("", size=10, color=ft.Colors.with_opacity(0.65, ft.Colors.WHITE), no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS, expand=True)

        # ── 视觉参数 ──────────────────────────────────
        bg_opacity   = 0.28 if self.is_selected else 0.10
        border_w     = 2    if self.is_selected else 1
        border_alpha = 0.65 if self.is_selected else 0.12

        # 元素色渐变底
        self.bg_gradient_ctrl = ft.Container(expand=True, border_radius=12)
        self._update_visual_style() # 初次设置样式

        # ── 顶行布局 ──────────────
        self.avatar_container = ft.Container(
            content=self.avatar_text,
            width=36, height=36,
            bgcolor=ft.Colors.with_opacity(0.3, elem_color),
            border_radius=18,
            alignment=ft.Alignment.CENTER,
            border=ft.Border.all(1.5, ft.Colors.with_opacity(0.25, elem_color))
        )
        
        remove_icon = ft.Container(
            content=ft.Icon(ft.Icons.CLOSE, size=12, color=ft.Colors.with_opacity(0.28, ft.Colors.WHITE)),
            width=22, height=22, border_radius=11, alignment=ft.Alignment.CENTER,
            on_click=self._on_remove_click,
        )
        remove_icon.mouse_cursor = ft.MouseCursor.CLICK

        top_row = ft.Row(
            [self.avatar_container, ft.Column([self.name_text, self.lvl_text], spacing=1, expand=True), remove_icon],
            spacing=9, vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # ── 中间行 ──────────────
        talent_row = ft.Row([
            self._build_mini_talent_container("A", self.t_a_val),
            self._build_mini_talent_container("E", self.t_e_val),
            self._build_mini_talent_container("Q", self.t_q_val),
        ], spacing=5)

        weapon_row = ft.Row([self.weapon_icon_ctrl, self.weapon_text_ctrl], spacing=5)
        artifact_row = ft.Row([ft.Icon(ft.Icons.AUTO_AWESOME, size=11, color=ft.Colors.with_opacity(0.45, ft.Colors.WHITE)), self.artifact_text_ctrl], spacing=5)

        divider = ft.Container(height=1, bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE), margin=ft.margin.symmetric(vertical=2))

        # ── 组装 ──────────────────────────────────────
        self.body = ft.Container(
            content=ft.Column([top_row, divider, talent_row, weapon_row, artifact_row], spacing=5, alignment=ft.MainAxisAlignment.START),
            padding=ft.Padding(11, 11, 11, 10), expand=True,
        )

        self.content = ft.Stack([self.bg_gradient_ctrl, self.body])
        
        self.expand = True
        self.border_radius = 12
        self._sync_content_data() # 同步具体文本数据

        self.on_click = lambda _: self.on_click_callback(self.index) if self.on_click_callback else None
        self.animate = ft.Animation(300, ft.AnimationCurve.DECELERATE)
        self.animate_offset = ft.Animation(300, ft.AnimationCurve.EASE_OUT_BACK)
        self.mouse_cursor = ft.MouseCursor.CLICK

    def _on_remove_click(self, e):
        # 触发移除回调
        if self.on_remove_callback:
            self.on_remove_callback(self.index)

    def _build_mini_talent_container(self, label: str, val_ctrl: ft.Text):
        return ft.Container(
            content=ft.Column([
                ft.Text(label, size=9, weight=ft.FontWeight.W_900, color=ft.Colors.with_opacity(0.55, ft.Colors.WHITE)),
                val_ctrl,
            ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=ft.Colors.with_opacity(0.35, ft.Colors.BLACK),
            padding=ft.Padding(7, 4, 7, 4),
            border_radius=6,
            border=ft.Border.all(1, ft.Colors.with_opacity(0.15, ft.Colors.WHITE)),
        )

    def _update_visual_style(self):
        """更新选中态、边框、阴影、偏移等外观属性 (不触及内容)"""
        elem_color = GenshinTheme.get_element_color(self.member.get("element", "Neutral"))
        bg_opacity = 0.28 if self.is_selected else 0.10
        
        self.bg_gradient_ctrl.gradient = ft.LinearGradient(
            begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1),
            colors=[
                ft.Colors.with_opacity(bg_opacity, elem_color),
                ft.Colors.with_opacity(bg_opacity * 0.3, elem_color),
            ]
        )
        self.border = ft.Border.all(2 if self.is_selected else 1, ft.Colors.with_opacity(0.65 if self.is_selected else 0.12, elem_color))
        self.shadow = GenshinTheme.get_element_glow(self.member.get("element", "Neutral"), 0.55) if self.is_selected else None
        self.offset = ft.Offset(0.04, 0) if self.is_selected else ft.Offset(0, 0)
        self.name_text.weight = ft.FontWeight.W_900 if self.is_selected else ft.FontWeight.BOLD
        self.name_text.color = ft.Colors.with_opacity(1.0 if self.is_selected else 0.75, ft.Colors.WHITE)

    def _sync_content_data(self):
        """同步具体的角色、武器、天赋数值数据"""
        m = self.member
        talents = m.get('talents', {'na': '1', 'e': '1', 'q': '1'})
        weapon = m.get('weapon', {})
        weapon_id = weapon.get('id')
        
        self.avatar_text.value = m.get("name", "?")[0]
        self.name_text.value = m.get("name", "未选定")
        self.lvl_text.value = f"Lv.{m.get('level', '90')}  C{m.get('constellation', '0')}"
        
        self.t_a_val.value = str(talents.get('na', '1'))
        self.t_e_val.value = str(talents.get('e', '1'))
        self.t_q_val.value = str(talents.get('q', '1'))
        
        self.weapon_icon_ctrl.name = GenshinTheme.get_weapon_icon(m.get('type', '单手剑'))
        self.weapon_text_ctrl.value = f"{weapon_id.upper()[:10]}  Lv.{weapon.get('level', '90')} R{weapon.get('refinement', '1')}" if weapon_id else "未装备武器"
        
        self.artifact_text_ctrl.value = UIFormatter.format_artifact_sets(m) or "未配置圣遗物"

    def update_state(self, member: dict, is_selected: bool, skip_update: bool = False):
        """精准同步数据与选中态 (非破坏性)"""
        if self.member.get("id") is None and member.get("id") is not None:
            # 如果从空位变为有角色，则必须重绘
            self.member = member
            self.is_selected = is_selected
            self._build_ui()
        elif member.get("id") is None:
            # 如果变为空位，也重绘
            self.member = member
            self._build_ui()
        else:
            # 核心优化：仅修改现有属性
            self.member = member
            self.is_selected = is_selected
            self._update_visual_style()
            self._sync_content_data()

        if not skip_update:
            try: self.update()
            except: pass
