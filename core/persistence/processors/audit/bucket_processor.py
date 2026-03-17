"""[V13.0] 审计桶处理器

负责将离散的审计记录聚合为标准的乘区模型。

[V13.0] 重构为 6 桶模型：
- core_dmg: 核心伤害（BASE + MULT 融合）
- bonus: 增伤乘区
- crit: 暴击乘区
- reaction: 反应乘区
- defense: 防御区
- resistance: 抗性区
"""

from __future__ import annotations
from typing import Any

from .constants import BASE_STATS


# ============================================================
# 桶结构创建
# ============================================================


def create_empty_buckets() -> dict[str, Any]:
    """创建空的乘区桶结构（常规伤害 6 桶模型）

    [V13.0] BASE + MULT 融合为 core_dmg
    [V14.0] 简化防御区和抗性区结构，移除冗余字段
    """
    return {
        "core_dmg": {
            "scaling_info": [],  # list[ScalingAttributeInfo]
            "independent_pct": 0.0,  # 独立乘区%
            "bonus_pct": 0.0,  # 倍率加值%
            "flat": 0.0,  # 固定伤害值加成
            "steps": [],  # 用于域详情展示
        },
        "bonus": {"multiplier": 1.0, "steps": []},
        "crit": {"multiplier": 1.0, "steps": []},
        "reaction": {"multiplier": 1.0, "steps": []},
        "defense": {"multiplier": 1.0, "def_ignore_pct": 0.0, "steps": []},
        "resistance": {
            "multiplier": 1.0,
            "base_resistance": 0.0,
            "final_resistance": 0.0,
            "steps": [],
        },
    }


def create_transformative_buckets() -> dict[str, Any]:
    """创建空的剧变反应桶结构（3 桶模型）

    剧变反应伤害公式：
    伤害 = 等级系数 × 反应系数×(1+精通收益+特殊加成) × 抗性区

    [V14.0] 简化抗性区结构
    [V16.0] 合并 reaction_coeff + em_bonus 为 reaction 桶
    """
    return {
        "level_coeff": {"value": 0.0, "steps": []},
        "reaction": {
            "reaction_type": "",  # 反应类型中文名称（如 "超载"）
            "reaction_base": 1.0,  # 反应系数（如 2.75）
            "em": 0.0,  # 元素精通
            "em_bonus_pct": 0.0,  # 精通加成%
            "special_bonus": 0.0,  # 特殊加成%
            "multiplier": 1.0,  # 总乘数
            "steps": [],
        },
        "resistance": {
            "multiplier": 1.0,
            "base_resistance": 0.0,
            "final_resistance": 0.0,
            "steps": [],
        },
    }


# ============================================================
# 桶分类逻辑
# ============================================================

# 属性到桶的映射（V13.0 新版）
STAT_TO_BUCKET: dict[str, str] = {
    # CORE (原 BASE + MULTIPLIER)
    "攻击力": "core_dmg",
    "生命值": "core_dmg",
    "防御力": "core_dmg",
    "元素精通": "core_dmg",
    "技能倍率%": "core_dmg",
    "独立乘区%": "core_dmg",
    "倍率加值%": "core_dmg",
    "固定伤害值加成": "core_dmg",
    # BONUS (包括元素特定伤害加成)
    "伤害加成": "bonus",
    "火元素伤害加成": "bonus",
    "水元素伤害加成": "bonus",
    "冰元素伤害加成": "bonus",
    "雷元素伤害加成": "bonus",
    "风元素伤害加成": "bonus",
    "岩元素伤害加成": "bonus",
    "草元素伤害加成": "bonus",
    "物理伤害加成": "bonus",
    # CRIT
    "暴击伤害": "crit",
    "暴击率": "crit",
    # REACTION
    "反应基础倍率": "reaction",
    "反应加成系数": "reaction",
    "剧变反应基础": "reaction",
    # DEFENSE
    "无视防御%": "defense",
}


