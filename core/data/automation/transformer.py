import re
from typing import Any, Dict, List


class DataTransformer:
    """
    数据转换器 (V2.3.3 高精度复合版)。
    支持复合倍率解析 (百分比+固定值) 及多段伤害拆分。
    """

    ELEMENT_MAP = {
        "Ice": "冰",
        "Fire": "火",
        "Water": "水",
        "Wind": "风",
        "Electric": "雷",
        "Rock": "岩",
        "Grass": "草",
    }

    WEAPON_MAP = {
        "WEAPON_SWORD_ONE_HAND": "单手剑",
        "WEAPON_CLAYMORE": "双手剑",
        "WEAPON_POLE": "长柄武器",
        "WEAPON_BOW": "弓",
        "WEAPON_CATALYST": "法器",
    }

    FIGHT_PROP_MAP = {
        "FIGHT_PROP_BASE_HP": "生命值",
        "FIGHT_PROP_BASE_ATTACK": "攻击力",
        "FIGHT_PROP_BASE_DEFENSE": "防御力",
        "FIGHT_PROP_CRITICAL": "暴击率",
        "FIGHT_PROP_CRITICAL_HURT": "暴击伤害",
        "FIGHT_PROP_CHARGE_EFFICIENCY": "元素充能效率",
        "FIGHT_PROP_ELEMENT_MASTERY": "元素精通",
        "FIGHT_PROP_HEAL_ADD": "治疗加成",
        "FIGHT_PROP_ATTACK_PERCENT": "攻击力%",
        "FIGHT_PROP_HP_PERCENT": "生命值%",
        "FIGHT_PROP_DEFENSE_PERCENT": "防御力%",
        "FIGHT_PROP_WATER_ADD_HURT": "水元素伤害加成",
        "FIGHT_PROP_FIRE_ADD_HURT": "火元素伤害加成",
        "FIGHT_PROP_ICE_ADD_HURT": "冰元素伤害加成",
        "FIGHT_PROP_ELEC_ADD_HURT": "雷元素伤害加成",
        "FIGHT_PROP_WIND_ADD_HURT": "风元素伤害加成",
        "FIGHT_PROP_ROCK_ADD_HURT": "岩元素伤害加成",
        "FIGHT_PROP_GRASS_ADD_HURT": "草元素伤害加成",
        "FIGHT_PROP_PHYSICAL_ADD_HURT": "物理伤害加成",
    }

    def transform(
        self, char_raw: Dict[str, Any], curve_raw: Dict[str, Any]
    ) -> Dict[str, Any]:
        data = char_raw
        special_prop_key = data.get("specialProp", "")

        result = {
            "metadata": {
                "id": data.get("id"),
                "name": data.get("name"),
                "rarity": data.get("rank"),
                "route": data.get("route"),
                "element": self.ELEMENT_MAP.get(
                    data.get("element"), data.get("element")
                ),
                "weapon_type": self.WEAPON_MAP.get(
                    data.get("weaponType"), data.get("weaponType")
                ),
                "breakthrough_prop": self.FIGHT_PROP_MAP.get(
                    special_prop_key, "未知属性"
                ),
            },
            "base_stats": self._calculate_all_levels(char_raw, curve_raw),
            "skills": self._parse_skills(data.get("talent", {})),
            "constellations": self._parse_constellations(data.get("constellation", {})),
            "descriptions": self._collect_descriptions(data),
        }
        return result

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        text = re.sub(r"<color=[^>]+>", "", text)
        text = re.sub(r"</color>", "", text)
        text = re.sub(r"<i>", "", text)
        text = re.sub(r"</i>", "", text)
        text = text.replace("\\n", "\n")
        return text

    def _calculate_all_levels(
        self, char_raw: Dict[str, Any], curve_raw: Dict[str, Any]
    ) -> Dict[int, Dict[str, Any]]:
        upgrade = char_raw.get("upgrade", {})
        promote_list = upgrade.get("promote", [])
        dictionary = curve_raw
        prop_configs = {
            p["propType"]: {"init": p["initValue"], "curve": p["type"]}
            for p in upgrade.get("prop", [])
        }
        special_prop_key = char_raw.get("specialProp")

        target_levels = {
            1: 0,
            20: 1,
            40: 2,
            50: 3,
            60: 4,
            70: 5,
            80: 6,
            90: 6,
            95: 6,
            100: 6,
        }
        results = {}

        for level, p_lv in target_levels.items():
            stats = {}
            add_props = (
                promote_list[p_lv].get("addProps", {})
                if p_lv < len(promote_list)
                else {}
            )
            for api_key in [
                "FIGHT_PROP_BASE_HP",
                "FIGHT_PROP_BASE_ATTACK",
                "FIGHT_PROP_BASE_DEFENSE",
            ]:
                config = prop_configs.get(api_key)
                if not config:
                    continue
                coeff_data = dictionary.get(str(level), {}).get("curveInfos", {})
                coeff = coeff_data.get(config["curve"], 1.0)
                final_val = config["init"] * coeff + add_props.get(api_key, 0.0)
                label = self.FIGHT_PROP_MAP.get(api_key, api_key)
                stats[label] = round(final_val, 2)

            if special_prop_key:
                val = add_props.get(special_prop_key, 0.0)
                label = self.FIGHT_PROP_MAP.get(special_prop_key, special_prop_key)
                stats[label] = round(val * 100, 2)
            results[level] = stats
        return results

    def _parse_skills(self, talents: Dict[str, Any]) -> Dict[str, Any]:
        results = {}
        valid_keys = sorted(
            [k for k, v in talents.items() if v.get("promote")], key=lambda x: int(x)
        )
        skill_keys = ["normal", "skill", "burst"]

        for i, k in enumerate(valid_keys[:3]):
            talent = talents[k]
            skill_key = skill_keys[i]
            promote = talent.get("promote", {})
            if not promote:
                continue

            first_lv = "1" if "1" in promote else next(iter(promote))
            descriptions = promote[first_lv].get("description", [])

            multipliers = {}
            for desc in descriptions:
                if "|" not in desc:
                    continue
                label, formula = desc.split("|")

                # [核心修复]：支持捕获所有参数
                param_matches = re.findall(r"\{param(\d+):([^\}]+)\}", formula)
                if not param_matches:
                    continue

                # 识别缩放属性
                scaling = "攻击力"
                if any(x in formula for x in ["生命", "HP"]):
                    scaling = "生命值"
                elif "防御" in formula:
                    scaling = "防御力"
                elif "精通" in formula:
                    scaling = "元素精通"

                # 抓取 1-15 级序列
                # 每一级存储为一个数值列表（如果有多参数）或单个数值
                levels_data = []
                for lv_str in sorted(promote.keys(), key=lambda x: int(x)):
                    p_list = promote[lv_str].get("params", [])
                    lv_vals = []
                    for p_match in param_matches:
                        p_idx = int(p_match[0]) - 1
                        fmt = p_match[1]
                        if p_idx < len(p_list):
                            val = p_list[p_idx]
                            # 高精度转换
                            res = val * 100 if "P" in fmt else val
                            lv_vals.append(round(res, 4))  # 提升到 4 位小数

                    # 简化逻辑：如果只有一个参数，不使用列表包裹
                    levels_data.append(lv_vals[0] if len(lv_vals) == 1 else lv_vals)

                multipliers[label] = {"scaling": scaling, "levels": levels_data}
            results[skill_key] = {"name": talent.get("name"), "data": multipliers}
        return results

    def _parse_constellations(
        self, constellations: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        results = []
        for i in range(6):
            c = constellations.get(str(i))
            if c:
                results.append(
                    {
                        "name": c.get("name"),
                        "desc": self._clean_text(c.get("description")),
                    }
                )
        return results

    def _collect_descriptions(self, data: Dict[str, Any]) -> Dict[str, str]:
        descs = {}
        talents = data.get("talent", {})
        for k, v in talents.items():
            descs[f"TALENT_{k}"] = self._clean_text(v.get("description"))
        return descs
