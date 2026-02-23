import flet as ft
from ui.theme import GenshinTheme
from ui.components.stat_input import StatInputField
from core.registry import ArtifactSetMap
from core.data.repository import MySQLDataRepository

# 模块级缓存，避免重复查询数据库导致 UI 卡顿
_ARTIFACT_SET_OPTIONS_CACHE = None

class ArtifactSlot(ft.Container):
    """
    圣遗物配置插槽 (Reboot 增强版)。
    支持圣遗物命名、主词条属性+数值、副词条录入。
    """
    def __init__(
        self,
        slot_name: str, 
        data: dict, # 传入 state 中的对应部位字典
        element: str = "Neutral",
        on_change=None
    ):
        super().__init__()
        self.slot_name = slot_name
        self.data = data
        self.element = element
        self.on_change_callback = on_change
        
        # 候选主词条映射
        self.main_stat_options = {
            "Flower": ["生命值"],
            "Plume": ["攻击力"],
            "Sands": ["攻击力%", "生命值%", "防御力%", "元素精通", "元素充能效率%"],
            "Goblet": ["攻击力%", "生命值%", "防御力%", "元素精通", "火元素伤害加成%", "水元素伤害加成%", "风元素伤害加成%", "雷元素伤害加成%", "草元素伤害加成%", "冰元素伤害加成%", "岩元素伤害加成%", "物理伤害加成%"],
            "Circlet": ["攻击力%", "生命值%", "防御力%", "元素精通", "暴击率%", "暴击伤害%", "治疗加成%"]
        }

        self._build_ui()

    def _get_set_options(self):
        """获取并缓存圣遗物套装选项"""
        global _ARTIFACT_SET_OPTIONS_CACHE
        if _ARTIFACT_SET_OPTIONS_CACHE is not None:
            return _ARTIFACT_SET_OPTIONS_CACHE

        set_options = []
        try:
            # 尝试从数据库获取全量名称
            repo = MySQLDataRepository()
            set_options = repo.get_all_artifact_sets()
        except:
            pass
            
        if not set_options:
            # 尝试从注册表获取已实现的
            set_options = sorted(list(ArtifactSetMap.keys()))
            
        if not set_options:
            # 最后的保底
            set_options = ["黄金剧团", "绝缘之旗印", "逐影猎人", "深林的记忆", "饰金之梦"]
            
        # 排序并去重
        _ARTIFACT_SET_OPTIONS_CACHE = sorted(list(set(set_options)))
        return _ARTIFACT_SET_OPTIONS_CACHE

    def _build_ui(self):
        elem_color = GenshinTheme.get_element_color(self.element)
        
        # 部位名映射
        slot_cn = {
            "Flower": "生之花",
            "Plume": "死之羽",
            "Sands": "时之沙",
            "Goblet": "空之杯",
            "Circlet": "理之冠"
        }
        
        # 1. 顶部：部位名称
        header = ft.Row([
            ft.Text(slot_cn.get(self.slot_name, self.slot_name), size=13, color=elem_color, weight=ft.FontWeight.BOLD),
        ], alignment=ft.MainAxisAlignment.START)

        # 2. 圣遗物套装选择 (使用缓存提速)
        set_options = self._get_set_options()
            
        self.name_input = ft.Dropdown(
            value=self.data.get('name', ""),
            options=[ft.dropdown.Option(s) for s in set_options],
            hint_text="选择圣遗物套装...",
            dense=True,
            text_size=12,
            border=ft.InputBorder.UNDERLINE,
            border_color=ft.Colors.WHITE_10,
            focused_border_color=elem_color,
            on_select=self._handle_name_select,
            content_padding=ft.Padding(0, 5, 0, 5)
        )

        # 3. 主词条配置区域 (属性 + 数值)
        self.main_stat_drop = ft.Dropdown(
            value=self.data.get('main', self.main_stat_options[self.slot_name][0]),
            options=[ft.dropdown.Option(s) for s in self.main_stat_options[self.slot_name]],
            dense=True,
            text_size=12,
            border_radius=6,
            border=ft.Border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
            bgcolor=ft.Colors.BLACK26,
            height=34,
            expand=2,
            on_select=self._handle_main_attr_change
        )
        
        self.main_val_input = ft.TextField(
            value=self.data.get('main_val', "0"),
            dense=True,
            text_size=12,
            text_align=ft.TextAlign.RIGHT,
            border=ft.Border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
            border_radius=6,
            bgcolor=ft.Colors.BLACK26,
            height=34,
            expand=1,
            on_change=self._handle_main_val_change
        )

        # 4. 副词条列表
        sub_options = ["生命值", "生命值%", "攻击力", "攻击力%", "防御力", "防御力%", "元素精通", "元素充能效率%", "暴击率%", "暴击伤害%"]
        
        current_subs = self.data.get('subs', [["暴击率%", "0.0"]] * 4)
        self.substat_inputs = [
            StatInputField(
                label=sub[0], 
                value=sub[1], 
                element=self.element, 
                width=185,
                label_options=sub_options,
                on_change=lambda v, i=i: self._handle_sub_change(i, v),
                on_label_change=lambda l, i=i: self._handle_sub_label_change(i, l)
            ) for i, sub in enumerate(current_subs)
        ]

        # 5. 组装内容
        self.content = ft.Column([
            header,
            self.name_input,
            ft.Divider(height=2, color="transparent"), 
            ft.Text("主词条属性", size=10, color=GenshinTheme.TEXT_SECONDARY, weight=ft.FontWeight.W_600),
            ft.Row([self.main_stat_drop, self.main_val_input], spacing=5),
            ft.Divider(height=1, color=ft.Colors.WHITE_10),
            ft.Text("副词条属性", size=10, color=GenshinTheme.TEXT_SECONDARY, weight=ft.FontWeight.W_600),
            *self.substat_inputs
        ], spacing=5)
        
        self.padding = ft.Padding(15, 15, 15, 15)
        self.bgcolor = GenshinTheme.SURFACE_VARIANT
        self.border_radius = 10
        self.border = ft.Border.all(1, ft.Colors.with_opacity(0.1, GenshinTheme.ON_SURFACE))
        self.width = 215 
        self.mouse_cursor = ft.MouseCursor.BASIC # 属性赋值方式

    def _handle_name_select(self, e):
        self.data['name'] = e.control.value
        if self.on_change_callback: self.on_change_callback()

    def _handle_main_attr_change(self, e):
        self.data['main'] = e.control.value
        if self.on_change_callback: self.on_change_callback()

    def _handle_main_val_change(self, e):
        self.data['main_val'] = e.control.value
        if self.on_change_callback: self.on_change_callback()

    def _handle_sub_change(self, index, value):
        self.data['subs'][index][1] = value
        if self.on_change_callback: self.on_change_callback()

    def _handle_sub_label_change(self, index, label):
        self.data['subs'][index][0] = label
        if self.on_change_callback: self.on_change_callback()

    def update_state(self, data: dict, element: str, skip_update: bool = False):
        """精准同步圣遗物数据与元素主题"""
        self.data = data
        self.element = element
        elem_color = GenshinTheme.get_element_color(self.element)
        
        # 1. 更新下拉框与输入框值 (无需重建)
        self.name_input.value = self.data.get('name', "")
        self.name_input.focused_border_color = elem_color
        
        self.main_stat_drop.value = self.data.get('main', self.main_stat_options[self.slot_name][0])
        self.main_val_input.value = self.data.get('main_val', "0")
        
        # 2. 局部刷新所有部位 header 颜色 (Hack: 直接修改内部 Text)
        self.content.controls[0].controls[0].color = elem_color
        
        # 3. 更新副词条同步
        subs = self.data.get('subs', [])
        for i, sub in enumerate(subs):
            if i < len(self.substat_inputs):
                self.substat_inputs[i].update_state(sub[1], self.element, skip_update=True)
        
        # 4. 容器视觉更新
        if not skip_update:
            try: self.update()
            except: pass