def find_target_bucket(stat: str) -> str | None:
    """查找属性所属的桶

    Args:
        stat: 属性名称

    Returns:
        桶名称或 None
    """
    # 精确匹配
    if stat in STAT_TO_BUCKET:
        return STAT_TO_BUCKET[stat]

    # 后缀匹配：任何以"倍率"或"倍率%"结尾的属性归入 core_dmg
    if stat.endswith("倍率") or stat.endswith("倍率%"):
        return "core_dmg"

    # 百分比属性匹配
    base_stat = stat.replace("%", "")
    if base_stat in STAT_TO_BUCKET:
        return STAT_TO_BUCKET[base_stat]

    # 关键词匹配：处理未在映射表中但包含关键词的属性
    if "伤害加成" in stat:
        return "bonus"
    if "暴击" in stat:
        return "crit"
    if "无视防御" in stat:
        return "defense"
    if "反应" in stat:
        return "reaction"

    return None


def classify_trail_entry(entry: dict[str, Any], buckets: dict[str, Any]) -> None:
    """将单个审计链条目归类到桶中"""
    stat = entry.get("stat", "")
    val = entry.get("value", 0.0)
    op = entry.get("op", "ADD")
    source = entry.get("source", "Unknown")

    target_key = find_target_bucket(stat)
    if not target_key or target_key not in buckets:
        return

    buckets[target_key]["steps"].append(
        {"stat": stat, "value": val, "op": op, "source": source}
    )


def classify_active_modifier(mod: dict[str, Any], buckets: dict[str, Any]) -> None:
    """将活跃修饰符归类到桶中

    注意：基础属性（攻击力、生命值、防御力、元素精通）相关的修饰符
    已经在 inject_frame_snapshot 中处理，此处跳过。
    """
    mod_stat = mod.get("stat", "")
    mod_val = mod.get("value", 0.0)
    mod_source = mod.get("name", "Unknown")

    # 跳过基础属性相关修饰符（已在 inject_frame_snapshot 处理）
    for base_stat in BASE_STATS:
        if (
            mod_stat == base_stat
            or mod_stat == f"{base_stat}%"
            or mod_stat == f"固定{base_stat}"
        ):
            return

    target_bucket = find_target_bucket(mod_stat)
    if target_bucket and target_bucket in buckets:
        buckets[target_bucket]["steps"].append(
            {
                "stat": mod_stat,
                "value": mod_val,
                "op": mod.get("op", "ADD"),
                "source": mod_source,
            }
        )


# ============================================================
# 帧快照注入
# ============================================================


def extract_scaling_stats(buckets: dict[str, Any]) -> set[str]:
    """从 core_dmg 步骤中提取缩放属性名称

    审计链中的格式为 "{属性名}技能倍率%"，如 "生命值技能倍率%"
    """
    scaling_stats: set[str] = set()
    for step in buckets["core_dmg"]["steps"]:
        stat = step.get("stat", "")
        if stat.endswith("技能倍率%"):
            attr_name = stat.replace("技能倍率%", "")
            if attr_name:
                scaling_stats.add(attr_name)
        elif stat == "技能倍率%":
            # 默认攻击力缩放
            scaling_stats.add("攻击力")
    return scaling_stats


