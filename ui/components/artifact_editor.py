import flet as ft
import json
import os
from ui.theme import GenshinTheme
from core.registry import ArtifactSetMap

class ArtifactEditor(ft.Column):
    """
    圣遗物编辑器 (高辨识度无边框版)
    """
    SUB_STATS = {
        "生命值": False, "生命值%": True, "攻击力": False, "攻击力%": True,
        "防御力": False, "防御力%": True, "元素精通": False, "充能效率%": True,
        "暴击率%": True, "暴击伤害%": True, "治疗加成%": True
    }

    VALID_MAIN_STATS = {
        "flower": ["生命值"], "feather": ["攻击力"],
        "sands": ["生命值%", "攻击力%", "防御力%", "元素精通", "充能效率%"],
        "goblet": ["生命值%", "攻击力%", "防御力%", "元素精通", "物理伤害加成%", "火元素伤害加成%", "水元素伤害加成%", "草元素伤害加成%", "雷元素伤害加成%", "风元素伤害加成%", "冰元素伤害加成%", "岩元素伤害加成%"],
        "circlet": ["生命值%", "攻击力%", "防御力%", "元素精通", "暴击率%", "暴击伤害%", "治疗加成%"]
    }

    def __init__(self, state):
        super().__init__(spacing=15)
        self.state = state
        self.char_data = None 
        
    def set_character(self, char_data: dict):
        self.char_data = char_data
        self._rebuild_controls()

    def _rebuild_controls(self):
        self.controls.clear()
        if not self.char_data: return
        arts = self.char_data["artifacts"]
        
        # 顶部工具栏 (无边框风格)
        self.controls.append(
            ft.Row([
                ft.Text("圣遗物配置 (ARTIFACTS)", size=10, weight=ft.FontWeight.W_900, opacity=0.3),
                ft.Row([
                    ft.TextButton("导出", icon=ft.Icons.UPLOAD_FILE, on_click=self._handle_export_set),
                    ft.TextButton("导入", icon=ft.Icons.DOWNLOAD_FOR_OFFLINE, on_click=self._handle_import_set),
                ], spacing=0)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        )
        
        grid = ft.Row(wrap=True, spacing=10, run_spacing=10)
        # 部位首字映射
        slots = [
            ("flower", "花", "生之花", ft.Icons.LOCAL_FLORIST),
            ("feather", "羽", "死之羽", ft.Icons.BRUSH), 
            ("sands", "沙", "时之沙", ft.Icons.TIMER),
            ("goblet", "杯", "空之杯", ft.Icons.WINE_BAR),
            ("circlet", "冠", "理之冠", ft.Icons.ACCOUNT_BALANCE),
        ]
        for key, initial, label, icon in slots:
            # 防御性：如果由于某种原因缺失该部位，显示一个默认值而不是报错
            slot_data = arts.get(key, {"set": "未装备", "main": "生命值", "value": 0, "subs": []})
            grid.controls.append(self._build_slot_block(key, initial, label, slot_data))
        
        self.controls.append(grid)

    def refresh(self):
        self._rebuild_controls()
        if self.page:
            try: self.update()
            except: pass

    def _build_slot_block(self, key, initial, full_label, data):
        """构建高辨识度无边框部位块"""
        accent_color = GenshinTheme.get_element_color(self.char_data["character"]["element"])
        is_pct = data["main"].endswith("%")
        val_str = f"{data['value']}%" if is_pct else f"{int(data['value'])}"
        
        sub_previews = []
        for sub in data.get("subs", [])[:4]:
            s_pct = sub['key'].endswith("%")
            sub_previews.append(
                ft.Text(f"{sub['key']} +{sub['value']}{'%' if s_pct else ''}", size=8, color=GenshinTheme.TEXT_SECONDARY)
            )

        return ft.Container(
            width=135, height=130,
            padding=ft.padding.all(12),
            bgcolor="rgba(255, 255, 255, 0.03)",
            border_radius=12,
            on_click=lambda _: self._open_slot_editor(key),
            on_hover=lambda e: self._handle_block_hover(e, accent_color),
            animate=ft.Animation(200, ft.AnimationCurve.DECELERATE),
            content=ft.Column([
                # 顶部：首字强化
                ft.Row([
                    ft.Text(initial, size=20, weight=ft.FontWeight.W_900, color=accent_color),
                    ft.Column([
                        ft.Text(full_label[1:], size=10, weight=ft.FontWeight.BOLD, opacity=0.4),
                        ft.Text(data["set"], size=9, weight=ft.FontWeight.BOLD, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                    ], spacing=-2, expand=True),
                ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                
                # 中部：主词条
                ft.Container(
                    content=ft.Text(f"{data['main']} {val_str}", size=10, weight=ft.FontWeight.W_900, color=accent_color),
                    padding=ft.padding.symmetric(vertical=4)
                ),
                
                ft.Divider(height=1, color="rgba(255,255,255,0.05)"),
                
                # 底部：副词条预览
                ft.Column(sub_previews, spacing=0)
            ], spacing=2)
        )

    def _handle_block_hover(self, e, color):
        if e.data == "true":
            e.control.bgcolor = ft.Colors.with_opacity(0.1, color)
            e.control.shadow = ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.1, color))
        else:
            e.control.bgcolor = "rgba(255, 255, 255, 0.03)"
            e.control.shadow = None
        e.control.update()

    # --- 逻辑处理 (保存/导入/弹窗编辑保持不变) ---

    def _handle_export_set(self, _):
        name_input = ft.TextField(label="名称", value=f"{self.char_data['character']['name']}_预设", dense=True)
        def confirm(_):
            if name_input.value: self.state.save_artifact_set_template(self.char_data["artifacts"], name_input.value); self.page.pop_dialog()
        self.page.show_dialog(ft.AlertDialog(title=ft.Text("导出套装"), content=name_input, actions=[ft.ElevatedButton("导出", on_click=confirm)]))

    def _handle_import_set(self, _):
        templates = self.state.list_templates("artifacts"); lv = ft.ListView(expand=True, spacing=5, height=300)
        def confirm(fname):
            path = os.path.join("data/templates/artifacts", fname)
            with open(path, "r", encoding="utf-8") as f: self.char_data["artifacts"] = json.load(f)
            self.page.pop_dialog(); self.refresh(); self.state.refresh()
        for t in templates: lv.controls.append(ft.ListTile(title=ft.Text(t), on_click=lambda _, n=t: confirm(n)))
        self.page.show_dialog(ft.AlertDialog(title=ft.Text("导入套装"), content=ft.Container(lv, width=300)))

    def _open_slot_editor(self, key):
        data = self.char_data["artifacts"][key]; implemented_sets = list(ArtifactSetMap.keys())
        set_options = [ft.dropdown.Option("未装备")]
        for s_name in self.state.artifact_sets:
            is_imp = s_name in implemented_sets
            set_options.append(ft.dropdown.Option(key=s_name, text=s_name if is_imp else f"{s_name}(待)", disabled=not is_imp))
        set_drop = ft.Dropdown(label="套装", value=data["set"], options=set_options, dense=True, expand=True)
        valid_mains = self.VALID_MAIN_STATS.get(key, ["生命值"])
        if data["main"] not in valid_mains: data["main"] = valid_mains[0]
        main_drop = ft.Dropdown(label="主词条", value=data["main"], options=[ft.dropdown.Option(m) for m in valid_mains], dense=True, expand=True)
        main_val_field = ft.TextField(label="数值", value=str(data["value"]), dense=True, width=120, input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9\.]", replacement_string=""))
        sub_inputs = []; sub_rows = []
        while len(data["subs"]) < 4: data["subs"].append({"key": "无", "value": 0.0})
        for i in range(4):
            sub_data = data["subs"][i]
            k_drop = ft.Dropdown(value=sub_data["key"], options=[ft.dropdown.Option("无")] + [ft.dropdown.Option(s) for s in self.SUB_STATS.keys()], dense=True, width=160)
            v_field = ft.TextField(value=str(sub_data["value"]), dense=True, width=100, input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9\.]", replacement_string=""))
            sub_inputs.append((k_drop, v_field)); sub_rows.append(ft.Row([ft.Text(f"#{i+1}", size=10, opacity=0.3), k_drop, v_field], spacing=10))
        def save_and_close(e):
            data["set"] = set_drop.value; data["main"] = main_drop.value; data["value"] = float(main_val_field.value or 0); data["subs"] = []
            for k, v in sub_inputs:
                if k.value != "无": data["subs"].append({"key": k.value, "value": float(v.value or 0)})
            self.page.pop_dialog(); self.refresh(); self.state.refresh()
        dialog = ft.AlertDialog(title=ft.Text(f"编辑 {key.upper()}"), content=ft.Container(content=ft.Column([set_drop, ft.Row([main_drop, main_val_field], spacing=10), ft.Divider(height=10, color="transparent"), ft.Text("副词条配置", size=10, weight=ft.FontWeight.BOLD, opacity=0.4), *sub_rows], spacing=10, scroll=ft.ScrollMode.AUTO, height=450), width=400), actions=[ft.TextButton("取消", on_click=lambda _: self.page.pop_dialog()), ft.ElevatedButton("应用修改", bgcolor=ft.Colors.PRIMARY, color=ft.Colors.ON_PRIMARY, on_click=save_and_close)])
        self.page.show_dialog(dialog)
