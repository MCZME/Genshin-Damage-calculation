import flet as ft


class GenshinTheme:
    """
    原神主题管理器 - 增强兼容性版
    """

    # --- 核心调色板 ---
    BACKGROUND = "#1A1625"
    PRIMARY = "#D1A2FF"
    ON_PRIMARY = "#2A0B3D"

    SURFACE = "#252131"
    SURFACE_VARIANT = "#322D41"
    ON_SURFACE = "#E5E1E6"
    TEXT_SECONDARY = "#ABA6B5"

    # --- 艺术装饰色 ---
    GOLD_LIGHT = "#F2E6C6" # 更亮的金色，用于高光
    GOLD_DARK = "#D3BC8E"  # 标准原神金

    # --- 玻璃拟态参数 ---
    GLASS_BG = "rgba(60, 55, 80, 0.4)"
    GLASS_BORDER = "rgba(200, 180, 255, 0.15)"
    HEADER_BG = "rgba(35, 30, 50, 0.6)"
    FOOTER_BG = "rgba(40, 35, 60, 0.9)"

    # --- 元素色映射 (中英文兼容) ---
    ELEMENT_COLORS = {
        # 英文
        "Pyro": "#FF4D4D",
        "Hydro": "#3399FF",
        "Anemo": "#66FFCC",
        "Electro": "#CC66FF",
        "Dendro": "#99FF33",
        "Cryo": "#99FFFF",
        "Geo": "#FFCC33",
        "Physical": "#E5E1E6",
        "Neutral": "#ABA6B5",
        # 中文
        "火": "#FF4D4D",
        "水": "#3399FF",
        "风": "#66FFCC",
        "雷": "#CC66FF",
        "草": "#99FF33",
        "冰": "#99FFFF",
        "岩": "#FFCC33",
        "物理": "#E5E1E6",
    }

    # --- 元素渐变 (用于背景与高亮) ---
    ELEMENT_GRADIENTS = {
        "火": ft.LinearGradient(begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1), colors=["#FF4D4D", "#B32424"]),
        "水": ft.LinearGradient(begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1), colors=["#3399FF", "#1A5299"]),
        "风": ft.LinearGradient(begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1), colors=["#66FFCC", "#2D997A"]),
        "雷": ft.LinearGradient(begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1), colors=["#CC66FF", "#7A2D99"]),
        "草": ft.LinearGradient(begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1), colors=["#99FF33", "#5C991F"]),
        "冰": ft.LinearGradient(begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1), colors=["#99FFFF", "#4D9999"]),
        "岩": ft.LinearGradient(begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1), colors=["#FFCC33", "#997A1F"]),
    }

    # --- 元素阴影 (用于呼吸灯效果) ---
    @staticmethod
    def get_element_glow(element: str, intensity: float = 0.5):
        """获取元素阴影效果 (带鲁棒性颜色获取与兼容性样式)"""
        color = GenshinTheme.get_element_color(element)
        return ft.BoxShadow(
            spread_radius=1,
            blur_radius=15 * intensity,
            color=color or GenshinTheme.ELEMENT_COLORS["Neutral"],
            offset=ft.Offset(0, 0),
            blur_style="outer",
        )

    @staticmethod
    def get_theme():
        return ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=GenshinTheme.PRIMARY,
                on_primary=GenshinTheme.ON_PRIMARY,
                surface=GenshinTheme.SURFACE,
                on_surface=GenshinTheme.ON_SURFACE,
                secondary=GenshinTheme.PRIMARY,
            ),
            use_material3=True,
            visual_density=ft.VisualDensity.COMFORTABLE,
        )

    @staticmethod
    def apply_page_settings(page: ft.Page):
        page.theme = GenshinTheme.get_theme()
        page.theme_mode = ft.ThemeMode.DARK
        page.bgcolor = GenshinTheme.BACKGROUND
        page.padding = 0
        page.spacing = 0

    @staticmethod
    def get_element_color(element: str):
        """根据元素名称获取对应颜色 (支持中英文，大小写不敏感)"""
        if not element:
            return GenshinTheme.ELEMENT_COLORS["Neutral"]
        
        # 1. 尝试直接匹配
        if element in GenshinTheme.ELEMENT_COLORS:
            return GenshinTheme.ELEMENT_COLORS[element]
            
        # 2. 尝试首字母大写匹配 (针对英文输入，如 "pyro" -> "Pyro")
        cap_elem = element.capitalize()
        if cap_elem in GenshinTheme.ELEMENT_COLORS:
            return GenshinTheme.ELEMENT_COLORS[cap_elem]
            
        # 3. 最终回退到中性色
        return GenshinTheme.ELEMENT_COLORS["Neutral"]

    @staticmethod
    def get_weapon_icon(weapon_type: str):
        """获取武器类型对应的图标"""
        mapping = {
            "单手剑": ft.Icons.SWORDS if hasattr(ft.Icons, "SWORDS") else ft.Icons.HARDWARE,
            "双手剑": ft.Icons.CONSTRUCTION,
            "长柄武器": ft.Icons.UPGRADE,
            "弓": ft.Icons.NEAR_ME,
            "法器": ft.Icons.AUTO_STORIES,
        }
        return mapping.get(weapon_type, ft.Icons.HARDWARE)