def inject_frame_snapshot(
    frame_snapshot: dict[str, Any] | None, buckets: dict[str, Any]
) -> None:
    """从帧快照获取基础属性并构建 ScalingAttributeInfo

    [V13.0] 直接填充 core_dmg 桶，合并 BASE + MULT 数据
    """
    if not frame_snapshot:
        return

    base_stats = frame_snapshot.get("stats", {})
    active_modifiers = frame_snapshot.get("active_modifiers", [])

    # 提取缩放属性
    scaling_stats = extract_scaling_stats(buckets)

    # 构建 skill_mult_map：属性名到技能倍率的映射
    skill_mult_map: dict[str, float] = {}
    for step in buckets["core_dmg"]["steps"]:
        stat_name = step.get("stat", "")
        val = float(step.get("value", 0.0))
        if stat_name.endswith("技能倍率%"):
            attr_name = stat_name.replace("技能倍率%", "")
            if attr_name:
                skill_mult_map[attr_name] = skill_mult_map.get(attr_name, 0.0) + val
        elif stat_name == "技能倍率%":
            # 默认攻击力
            skill_mult_map["攻击力"] = skill_mult_map.get("攻击力", 0.0) + val

    # 为每个缩放属性构建 ScalingAttributeInfo
    scaling_info_list: list[dict[str, Any]] = []

    for stat_name in BASE_STATS:
        # 只处理缩放属性
        if scaling_stats and stat_name not in scaling_stats:
            continue

        # 从 base_stats 获取基础值
        base_val = float(base_stats.get(stat_name, 0.0))

        # 从 active_modifiers 提取百分比和固定值加成
        pct_bonus = 0.0
        flat_bonus = 0.0
        pct_modifiers: list[dict[str, Any]] = []
        flat_modifiers: list[dict[str, Any]] = []

        for mod in active_modifiers:
            mod_stat = mod.get("stat", "")
            mod_val = float(mod.get("value", 0.0))

            if mod_stat == f"{stat_name}%":
                pct_bonus += mod_val
                pct_modifiers.append(mod)
            elif mod_stat == f"固定{stat_name}":
                flat_bonus += mod_val
                flat_modifiers.append(mod)
            elif mod_stat == stat_name:
                # 武器基础攻击力等
                flat_bonus += mod_val
                flat_modifiers.append(mod)

        # 计算最终属性值
        total = base_val * (1 + pct_bonus / 100) + flat_bonus
        if total <= 0:
            continue

        # 获取该属性的技能倍率
        skill_mult = skill_mult_map.get(stat_name, 0.0)
        if (
            skill_mult == 0.0
            and "攻击力" in skill_mult_map
            and stat_name not in skill_mult_map
        ):
            # 如果没有属性特定倍率但有默认倍率，使用默认
            pass

        # 计算贡献值
        contribution = total * skill_mult / 100 if skill_mult > 0 else 0.0

        # 构建 ScalingAttributeInfo
        scaling_info = {
            "attr_name": stat_name,
            "base_val": base_val,
            "pct_bonus": pct_bonus,
            "flat_bonus": flat_bonus,
            "total_val": total,
            "skill_mult": skill_mult,
            "contribution": contribution,
            "pct_modifiers": pct_modifiers,
            "flat_modifiers": flat_modifiers,
        }
        scaling_info_list.append(scaling_info)

        # 注入步骤（用于域详情展示）
        buckets["core_dmg"]["steps"].append(
            {"stat": stat_name, "value": base_val, "op": "SET", "source": "[基础面板]"}
        )

        for mod in pct_modifiers:
            buckets["core_dmg"]["steps"].append(
                {
                    "stat": f"{stat_name}%",
                    "value": mod.get("value", 0.0),
                    "op": "PCT",
                    "source": mod.get("name", "未知来源"),
                }
            )

        for mod in flat_modifiers:
            buckets["core_dmg"]["steps"].append(
                {
                    "stat": f"固定{stat_name}",
                    "value": mod.get("value", 0.0),
                    "op": "ADD",
                    "source": mod.get("name", "未知来源"),
                }
            )

    # 存储 scaling_info
    buckets["core_dmg"]["scaling_info"] = scaling_info_list

    # 活跃修饰符合并到对应乘区
    for mod in active_modifiers:
        classify_active_modifier(mod, buckets)


# ============================================================
# 桶聚合
# ============================================================


