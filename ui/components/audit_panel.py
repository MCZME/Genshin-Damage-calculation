import flet as ft
from ui.theme import GenshinTheme

class AuditPanel(ft.Container):
    """
    扁平化伤害审计面板。
    一次性平铺展示单笔伤害的所有公式乘区与 Buff 来源。
    """
    def __init__(self, audit_item=None):
        super().__init__()
        self.item = audit_item
        self._build_ui()

    def _build_ui(self):
        if not self.item:
            self.content = ft.Container(
                content=ft.Text("CLICK A DAMAGE POINT TO VIEW AUDIT", size=12, opacity=0.3),
                alignment=ft.Alignment.CENTER,
                height=200
            )
            return

        # 1. 顶部基本信息
        header = ft.Row([
            ft.Text(f"第 {self.item.frame} 帧", size=14, weight=ft.FontWeight.BOLD, color=GenshinTheme.PRIMARY),
            ft.Text(f"{self.item.char_name}: {self.item.action}", size=14, weight=ft.FontWeight.W_500),
            ft.VerticalDivider(width=1),
            ft.Text(f"总伤害: {self.item.total_dmg:,.0f}", size=18, weight=ft.FontWeight.W_900, color=ft.Colors.AMBER_400),
        ], spacing=20)

        # 2. 公式因子展示 (扁平化)
        factors = ft.Row([
            self._build_factor("最终攻击", f"{self.item.atk_final:,.0f}"),
            self._build_factor("技能倍率", f"{self.item.multiplier_sum * 100:.1f}%"),
            self._build_factor("增伤乘区", f"{self.item.dmg_bonus * 100:.1f}%"),
            self._build_factor("暴击乘区", f"{self.item.crit_factor:.2f}x"),
            self._build_factor("防御减伤", f"{self.item.def_factor:.3f}"),
            self._build_factor("抗性乘区", f"{self.item.res_factor:.3f}"),
            self._build_factor("反应乘区", f"{self.item.reaction_mult:.2f}x"),
        ], spacing=15, wrap=True)

        # 3. 审计标签池 (谁给了加成)
        claims_chips = ft.Row([
            ft.Container(
                content=ft.Text(claim, size=10, color=ft.Colors.WHITE_70),
                bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.BLUE_GREY_200),
                padding=ft.Padding(8, 4, 8, 4),
                border_radius=4,
                border=ft.Border.all(1, ft.Colors.with_opacity(0.2, ft.Colors.WHITE))
            ) for claim in self.item.claims
        ], wrap=True, spacing=8)

        # 组装容器
        self.content = ft.Column([
            header,
            ft.Divider(height=1, color=ft.Colors.WHITE_10),
            ft.Text("伤害公式细节拆解", size=10, weight=ft.FontWeight.BOLD, opacity=0.4),
            factors,
            ft.Divider(height=1, color=ft.Colors.WHITE_10),
            ft.Text("审计溯源 (当前激活的增益/修正项)", size=10, weight=ft.FontWeight.BOLD, opacity=0.4),
            claims_chips
        ], spacing=15)

        self.padding = 25
        self.bgcolor = ft.Colors.with_opacity(0.05, ft.Colors.BLACK)
        self.border_radius = 12
        self.border = ft.Border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE))

    def _build_factor(self, label, val):
        return ft.Column([
            ft.Text(label, size=9, color=GenshinTheme.TEXT_SECONDARY),
            ft.Text(val, size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
        ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.START)

    def update_item(self, new_item):
        self.item = new_item
        self._build_ui()
        try:
            self.update()
        except: pass
