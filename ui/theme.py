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
    
    # --- 玻璃拟态参数 ---
    GLASS_BG = "rgba(60, 55, 80, 0.4)"      
    GLASS_BORDER = "rgba(200, 180, 255, 0.15)" 
    HEADER_BG = "rgba(35, 30, 50, 0.6)"     
    FOOTER_BG = "rgba(40, 35, 60, 0.9)"     

    # --- 元素色映射 (中英文兼容) ---
    ELEMENT_COLORS = {
        # 英文
        "Pyro": "#FF7E7E", "Hydro": "#4CC2F1", "Anemo": "#72E2C7",
        "Electro": "#D1A2FF", "Dendro": "#A6E3A1", "Cryo": "#A0E9FF",
        "Geo": "#FFE699", "Physical": "#E5E1E6", "Neutral": "#ABA6B5",
        # 中文
        "火": "#FF7E7E", "水": "#4CC2F1", "风": "#72E2C7",
        "雷": "#D1A2FF", "草": "#A6E3A1", "冰": "#A0E9FF",
        "岩": "#FFE699", "物理": "#E5E1E6"
    }

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
        """根据元素名称获取对应颜色 (支持中英文)"""
        if not element: return GenshinTheme.ELEMENT_COLORS["Neutral"]
        return GenshinTheme.ELEMENT_COLORS.get(element, GenshinTheme.ELEMENT_COLORS["Neutral"])