def aggregate_buckets(buckets: dict[str, Any], is_crit: bool = False) -> None:
    """聚合桶数据，计算各乘区系数

    [V13.0] 适配新的 6 桶模型
    """
    # [Core] 核心伤害区
    for s in buckets["core_dmg"]["steps"]:
        stat_name = s["stat"]
        if stat_name == "独立乘区%":
            buckets["core_dmg"]["independent_pct"] += s["value"]
        elif stat_name == "倍率加值%":
            buckets["core_dmg"]["bonus_pct"] += s["value"]
        elif stat_name == "固定伤害值加成":
            buckets["core_dmg"]["flat"] += s["value"]

    # [Bonus] 增伤区
    b_sum = 0.0
    for s in buckets["bonus"]["steps"]:
        b_sum += s["value"]
    buckets["bonus"]["multiplier"] = 1.0 + (b_sum / 100.0)

    # [Crit] 暴击区
    for s in buckets["crit"]["steps"]:
        if s["stat"] == "暴击乘数":
            buckets["crit"]["multiplier"] = s["value"]
            break
    else:
        buckets["crit"]["multiplier"] = 1.0 if not is_crit else 1.5

    # [Reaction] 反应区 - [V4.2] 提取反应类型、分离精通加成
    r_base = 1.0
    r_bonus = 0.0
    em_bonus = 0.0
    other_bonus = 0.0
    reaction_type = ""

    for s in buckets["reaction"]["steps"]:
        if s["stat"] == "反应基础倍率":
            r_base = s["value"]
            # 从 source 提取反应类型名称，格式为 "反应:VAPORIZE"
            source = s.get("source", "")
            if ":" in source:
                rt_key = source.split(":")[1]
                # 使用枚举获取中文名称
                from core.systems.contract.reaction import ElementalReactionType
                try:
                    reaction_type = ElementalReactionType[rt_key].value
                except KeyError:
                    reaction_type = rt_key  # 未知类型保持原样
        elif s["stat"] == "反应加成系数":
            r_bonus += s["value"]
            # 分离精通转化加成
            if s.get("source") == "[精通转化]":
                em_bonus += s["value"]
            else:
                other_bonus += s["value"]

    buckets["reaction"]["multiplier"] = r_base * (1.0 + r_bonus) if r_base > 0 else 1.0
    buckets["reaction"]["reaction_type"] = reaction_type
    buckets["reaction"]["reaction_base"] = r_base
    buckets["reaction"]["em_bonus"] = em_bonus
    buckets["reaction"]["other_bonus"] = other_bonus

    # [Defense] 防御区
    d_coeff = 0.0
    for s in buckets["defense"]["steps"]:
        stat_name = s["stat"]
        if stat_name == "防御区系数":
            d_coeff = s["value"]
        elif stat_name == "无视防御%":
            buckets["defense"]["def_ignore_pct"] += s["value"]
    buckets["defense"]["multiplier"] = d_coeff if d_coeff > 0 else 1.0

    # [Resistance] 抗性区
    res_coeff = 0.0
    for s in buckets["resistance"]["steps"]:
        stat_name = s["stat"]
        if stat_name == "抗性区系数":
            res_coeff = s["value"]
    buckets["resistance"]["multiplier"] = res_coeff if res_coeff > 0 else 1.0
    # 注：V15.0 系数计算移至 collect_def_res_raw_data() 中，因为 raw_data 在此时尚未填充


# ============================================================
# 目标修饰符注入
# ============================================================


