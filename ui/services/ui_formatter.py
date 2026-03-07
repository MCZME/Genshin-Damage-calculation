import flet as ft
from ui.theme import GenshinTheme

class UIFormatter:
    """
    UI 格式化工具：集中处理颜色、文字转换及展示逻辑。
    实现业务数据到视觉展现的解耦。
    """
    
    @staticmethod
    def format_artifact_sets(member_data: dict) -> str:
        """从成员数据解析并格式化圣遗物套装描述"""
        artifacts = member_data.get('artifacts', {})
        counts: dict[str, int] = {}
        for slot_data in artifacts.values():
            name = slot_data.get('name', '').strip()
            if name:
                counts[name] = counts.get(name, 0) + 1

        # 取 2 件及以上的，最多显示两个套装
        sets = sorted([(n, c) for n, c in counts.items() if c >= 2], key=lambda x: -x[1])
        if not sets:
            return "未配置圣遗物"
        parts = [f"{n[:4]}·{c}件" for n, c in sets[:2]]
        return "  ".join(parts)

    @staticmethod
    def shorten_action_label(label: str) -> str:
        """将长招式名转换为简短标签"""
        return (label.replace("普通攻击", "普攻")
                     .replace("元素战技", "战技")
                     .replace("元素爆发", "爆发")
                     .replace("重击/蓄力", "重击"))

    @staticmethod
    def format_distance(pos: dict) -> str:
        """格式化欧氏距离显示"""
        import math
        dist = math.sqrt(pos.get('x', 0)**2 + pos.get('z', 0)**2)
        return f"{dist:.1f}m"

    @staticmethod
    def get_rarity_color(rarity: int) -> str:
        """获取稀有度对应的颜色"""
        colors = {
            5: ft.Colors.AMBER_400,
            4: ft.Colors.PURPLE_400,
            3: ft.Colors.BLUE_400,
            2: ft.Colors.GREEN_400,
            1: ft.Colors.GREY_400
        }
        return colors.get(rarity, ft.Colors.WHITE_24)

    @staticmethod
    def get_element_icon(element: str):
        """获取元素对应的图标"""
        icons = {
            "Pyro": ft.Icons.WHATSHOT,
            "Hydro": ft.Icons.WATER_DROP,
            "Anemo": ft.Icons.AIR,
            "Electro": ft.Icons.FLASH_ON,
            "Dendro": ft.Icons.GRASS,
            "Cryo": ft.Icons.AC_UNIT,
            "Geo": ft.Icons.LANDSCAPE,
            "Neutral": ft.Icons.SHIELD
        }
        return icons.get(element, ft.Icons.HELP_OUTLINE)

    @staticmethod
    def format_metric_value(val: float, precision: int = 0) -> str:
        """格式化数值指标，增加千分位分隔符"""
        if val >= 1000000:
            return f"{val/1000000:.2f}M"
        return f"{val:,.{precision}f}"
