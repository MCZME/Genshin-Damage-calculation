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
    """
    return {
        "core_dmg": {
            "scaling_info": [],      # list[ScalingAttributeInfo]
            "independent_pct": 0.0,  # 独立乘区%
            "bonus_pct": 0.0,        # 倍率加值%
            "flat": 0.0,             # 固定伤害值加成
            "steps": [],             # 用于域详情展示
        },
        "bonus": {"multiplier": 1.0, "steps": []},
        "crit": {"multiplier": 1.0, "steps": []},
        "reaction": {"multiplier": 1.0, "steps": []},
        "defense": {"multiplier": 1.0, "def_reduction_pct": 0.0, "def_ignore_pct": 0.0, "steps": []},
        "resistance": {"multiplier": 1.0, "res_reduction_pct": 0.0, "res_penetration_pct": 0.0, "steps": []}
    }


def create_transformative_buckets() -> dict[str, Any]:
    """创建空的剧变反应桶结构（4 桶模型）

    剧变反应伤害公式：
    伤害 = 等级系数 × 反应系数 × (1 + 精通收益 + 特殊加成) × 抗性区
    """
    return {
        "level_coeff": {"value": 0.0, "steps": []},
        "reaction_coeff": {"value": 1.0, "steps": []},
        "em_bonus": {
            "value": 1.0,
            "em": 0.0,
            "em_bonus_pct": 0.0,
            "special_bonus": 0.0,
            "steps": []
        },
        "resistance": {"multiplier": 1.0, "res_reduction_pct": 0.0, "res_penetration_pct": 0.0, "steps": []}
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
    "减防%": "defense",
    "无视防御%": "defense",
    # RESISTANCE
    "减抗%": "resistance",
    "抗性穿透%": "resistance",
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
    if "减抗" in stat or "抗性穿透" in stat:
        return "resistance"
    if "减防" in stat or "无视防御" in stat:
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

    buckets[target_key]["steps"].append({
        "stat": stat,
        "value": val,
        "op": op,
        "source": source
    })


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
        if mod_stat == base_stat or mod_stat == f"{base_stat}%" or mod_stat == f"固定{base_stat}":
            return

    target_bucket = find_target_bucket(mod_stat)
    if target_bucket and target_bucket in buckets:
        buckets[target_bucket]["steps"].append({
            "stat": mod_stat,
            "value": mod_val,
            "op": mod.get("op", "ADD"),
            "source": mod_source
        })


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
    frame_snapshot: dict[str, Any] | None,
    buckets: dict[str, Any]
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
        if skill_mult == 0.0 and "攻击力" in skill_mult_map and stat_name not in skill_mult_map:
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
        buckets["core_dmg"]["steps"].append({
            "stat": stat_name,
            "value": base_val,
            "op": "SET",
            "source": "[基础面板]"
        })

        for mod in pct_modifiers:
            buckets["core_dmg"]["steps"].append({
                "stat": f"{stat_name}%",
                "value": mod.get("value", 0.0),
                "op": "PCT",
                "source": mod.get("name", "未知来源")
            })

        for mod in flat_modifiers:
            buckets["core_dmg"]["steps"].append({
                "stat": f"固定{stat_name}",
                "value": mod.get("value", 0.0),
                "op": "ADD",
                "source": mod.get("name", "未知来源")
            })

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

    # [Reaction] 反应区
    r_base = 1.0
    r_bonus = 0.0
    for s in buckets["reaction"]["steps"]:
        if s["stat"] == "反应基础倍率":
            r_base = s["value"]
        elif s["stat"] == "反应加成系数":
            r_bonus += s["value"]
    buckets["reaction"]["multiplier"] = r_base * (1.0 + r_bonus) if r_base > 0 else 1.0

    # [Defense] 防御区
    d_coeff = 0.0
    for s in buckets["defense"]["steps"]:
        stat_name = s["stat"]
        if stat_name == "防御区系数":
            d_coeff = s["value"]
        elif stat_name == "减防%":
            buckets["defense"]["def_reduction_pct"] += s["value"]
        elif stat_name == "无视防御%":
            buckets["defense"]["def_ignore_pct"] += s["value"]
    buckets["defense"]["multiplier"] = d_coeff if d_coeff > 0 else 1.0

    # [Resistance] 抗性区
    res_coeff = 0.0
    for s in buckets["resistance"]["steps"]:
        stat_name = s["stat"]
        if stat_name == "抗性区系数":
            res_coeff = s["value"]
        elif stat_name == "减抗%":
            buckets["resistance"]["res_reduction_pct"] += s["value"]
        elif stat_name == "抗性穿透%":
            buckets["resistance"]["res_penetration_pct"] += s["value"]
    buckets["resistance"]["multiplier"] = res_coeff if res_coeff > 0 else 1.0