def inject_target_modifiers(
    target_snapshot: dict[str, Any] | None, buckets: dict[str, Any]
) -> None:
    """从目标快照注入减防/减抗修饰符

    [V14.0] 新增：处理目标侧修饰符（减防、减抗等）
    [V15.0] 适配剧变反应路径（无 defense 桶）

    减防效果：作用于目标实体的 `防御力%` 负值
    减抗效果：作用于目标实体的 `{元素}元素抗性` 负值

    Args:
        target_snapshot: 目标实体快照，包含 `active_modifiers` 列表
        buckets: 乘区桶数据结构
    """
    if not target_snapshot:
        return

    modifiers = target_snapshot.get("active_modifiers", [])
    if not modifiers:
        return

    # 检查是否为剧变反应路径（无 defense 桶）
    has_defense = "defense" in buckets

    for mod in modifiers:
        stat = mod.get("stat", "")
        val = mod.get("value", 0.0)
        source = mod.get("name", mod.get("source", "目标修饰符"))

        # 减防修饰符：防御力% 的负值（仅常规伤害路径）
        if has_defense and stat == "防御力%" and val < 0:
            buckets["defense"]["steps"].append(
                {"stat": "减防%", "value": abs(val), "op": "SET", "source": source}
            )

        # 固定防御力减益（仅常规伤害路径）
        elif has_defense and stat == "固定防御力" and val < 0:
            buckets["defense"]["steps"].append(
                {
                    "stat": "固定防御力减益",
                    "value": abs(val),
                    "op": "ADD",
                    "source": source,
                }
            )

        # 减抗修饰符：{元素}元素抗性
        elif "抗性" in stat:
            buckets["resistance"]["steps"].append(
                {"stat": stat, "value": val, "op": "ADD", "source": source}
            )


# ============================================================
# [V14.1] 防御区/抗性区原始数据收集
# ============================================================


def collect_def_res_raw_data(
    frame_snapshot: dict[str, Any] | None,
    target_snapshot: dict[str, Any] | None,
    buckets: dict[str, Any],
    element_type: str = "",
) -> None:
    """收集防御区和抗性区计算所需的原始参数

    [V14.1] 为 UI 端计算提供原始数据
    [V15.0] 适配剧变反应路径（无 defense 桶）

    背景问题：
    - damage_system.py 中计算防御区/抗性区系数时设置 audit=False，不入库
    - aggregate_buckets 从审计链提取系数失败，默认为 1.0
    - 本函数收集原始参数，供 UI 端工具类重新计算

    Args:
        frame_snapshot: 攻击者帧快照（含等级、基础属性）
        target_snapshot: 目标实体快照（含防御力、修饰符）
        buckets: 乘区桶数据结构
        element_type: 元素类型（如 "火", "水", "PHYSICAL" 等）
    """
    # 检查是否为剧变反应路径（无 defense 桶）
    has_defense = "defense" in buckets

    # ========== 防御区原始数据（仅常规伤害路径）==========
    if has_defense:
        # 从帧快照获取攻击者等级
        attacker_level = 90  # 默认值
        if frame_snapshot:
            stats = frame_snapshot.get("stats", {})
            attacker_level = stats.get("等级", 90)

        # 从目标快照获取目标防御力
        target_defense = 500  # 默认值（史莱姆约 500）
        def_reduction_pct = 0.0  # 减防百分比

        if target_snapshot:
            target_stats = target_snapshot.get("stats", {})
            target_defense = target_stats.get("防御力", 500)

            # 从目标修饰符提取减防百分比
            for mod in target_snapshot.get("active_modifiers", []):
                mod_stat = mod.get("stat", "")
                mod_val = mod.get("value", 0.0)
                if mod_stat == "防御力%" and mod_val < 0:
                    def_reduction_pct += abs(mod_val)

        # 从审计链获取无视防御百分比
        def_ignore_pct = buckets["defense"].get("def_ignore_pct", 0.0)

        buckets["defense"]["raw_data"] = {
            "attacker_level": attacker_level,
            "target_defense": target_defense,
            "def_reduction_pct": def_reduction_pct,
            "def_ignore_pct": def_ignore_pct,
        }

    # ========== 抗性区原始数据 ==========
    # 元素名称映射（用于匹配抗性属性）
    element_name_map = {
        "PHYSICAL": "物理",
        "PYRO": "火",
        "HYDRO": "水",
        "ELECTRO": "雷",
        "CRYO": "冰",
        "ANEMO": "风",
        "GEO": "岩",
        "DENDRO": "草",
    }
    el_name = element_name_map.get(element_type, element_type)

    # [V16.0] 从目标快照获取基础抗性
    base_resistance = 0.0
    if target_snapshot:
        target_resistance = target_snapshot.get("resistance", {})
        base_resistance = target_resistance.get(el_name, 0.0)
        # 同时设置到 buckets 中（供域点击展示）
        buckets["resistance"]["base_resistance"] = base_resistance

    # 计算最终抗性值
    final_resistance = base_resistance

    if target_snapshot:
        # 从目标修饰符累加对应元素的抗性变化
        for mod in target_snapshot.get("active_modifiers", []):
            mod_stat = mod.get("stat", "")
            mod_val = mod.get("value", 0.0)

            # [V16.0] 精确匹配元素抗性属性
            # 匹配格式: "火元素抗性"、"物理元素抗性" 等
            target_res_key = f"{el_name}元素抗性"
            if mod_stat == target_res_key:
                final_resistance += mod_val

    buckets["resistance"]["raw_data"] = {
        "element_type": element_type,
        "element_name": el_name,
        "base_resistance": base_resistance,
        "final_resistance": final_resistance,
    }

    # [V15.0] 计算并填充防御区和抗性区系数
    from .coefficient_calculator import (
        calculate_defense_coefficient,
        calculate_resistance_coefficient,
    )

    # 防御区：使用 raw_data 计算系数（仅常规伤害路径）
    if has_defense:
        def_raw = buckets["defense"].get("raw_data", {})
        if def_raw:
            buckets["defense"]["multiplier"] = calculate_defense_coefficient(def_raw)

    # 抗性区：使用 raw_data 计算系数
    res_raw = buckets["resistance"].get("raw_data", {})
    if res_raw:
        buckets["resistance"]["multiplier"] = calculate_resistance_coefficient(res_raw)


