import os
from typing import Any

from core.logger import get_emulation_logger


class DataGenerator:
    """
    代码生成器。
    负责将清洗后的数据渲染为本地 Python 配置文件 (data.py)。
    """

    def generate_character_data(self, data: dict[str, Any], output_path: str) -> bool:
        """生成角色数据文件。"""
        try:
            m = data["metadata"]
            lines = [
                f'"""{m["name"]} 的自动化提取数据 (V2.3.1)。"""',
                "",
                "# --- 角色基础信息 ---",
                f'NAME = "{m["name"]}"',
                f"ID = {m['id']}",
                f"RARITY = {m['rarity']}",
                f'ELEMENT = "{m["element"]}"',
                f'WEAPON_TYPE = "{m["weapon_type"]}"',
                f'BREAKTHROUGH_PROP = "{m["breakthrough_prop"]}"',
                "",
                "# --- 属性成长表 (1-100级) ---",
                "BASE_STATS = {",
            ]

            for lv, stats in data["base_stats"].items():
                lines.append(f"    {lv}: {stats},")
            lines.append("}")
            lines.append("")

            skill_vars = {
                "normal": "NORMAL_ATTACK_DATA",
                "skill": "ELEMENTAL_SKILL_DATA",
                "burst": "ELEMENTAL_BURST_DATA",
            }

            for s_key, var_name in skill_vars.items():
                s_info = data["skills"].get(s_key)
                if not s_info:
                    continue
                lines.append(f"# --- {s_info['name']} ({s_key}) ---")
                lines.append(f"{var_name} = {{")
                for label, info in s_info["data"].items():
                    clean_label = label.replace('"', '\\"')
                    lines.append(
                        f'    "{clean_label}": ["{info["scaling"]}", {info["levels"]}],'
                    )
                lines.append("}")
                lines.append("")

            lines.append("# --- 命座效果概要 ---")
            lines.append("CONSTELLATIONS = {")
            for i, c in enumerate(data["constellations"]):
                clean_name = c["name"].replace('"', '\\"')
                safe_desc = c["desc"].replace('"', '\\"').replace("\n", "\\n")
                lines.append(
                    f'    {i + 1}: {{ "name": "{clean_name}", "desc": "{safe_desc}" }},'
                )
            lines.append("}")
            lines.append("")

            lines.append("# --- 原始描述文本 (开发参考) ---")
            lines.append("DESCRIPTIONS = {")
            for k, text in data["descriptions"].items():
                safe_text = text.replace('"', '\\"').replace("\n", "\\n")
                lines.append(f'    "{k}": "{safe_text}",')
            lines.append("}")
            lines.append("")

            lines.append("# --- 动作帧数 (默认占位，需手动校对) ---")
            lines.append("FRAME_DATA = {")
            lines.append('    "NORMAL_1": {"total": 30, "hit": [10]},')
            lines.append('    "SKILL_PRESS": {"total": 40, "hit": [15]},')
            lines.append('    "BURST_CAST": {"total": 100, "hit": [60]},')
            lines.append("}")

            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            return True
        except Exception as e:
            print(f"代码生成失败: {str(e)}")
            return False

    def generate_weapon_data(self, data: dict[str, Any], output_path: str) -> bool:
        """生成武器代码文件。"""
        try:
            m = data["metadata"]

            # 生成类名（中文转拼音或使用 route）
            class_name = self._generate_class_name(m.get("route", m["name"]))
            weapon_type_dir = self._get_weapon_type_dir(m["type"])

            lines = [
                f'"""{m["name"]} 的自动化提取数据。"""',
                "",
                "from typing import Any",
                "from weapon.weapon import Weapon",
                "from core.registry import register_weapon",
                "",
                "",
                f'@register_weapon("{m["name"]}", "{m["type"]}")',
                f"class {class_name}(Weapon):",
                f'    """{m["name"]}：武器描述待补充。"""',
                "",
                f"    ID = {m['id']}",
                "",
                "    def __init__(",
                "        self,",
                "        character: Any,",
                "        level: int = 1,",
                "        lv: int = 1,",
                "        base_data: dict[str, Any] | None = None,",
                "    ):",
                f"        super().__init__(character, {class_name}.ID, level, lv, base_data)",
                "",
                "    def skill(self) -> None:",
                "        # TODO: 实现武器特效",
                "        pass",
            ]

            # 确保目录存在：weapon/{TYPE}/
            dir_path = os.path.join("weapon", weapon_type_dir)
            os.makedirs(dir_path, exist_ok=True)

            # 写入文件
            file_path = os.path.join(dir_path, f"{class_name.lower()}.py")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

            get_emulation_logger().log_info(
                f"武器代码文件已生成: {file_path}", sender="Generator"
            )
            return True
        except Exception as e:
            get_emulation_logger().log_error(
                f"武器代码生成失败: {str(e)}", sender="Generator"
            )
            return False

    def _generate_class_name(self, route: str) -> str:
        """根据 route 生成类名。"""
        if not route:
            return "UnknownWeapon"
        # 移除空格，转为驼峰
        # route 可能是 "Aqua Simulacra" 或 "aqua_simulacra"
        route = route.replace("_", " ")
        parts = route.split()
        return "".join(part.capitalize() for part in parts)

    def _get_weapon_type_dir(self, weapon_type: str) -> str:
        """获取武器类型目录名。"""
        type_map = {
            "单手剑": "SWORD",
            "双手剑": "CLAYMORE",
            "长柄武器": "POLEARM",
            "弓": "BOW",
            "法器": "CATALYST",
        }
        return type_map.get(weapon_type, "OTHER")