def collect_resistance_raw_data(
    frame_snapshot: dict[str, Any] | None,
    target_snapshot: dict[str, Any] | None,
    buckets: dict[str, Any],
    element_type: str = "",
) -> None:
    """收集抗性区计算所需的原始参数（剧变反应专用）

    [V15.0] 从 collect_def_res_raw_data 拆分，仅处理抗性区

    Args:
        frame_snapshot: 攻击者帧快照（含等级、基础属性）
        target_snapshot: 目标实体快照（含防御力、修饰符）
        buckets: 乘区桶数据结构
        element_type: 元素类型（如 "火", "水", "PHYSICAL" 等）
    """
    # 元素名称映射（用于匹配抗性属性）
    element_name_map = {
        "PHYSICAL": "物理",
        "PYRO": "火",
        "HYDRO": "水",
        "ELECTRO": "雷",
        "CRYO": "冰",
        "ANEMO": "风",
        "GEO": "岩",
        "DENDRO": "草",
    }
    el_name = element_name_map.get(element_type, element_type)

    # 计算最终抗性值
    # [V16.0] 修复：初始化为基础抗性，然后累加修饰符变化
    base_resistance = buckets["resistance"].get("base_resistance", 0.0)
    final_resistance = base_resistance

    if target_snapshot:
        # 从目标修饰符累加对应元素的抗性变化
        for mod in target_snapshot.get("active_modifiers", []):
            mod_stat = mod.get("stat", "")
            mod_val = mod.get("value", 0.0)

            # [V16.0] 精确匹配元素抗性属性
            # 匹配格式: "火元素抗性"、"物理元素抗性" 等
            target_res_key = f"{el_name}元素抗性"
            if mod_stat == target_res_key:
                final_resistance += mod_val

    buckets["resistance"]["raw_data"] = {
        "element_type": element_type,
        "element_name": el_name,
        "base_resistance": base_resistance,
        "final_resistance": final_resistance,
    }

    # 计算并填充抗性区系数
    from .coefficient_calculator import calculate_resistance_coefficient

    res_raw = buckets["resistance"].get("raw_data", {})
    if res_raw:
        buckets["resistance"]["multiplier"] = calculate_resistance_coefficient(res_raw)
